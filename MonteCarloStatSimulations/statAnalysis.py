import matplotlib.pyplot as plt
import random
from classes import device

# in this code is used the Monte Carlo simulation to analyze the statistical behaviour of the P-NET 
# supposing each esp32 works in the following way:
# beacon | listen (random) | sleep (random)

#####################
# GLOBAL VARIABLES 
#####################
decimalNumber = 3



##################################################### MAIN #########################################
B = 12
b = B * 8
minBeacon, maxBeacon = 1, 1
minListen, maxListen = 1, 10
minSleep, maxSleep = 1, 10

Vcc = 3.3
beaconPower = Vcc * 130e-3  #[W]
listenPower = Vcc * 100e-3  #[W]
sleepPower = Vcc * 0.8e-3   #[W]

frequecy = 240e+6
unitTime = b / (frequecy) # one unit time = time needed to send one beacon with 240MHz

# hours = 4
# duration = (hours*60*60)/unitTime #4 hours, event duration
duration = 100000









###################################
# average power consumption of a cycle: beacon | listen | sleep
###################################

# print(f"\n\nduration: {duration} beacon cycles")
# print(f"borders of power consumption of a cycle:\n"\
#       f"min = {round((minBeacon*beaconPower + minListen*listenPower + minSleep*sleepPower)\
#             * unitTime * 1e+9, decimalNumber)}[nJ]\n"\
#       f"max = {round((maxBeacon*beaconPower + maxListen*listenPower + maxSleep*sleepPower)\
#                * unitTime * 1e+6, decimalNumber)}[uJ]")

# energy = []
# oneESP = device()
# oneESP.name = "energy consumption"
# for d in range(duration):
#     power = 0
#     beacon = random.randint(minBeacon, maxBeacon)
#     listen = random.randint(minListen, maxListen)
#     sleep = random.randint(minSleep, maxSleep)

#     for b in range(beacon): power += beaconPower
#     for l in range(listen): power += listenPower
#     for s in range(sleep): power += sleepPower

#     energy.append(power * unitTime)
    
# print(f"Total energy consumed: {sum(energy)}[J]")
# print(f"Average energy consumed during one cycle: {sum(energy) / len(energy)}[J]\n")












##############################################
# statistical analysis
##############################################
deviceNumber = 30

deviceMessages = {}     # stores the number of devices : amount of detected positions
timePower = {f"{i}" : [] for i in range(30)}

for deviceNumber_ in range(1, deviceNumber):

    devices = []
    for i in range(deviceNumber_):
        devices.append(device(name=f"device{i}",\
                            minBeacon=minBeacon, maxBeacon=maxBeacon,\
                            minListen=minListen, maxListen=maxListen,\
                            minSleep=minSleep, maxSleep=maxSleep))
    
    energyAvg = []
    nearDeviceDetected = 0
    
    # analysis
    for d in range(duration):
            
        sends = 0   # how many TX in one cycle
        i = 0
        l = 0       # how many listens in one cycle
        for i in range(deviceNumber_):

            if devices[i].status == "beacon":       # check TX
                sends += 1

            if devices[i].status == "listen":       # check RX
                l += 1  

            if deviceNumber_ == 29: 
                devices[i].energyBehaviour()
                timePower[f"{i}"].append(devices[i].instantPower)
            devices[i].currentState()       # update device status

        if l > 0 and sends == 1:
            nearDeviceDetected += 1

    deviceMessages[f"{deviceNumber_}"] = nearDeviceDetected

    print(f"Analysis done with {deviceNumber_} devices")


print("Finish simulation")
print(f"Average period power consumption of device0 = "\
      f"{sum(devices[0].energyPeriods) / len(devices[0].energyPeriods)} [J]")
print(f"Total energy consumed = {sum(devices[0].energyPeriods)} [J]")


# instant energy plotted
x_timePower = list(range(len(timePower["0"][100:500])))
y_timePower = list(timePower["0"][100:500])

x_throughput = list(deviceMessages.keys()) # number of devices
y_throughput = list(deviceMessages.values())    # number of near devices detected

fig, (ax_timePower, ax_throughput) =plt.subplots(2, 1, figsize=(8,6))

ax_timePower.plot(x_timePower, y_timePower, linewidth=0.8)
ax_timePower.set_xlabel("time over duration")
ax_timePower.set_ylabel("instant power [W]")
ax_timePower.set_title("time-power (device0 power)")
ax_timePower.grid(True)

ax_throughput.plot(x_throughput, y_throughput, linewidth=0.8)
ax_throughput.set_xlabel("number of devices")
ax_throughput.set_ylabel(f"number of devices detected")
ax_throughput.set_title(f"throughput ({duration} cycles)")
ax_throughput.grid(True)

plt.tight_layout()
plt.show()
input("Press something to exit ...")


        