import matplotlib.pyplot as plt
import random

# in this code is used the Monte Carlo simulation to analyze the statistical behaviour of the P-NET 
# supposing each esp32 works in the following way:
# beacon | listen (random) | sleep (random)


class device():
    '''This class define the behaviour of an esp32 as a Finite State Machine
    '''

    
    def __init__(self, name:str="", tBeacon:int=1):
        self.name = name

        self.maxListen = 10
        self.maxSleep = 10

        self.beacon = tBeacon
        self.listen = random.randint(1, self.maxListen)
        self.sleep = random.randint(1, self.maxSleep)
        self.status = random.choice(["beacon", "listen", "sleep"])

        self.averageSendTime = []   #TODO: implement this

        self.currentState()


    def currentState(self):

        if self.status == "beacon":
            self.status = "listen"
            self.listen = random.randint(1, self.maxListen)
        
        elif self.status == "listen":
            if self.listen > 0: self.listen -= 1
            else: 
                self.status = "sleep"
                self.sleep = random.randint(1, self.maxSleep)

        elif self.status == "sleep":
            if self.sleep > 0: self.sleep -= 1
            else:
                self.status = "beacon"








##################################################### MAIN #########################################
# define each esp32 in the radius of interest
deviceNumber = 30       # supposing around one device there are 30 peoples
devices = []
for i in range(deviceNumber):
    devices.append(device(name=f"device{i}"))

# define the duration of the event
duration = 4*60*60 #4 hours

# analysis parameters
listSends = {}
deviceMessages = {}     # stores the number of devices : amount of detected positions

for deviceNumber_ in range(deviceNumber):
    
    positionDetected = 0    # how many times is detected the position?
    
    # analysis
    for d in range(duration):
            
        # count sends
        sends = 0
        i = 0
        for i in range(deviceNumber_):
            if devices[i].status == "beacon": 
                # TODO: check receivers
                sends += 1
            devices[i].currentState()    # update device status

        # listSends[d] = sends

        l = 0   # how many devices are listening?
        for i in range(deviceNumber):
            if devices[i].status == "listen":
                l += 1  
        
        if l >= 3 and sends == 1:
            positionDetected += 1

    deviceMessages[f"{deviceNumber_}"] = positionDetected

print("Finish simulation")

x = list(deviceMessages.keys())
y = list(deviceMessages.values())

# Plot
plt.figure(figsize=(12, 5))
plt.plot(x, y, linewidth=0.8)
plt.xlabel("number of devices")
plt.ylabel("number of position detected in total")
plt.title("")
plt.grid(True)
plt.tight_layout()
plt.show()


        