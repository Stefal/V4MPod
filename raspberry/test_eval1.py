class Maclasse(object):
    def __init__(self):
        self.mondict = {'action':'mi(self)'}

    def do(self):
        print(self.mondict['action'])
        eval(self.mondict['action'])

    def mi(self):
        print('dans mi')
