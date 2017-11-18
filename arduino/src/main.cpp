/*
Première version du programme de controle des Yi
*/
//TODO La caméra rev B ne fonctionne pas sur la sortie 3
//TODO A vérifier
#include <Arduino.h>
#include <Wire.h>
//#include <Adafruit_MAX31855.h>
#include <CmdMessenger.h>
#include <SPI.h>



const int powerup_button_pin = 5;
const int powerdown_button_pin = 6;
const int tmlapse_start_pin = 7;
const int tmlapse_stop_pin = 8;
const int shutter_led_pin = 3;
const int shutter_button_pin = 9;

int pic_count = 0; // picture counter
int after_pic_delay = 600;
volatile int shutter_led_counter = 0;
long old_timestamp = 0;
long current_timestamp = 0;
byte cam_range = 0b00001111;

// MCP23017 registers (everything except direction defaults to 0)

#define IODIRA   0x00   // IO direction  (0 = output, 1 = input (Default))
#define IODIRB   0x01
#define IOPOLA   0x02   // IO polarity   (0 = normal, 1 = inverse)
#define IOPOLB   0x03
#define GPINTENA 0x04   // Interrupt on change (0 = disable, 1 = enable)
#define GPINTENB 0x05
#define DEFVALA  0x06   // Default comparison for interrupt on change (interrupts on opposite)
#define DEFVALB  0x07
#define INTCONA  0x08   // Interrupt control (0 = interrupt on change from previous, 1 = interrupt on change from DEFVAL)
#define INTCONB  0x09
#define IOCON    0x0A   // IO Configuration: bank/mirror/seqop/disslw/haen/odr/intpol/notimp
//#define IOCON 0x0B  // same as 0x0A
#define GPPUA    0x0C   // Pull-up resistor (0 = disabled, 1 = enabled)
#define GPPUB    0x0D
#define INFTFA   0x0E   // Interrupt flag (read only) : (0 = no interrupt, 1 = pin caused interrupt)
#define INFTFB   0x0F
#define INTCAPA  0x10   // Interrupt capture (read only) : value of GPIO at time of last interrupt
#define INTCAPB  0x11
#define GPIOA    0x12   // Port value. Write to change, read to obtain value
#define GPIOB    0x13
#define OLLATA   0x14   // Output latch. Write to latch output.
#define OLLATB   0x15

#define mcp1 0x20  // MCP23017 n°1 (shutter and power) is on I2C port 0x20
#define mcp2 0x21  // MCP23017 n°2 (shutter led input) is on I2C port 0x21

#define ISR_INDICATOR 12  // pin 12
#define ONBOARD_LED 13    // pin 13
volatile bool sht_led_activity;
int sht_LedToggle_array[8];
unsigned long time = 0;

// Function prototypes
void attachCommandCallbacks(void);
void OnCommandList(void);
byte power_up_Yi(const byte cam_range);
void power_down_Yi(const byte cam_range);
byte take_picture(const byte cam_range);
void wait_time(const byte cam_range);
void ShowCommands(void);
void OnTake_picture(void);
void OnPower_up_Yi(void);
void OnPower_down_Yi(void);
void OnWake_up(void);
void handle_Sht_led_activity(void);

// End of Function prototypes

void expanderWrite (const byte port, const byte reg, const byte data ){
  Wire.beginTransmission (port);
  Wire.write (reg);
  Wire.write (data);
  Wire.endTransmission ();
} // end of expanderWrite

// read a byte from the expander
unsigned int expanderRead (const byte port, const byte reg){
  Wire.beginTransmission (port);
  Wire.write (reg);
  Wire.endTransmission ();
  Wire.requestFrom (port, 1);
  return Wire.read();
} // end of expanderRead

// interrupt service routine, called when pin D2 goes from 0 to 1
void mcp2_interrupt ()
{
  digitalWrite (ISR_INDICATOR, HIGH);  // debugging
  sht_led_activity = true;   // set flag so main loop knows
}  // end of mcp2_interrupt


CmdMessenger cmdMessenger = CmdMessenger(Serial);
enum
{
    KCommandList      , // Command to request list of available commands
    KTakepic          , // Command to request cams to take a pic_count
    KPower_up         , // Command to request cams to power up
    KPower_down       , // Command to request cams to power down
  };

void attachCommandCallbacks()
{
  // Attach callback methods

  cmdMessenger.attach(KCommandList, OnCommandList);
  cmdMessenger.attach(KTakepic, OnTake_picture);
  cmdMessenger.attach(KPower_up, OnPower_up_Yi);
  cmdMessenger.attach(KPower_down, OnPower_down_Yi);

}

void OnCommandList()
{
  ShowCommands();
}

void ShowCommands()
{
  Serial.println("Available commands");
  Serial.println("TODO");
}

void OnTake_picture()
{
  //byte cams_return = 0b00000000;
  byte cams = cmdMessenger.readBinArg<byte>();
  unsigned int pic_nbr = cmdMessenger.readBinArg<unsigned int>();
  long start_time = millis();
  byte cams_return=take_picture(cams);
  long shutter_time = millis() - start_time;
  /* Send result back */
  cmdMessenger.sendCmdStart(KTakepic);
  cmdMessenger.sendCmdBinArg(cams_return);
  cmdMessenger.sendCmdBinArg(shutter_time);
  cmdMessenger.sendCmdBinArg(pic_nbr);
  cmdMessenger.sendCmdEnd();
  //wait_time(cams);

}

void OnPower_up_Yi()
{
  int value1 = cmdMessenger.readBinArg<int>();
  byte shutter_led_return = power_up_Yi(value1);
  //send result back
  cmdMessenger.sendCmdStart(KPower_up);
  cmdMessenger.sendCmdBinArg(shutter_led_return);
  cmdMessenger.sendCmdEnd();
}

void OnPower_down_Yi()
{
  int value1 = cmdMessenger.readBinArg<int>();
  power_down_Yi(value1);
  //TODO send result back

}

void Clear_mcp2_Interrupt()
{
  // read from interrupt capture ports to clear them
  expanderRead (mcp2, INTCAPA);
  expanderRead (mcp2, INTCAPB);
  digitalWrite (ISR_INDICATOR, LOW); // debugging

}

void setup() {
  pinMode (ISR_INDICATOR, OUTPUT);  // for testing (ISR indicator)
  pinMode (ONBOARD_LED, OUTPUT);  // for onboard LED
  Serial.begin(115200);
  //Serial.println("Starting program");

  // Adds newline to every command
  cmdMessenger.printLfCr();

  // Attach my application's user-defined callback methods
  attachCommandCallbacks();


  Wire.begin ();
  // Set expander n°1 I/O as output
  expanderWrite(mcp1, IODIRA, 0x00);
  expanderWrite(mcp1, IODIRB, 0x00);
  // Set expander n°2 I/O as output. We will set inputs later
  expanderWrite(mcp2, IODIRA, 0x00);
  expanderWrite(mcp2, IODIRB, 0x00);

  // TODO set dynamically the pins as output
  // enable GPIOA pins as input
  expanderWrite(mcp2, IODIRA, 0xFF);
  // enable pull-up on switches
  expanderWrite(mcp2, GPPUA, 0xFF);
  // expander configuration register
  expanderWrite(mcp2, IOCON, 0b01100010); // no mirror interrupts, disable sequential mode, active HIGH

  // invert polarity
  //expanderWrite(mcp2, IOPOLA, 0xFF);  // invert polarity of signal - both ports

  // enable interrupts
  expanderWrite (mcp2, GPINTENA, cam_range); // enable interrupts

  //expanderWriteBoth(DEFVALA, 0b00000000); // defini la valeur par défaut à 0
  expanderWrite(mcp2, INTCONA, 0b00000000);// Active le mode "on change"
  // FIN MES TESTS
  // no interrupt yet
  sht_led_activity = false;
  // pin 19 of MCP23017 is plugged into D2 of the Arduino which is interrupt 0
  attachInterrupt(0, mcp2_interrupt, RISING);

  // pinMode(shutter_pin, OUTPUT);
  // pinMode(power_pin, OUTPUT);
  pinMode(powerup_button_pin, INPUT_PULLUP);
  pinMode(powerdown_button_pin, INPUT_PULLUP);
  pinMode(tmlapse_start_pin, INPUT_PULLUP);
  pinMode(tmlapse_stop_pin, INPUT_PULLUP);
  pinMode(shutter_button_pin, INPUT_PULLUP);
  pinMode(shutter_led_pin, OUTPUT);
  //pinMode(A5, INPUT);
  //attachInterrupt(digitalPinToInterrupt(shutter_led_pin), myISR, RISING);

  // Clear Mcp2 interrupt
  Clear_mcp2_Interrupt();


}

byte power_up_Yi(const byte cam_range) {
  //Serial.println("Starting the Yi");
  //Set expander n°1 GPIOA to HIGH
  expanderWrite(mcp1, GPIOA, cam_range);
  delay(600); // Keep the power button pressed
  //Set expander n°1 GPIOA to LOW
  expanderWrite(mcp1, GPIOA, 0b00000000);
  //Serial.println("Pause during the boot");
  delay(4000); //attente mise en route
  // Clear mcp2 Interrupt
  Clear_mcp2_Interrupt();
  return 1;
}

void power_down_Yi(const byte cam_range) {
  //Serial.println("Shutting down the Yi");
  //Set expander n°1 GPIOA to HIGH
  expanderWrite(mcp1, GPIOA, cam_range);

  delay(2500);
  //Set expander n°1 GPIOA to LOW
  expanderWrite(mcp1, GPIOA, 0b00000000);
}

void handle_Sht_led_activity ()
{
  unsigned int sht_LedValue = 0;
  unsigned int sht_LedLastValue = 0;
  sht_led_activity = false;  // ready for next time through the interrupt service routine
  digitalWrite (ISR_INDICATOR, LOW);  // debugging

  // Read port values, as required. Note that this re-arms the interrupts.

  if (expanderRead (mcp2, INFTFA))
    {

    sht_LedValue |= expanderRead (mcp2, INTCAPA);        // port B is in low-order byte
    //Serial.print("sht_LedValue : ");
    //Serial.println(sht_LedValue, BIN);
    }

    /*Serial.print("sht_LedValue : ");
    Serial.println(sht_LedValue, BIN);
    Serial.print("last State : ");
    Serial.println(sht_LedLastValue, BIN);
    Serial.print("Ou exclusif : ");
    Serial.println(sht_LedLastValue ^ sht_LedValue, BIN);
    Serial.println("");
  Serial.println ("Shutter Led toggles");
  //Serial.println ("0                   1");
  Serial.println ("0 1 2 3 4 5 6 7");*/

  // display which buttons were down at the time of the interrupt
  for (byte sht_Led = 0; sht_Led < 8; sht_Led++)
    {
    if ((sht_LedLastValue ^ sht_LedValue) & (1 << sht_Led)){
      //Serial.print ("01 ");
      sht_LedToggle_array[sht_Led]+=1;
      /*Serial.print(sht_LedToggle_array[sht_Led]);
      Serial.print(" ");*/
      }
    else {
      //Serial.print ("00 ");
      /*Serial.print(sht_LedToggle_array[sht_Led]);
      Serial.print(" ");*/
      }

    }
  sht_LedLastValue = sht_LedValue; /*TODO Vérifier que ça fonctionne car sht_LedLastValue
  est reseté au redémarrage de la fonction*/

  // if a switch is now pressed, turn LED on  (key down event)
  if (sht_LedValue)
    {
    time = millis ();  // remember when
    digitalWrite (ONBOARD_LED, HIGH);  // on-board LED
    }  // end if

}  // end of handle_Sht_led_activity

//Take a picture
byte take_picture(const byte cam_range) {
  digitalWrite(shutter_led_pin, HIGH);
  //Serial.println("Taking picture...");
  byte shutter_led_check = 0b00000000;
  memset(sht_LedToggle_array,0,sizeof(sht_LedToggle_array
  )); //Reset the array

  long pic_start_time = millis();
  //Set expander n°1 GPIOB to HIGH to "press" the shutter button
  expanderWrite(mcp1, GPIOB, cam_range);
  delay(100);
  //Set expander n°1 GPIOB to LOW to "release" the shutter button
  expanderWrite(mcp1, GPIOB, 0b00000000);

  // Wait for the shutter led return for each enabled camera
  while ((shutter_led_check != cam_range) && ((millis() - pic_start_time) < 3000)) {

    if (sht_led_activity) {
      handle_Sht_led_activity();
      /*Serial.print("sht_LedToggle_array : ");
      for(int i = 7; i >= 0; i--)
      {
        Serial.print(sht_LedToggle_array[i]);
      }
      Serial.println(" ");*/
      for (byte sht_Led = 0; sht_Led < 8; sht_Led++)
      {
        if ((sht_LedToggle_array[sht_Led] == 1) && (cam_range & (1 << sht_Led)))
          {
          shutter_led_check = shutter_led_check | (1 << sht_Led);
          /*Serial.print("1 << sht_Led : ");
          Serial.println(1 << sht_Led, BIN);
          Serial.print("shutter_led_check : ");
          Serial.println(shutter_led_check, BIN);
          Serial.print("cam_range : ");
          Serial.println(cam_range, BIN);*/

          }
        }
      }
    }




  //Serial.println("existing take_pic function");
  digitalWrite(shutter_led_pin, LOW);
  return shutter_led_check;
}

void wait_time(const byte cam_range)
{
  // Wait for the cams to be ready, and check interrupt in case of a failure
  //Serial.println("we are in wait_time");
  unsigned long delay_Start_Time = millis();
  while (millis() < (delay_Start_Time + after_pic_delay)) {
    if (sht_led_activity) {
      handle_Sht_led_activity();
      for (byte sht_Led = 0; sht_Led < 8; sht_Led++)
      {
        if ((sht_LedToggle_array[sht_Led] > 1) & (cam_range & (1 << sht_Led)))
        {
          //Serial.print("Error on cam n°");
          //Serial.println(sht_Led);
          //return -1;
        }
      }
    }
  }

}

void timelapse(const byte cam_range) {
  Serial.println("Starting timelapse");
  int pic_shutter_request = 0;
  int pic_shutter_taken = 0;
  while (true) {
    current_timestamp = take_picture(cam_range);
    pic_shutter_request++;
    Serial.print("Interval : ");
    Serial.print(current_timestamp - old_timestamp);
    Serial.println("ms");
    if (current_timestamp != 0) {
      old_timestamp = current_timestamp;
      pic_shutter_taken++;
      Serial.print("Successful pictures : ");
      Serial.print(pic_shutter_taken);
      Serial.print(" of ");
      Serial.println(pic_shutter_request);
      Serial.print("Missing pictures : ");
      Serial.println(pic_shutter_request - pic_shutter_taken);
    }

    if (digitalRead(tmlapse_stop_pin) == LOW) {
      Serial.println("Timelapse stopped");
      break;
    }
  }
}


void loop() {

  // Process incoming serial data, and perform callbacks
  cmdMessenger.feedinSerialData();

  if (digitalRead(powerup_button_pin) == LOW) {
    power_up_Yi(cam_range);
  }

  if (digitalRead(powerdown_button_pin) == LOW) {
    power_down_Yi(cam_range);
  }

  if (digitalRead(shutter_button_pin) == LOW) {
    Serial.println(take_picture(cam_range));
    //wait_time(cam_range);
  }

  if (digitalRead(tmlapse_start_pin) == LOW) {
    timelapse(cam_range);
  }

  // turn LED off after 500 ms
  if (millis () > (time + 200) && time != 0)
   {
    digitalWrite (ONBOARD_LED, LOW);
    time = 0;
   }  // end if time up

}
