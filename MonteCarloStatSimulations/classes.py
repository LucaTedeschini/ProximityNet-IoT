import random


class device():
    '''This class define the behaviour of an esp32 as a Finite State Machine
    '''


    def __init__(self, name:str="", beaconByte:int=12, \
                minBeacon:int=1, maxBeacon:int=1, \
                minListen:int=1, maxListen:int=10, \
                minSleep:int=1, maxSleep:int=10):
        self.name = name

        # energy parameters
        Vcc = 3.3
        self.beaconPower = Vcc * 130e-3
        self.listenPower = Vcc * 100e-3
        self.sleepPower = Vcc * 0.8e-3
        self.ble_connectionPower = Vcc * 130e-3
        self.energyConsumption = 0
        self.energyPeriods = []
        
        # frame parameters
        self.bitsBeacon = beaconByte * 8
        self.freq = 240e+6  # 240MHz
        self.unitTime = (self.bitsBeacon / self.freq)

        self.minBeacon, self.maxBeacon = minBeacon, maxBeacon
        self.minListen, self.maxListen = minListen, maxListen
        self.minSleep, self.maxSleep = minSleep, maxSleep

        # duration steps parameters
        self.beacon = random.randint(self.minBeacon, self.maxBeacon)
        self.listen = random.randint(self.minListen, self.maxListen)
        self.sleep = random.randint(self.minSleep, self.maxSleep)
        self.status = "beacon" #random.choice(["beacon", "listen", "sleep"])
        self.nextStatus = self.status
        self.cycle = 0
        self.buffer = 0 #empty buffer
        self.maxBuffer = 100

        self.historyStatus = {"beacon" : [self.beacon],
                              "listen" : [self.listen],
                              "sleep"  : [self.sleep],
                              "ble_connection" : [self.buffer]}

        self.averageSendTime = []   #TODO: implement this

        self.currentState()


    def currentState(self):
        '''This function define the device's working state 
        '''
        if self.status == "beacon":
            self.beacon -= 1
            if self.beacon == 0:
                self.nextStatus = "listen"
                self.listen = random.randint(self.minListen, self.maxListen)
                self.historyStatus["listen"].append(self.listen)

        if self.status == "listen":
            self.listen -= 1
            if self.listen == 0: 
                self.nextStatus = "sleep"
                self.sleep = random.randint(self.minSleep, self.maxSleep)
                self.historyStatus["sleep"].append(self.sleep)
            if self.buffer >= self.maxBuffer:
                self.listen = 0
                self.nextStatus = "ble_connection"
                self.historyStatus["ble_connection"].append(0)

        if self.status == "sleep":
            self.sleep -= 1
            if self.sleep == 0:
                self.nextStatus = "beacon"
                self.beacon = random.randint(self.minBeacon, self.maxBeacon)
                self.historyStatus["beacon"].append(self.beacon)
                self.cycle = 2

        if self.status == "ble_connection": # TODO: is not considered the time needed to transfer the data
            # uint32_t (time) | uint8_t * 8 (uuid) | int8_t (rssi) -> 13byte every row
            self.nextStatus = "sleep"

        

        self.status = self.nextStatus
                
                
    def energyBehaviour(self):
        '''This function analyze the energy consumption of the esp32
        '''
        if self.cycle == 2:
            # last sleep cycle
            # self.energyConsumption += self.sleepPower * self.unitTime
            
            self.energyPeriods.append(self.energyConsumption)
            self.cycle = 0

        if self.status == "beacon":
            if self.cycle == 0: self.energyConsumption = 0
            self.cycle = 1
            self.energyConsumption += self.beaconPower * self.unitTime
            self.instantPower = self.beaconPower
        elif self.status == "listen":
            self.energyConsumption += self.listenPower * self.unitTime
            self.instantPower = self.listenPower
        elif self.status == "sleep":
            self.energyConsumption += self.sleepPower * self.unitTime
            self.instantPower = self.sleepPower
        elif self.status == "ble_connection":            
            self.data = self.buffer * 13
            self.bleTime = (self.data * 8) / self.freq
            self.buffer = 0 # now is an empty buffer
            self.energyConsumption += self.ble_connectionPower * self.bleTime
            self.instantPower = self.ble_connectionPower

