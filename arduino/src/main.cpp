/*
Première version du programme de controle des Yi
*/
#include <Arduino.h>
#include <Wire.h>


//const int shutter_pin = 2;
//const int power_pin = 4;
const int powerup_button_pin = 5;
const int powerdown_button_pin = 6;
const int tmlapse_start_pin = 7;
const int tmlapse_stop_pin = 8;
//const int shutter_led_pin = A0;
const int shutter_led_pin = 3;
const int shutter_button_pin = 9;

int pic_count = 0; // picture counter
int after_pic_delay = 800;
volatile int shutter_led_counter = 0;
long old_timestamp = 0;
long current_timestamp = 0;
const byte cam_range = 0b00000001;

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

void myISR() {
  shutter_led_counter++;
}

void setup() {
  // put your setup code here, to run once:

  // Set expander n°1 I/O as output
  expanderWrite(mcp1, IODIRA, 0x00);
  expanderWrite(mcp1, IODIRB, 0x00);

  // Set expander n°2 I/O as output. We will set inputs later
  expanderWrite(mcp2, IODIRA, 0x00);
  expanderWrite(mcp2, IODIRB, 0x00);

  // expander configuration register
  expanderWrite(mcp2, IOCON, 0b00100010); // no mirror interrupts, disable sequential mode, active HIGH

  // enable pull-up on switches
  //expanderWrite (GPPUA, 0xFF);   // pull-up resistor for switch - both ports

  // invert polarity
  //expanderWrite(mcp2, IOPOLA, 0xFF);  // invert polarity of signal - both ports

  // enable all interrupts
  expanderWrite (mcp2, GPINTENA, 0xFF); // enable interrupts - both ports

  // MES TESTS
  //expanderWriteBoth (IOPOLA, 0x00);  // polarity of signal - both ports

  //expanderWriteBoth(DEFVALA, 0b00000000); // defini la valeur par défaut à 0
  expanderWrite(mcp2, INTCONA, 0b00000000);// Active le mode "on change"
  // FIN MES TESTS
  // no interrupt yet
  sht_led_activity = false;

  // read from interrupt capture ports to clear them
  expanderRead (mcp2, INTCAPA);
  expanderRead (mcp2, INTCAPB);

  // pin 19 of MCP23017 is plugged into D2 of the Arduino which is interrupt 0
  attachInterrupt(0, mcp2_interrupt, RISING);


  // pinMode(shutter_pin, OUTPUT);
  // pinMode(power_pin, OUTPUT);
  pinMode(powerup_button_pin, INPUT_PULLUP);
  pinMode(powerdown_button_pin, INPUT_PULLUP);
  pinMode(tmlapse_start_pin, INPUT_PULLUP);
  pinMode(tmlapse_stop_pin, INPUT_PULLUP);
  pinMode(shutter_button_pin, INPUT_PULLUP);
  pinMode(shutter_led_pin, INPUT);
  pinMode(A5, INPUT);
  attachInterrupt(digitalPinToInterrupt(shutter_led_pin), myISR, RISING);
  Serial.begin(9600);
  Serial.println("Starting program");

}

void power_up_Yi(const byte cam_range) {
  Serial.println("Starting the Yi");
  //Set expander n°1 GPIOA to HIGH
  expanderWrite(mcp1, GPIOA, cam_range);

  delay(500);
  //Set expander n°1 GPIOA to LOW
  expanderWrite(mcp1, GPIOA, 0b00000000);

  Serial.println("Pause during the boot");
  delay(10000); //attente mise en route
  Serial.println("The cams should be ready");
}

void power_down_Yi(const byte cam_range) {
  Serial.println("Shutting down the Yi");
  //Set expander n°1 GPIOA to HIGH
  expanderWrite(mcp1, GPIOA, cam_range);

  delay(2500);
  //Set expander n°1 GPIOA to LOW
  expanderWrite(mcp1, GPIOA, 0b00000000);
}

//Take a picture
long take_picture(const byte cam_range) {
  Serial.println("Taking picture...");
  long pic_start_time = millis();
  int shutter_return = LOW;
  shutter_led_counter = 0;
  int sht_LedToggle_array[8] = {0,0,0,0,0,0,0,0}; //Reset the array
  //Set expander n°1 GPIOB to HIGH
  expanderWrite(mcp1, GPIOB, cam_range);
  delay(100);
  //Set expander n°1 GPIOB to LOW
  expanderWrite(mcp1, GPIOB, 0b00000000);

  while (shutter_led_counter == 0) { // Wait for the shutter led return

    if (millis()-pic_start_time > 2500) {
      Serial.println("No response");
      return 0;
    }
  }

  Serial.println("Shutter led detected");
  Serial.println("Pause");
  delay(after_pic_delay);
  if (shutter_led_counter > 1) {
    Serial.print("ERROR ! counter = ");
    Serial.println(shutter_led_counter);
    return -1;
  }
  Serial.println("End of pause");
  return pic_start_time;
}

void handle_Sht_led_activity ()
{
  unsigned int sht_LedValue = 0;
  unsigned int sht_LedLastValue = 0;

  sht_led_activity = false;  // ready for next time through the interrupt service routine
  digitalWrite (ISR_INDICATOR, LOW);  // debugging

  // Read port values, as required. Note that this re-arms the interrupts.

  if (expanderRead (mcp2, INFTFB))
    {

    sht_LedValue |= expanderRead (mcp2, INTCAPB);        // port B is in low-order byte
    }

  /*Serial.print("sht_LedValue : ");
  Serial.println(sht_LedValue, BIN);
  Serial.print("last State : ");
  Serial.println(sht_LedLastValue, BIN);
  Serial.print("Ou exclusif : ");
  Serial.println(sht_LedLastValue ^ sht_LedValue, BIN);
  Serial.println("");*/
  Serial.println ("Led toggles");
  //Serial.println ("0                   1");
  Serial.println ("00 01 02 03 04 05 06 07");

  // display which buttons were down at the time of the interrupt
  for (byte sht_Led = 0; sht_Led < 8; sht_Led++)
    {
    // this key down?
    /*Serial.print("sht_Led : ");
    Serial.println(1<< sht_Led, BIN);
    Serial.print("résultat de : ");
    Serial.print(sht_LedLastValue, BIN);
    Serial.print(" ^ ");
    Serial.print(sht_LedValue, BIN);
    Serial.print(" & ");
    Serial.print("1 << ");
    Serial.print(sht_Led, BIN);
    Serial.print(" : ");
    Serial.println(((sht_LedLastValue ^ sht_LedValue) & (1 << sht_Led)));
    Serial.print("calcul d origine : ");
    Serial.println(sht_LedValue & (1 << sht_Led), BIN);*/
    if ((sht_LedLastValue ^ sht_LedValue) & (1 << sht_Led)){
      //Serial.print ("01 ");
      sht_LedToggle_array[sht_Led]+=1;
      Serial.print(sht_LedToggle_array[sht_Led]);
      Serial.print(" ");
      }
    else {
      //Serial.print ("00 ");
      Serial.print(sht_LedToggle_array[sht_Led]);
      Serial.print(" ");
      }

    }
  sht_LedLastValue = sht_LedValue;
  Serial.println ();

  // if a switch is now pressed, turn LED on  (key down event)
  if (sht_LedValue)
    {
    time = millis ();  // remember when
    digitalWrite (ONBOARD_LED, HIGH);  // on-board LED
    }  // end if

}  // end of handle_Sht_led_activity

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

  if (digitalRead(powerup_button_pin) == LOW) {
    power_up_Yi(cam_range);
  }

  if (digitalRead(powerdown_button_pin) == LOW) {
    power_down_Yi(cam_range);
  }

  if (digitalRead(shutter_button_pin) == LOW) {
    Serial.println(take_picture(cam_range));
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