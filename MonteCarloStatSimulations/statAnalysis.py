import matplotlib.pyplot as plt
import random
from classes import device
import numpy as np

# in this code is used the Monte Carlo simulation to analyze the statistical behaviour of the P-NET 
# supposing each esp32 works in the following way:
# beacon | listen (random) | sleep (random)

#####################
# GLOBAL VARIABLES 
#####################
decimalNumber = 3               

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
duration = 10000

deviceNumber = 20


##############################################
# SIMULATION STORAGE
##############################################
detectedESPs = {f"{_}" : 0 for _ in range(1, deviceNumber+1)}     # stores {number of total devices : number of detections}
avgDetectionTime = {}   # average time to be detected
avgTotalEnergyConsumed = {} # average energy consumed

# #####################
# MAIN SIMULATION LOOP
# #####################
for deviceNumber_ in range(1, deviceNumber+1):
    # Create devices
    devices = [device(name=f"device{i}",
                      minBeacon=minBeacon, maxBeacon=maxBeacon,
                      minListen=minListen, maxListen=maxListen,
                      minSleep=minSleep, maxSleep=maxSleep)
               for i in range(deviceNumber_)]

    totalEnergy = {f"{_}" : [0] for _ in range(deviceNumber_)}
    timeDetections = {f"{_}" : [0] for _ in range(deviceNumber_)}
    for d in range(duration):
        sends = 0   # stores the number of sends during the duration
        listens = 0 # stores the number of listens during the duration
        detectedIndex = False

        for deviceIndex, dev in enumerate(devices):
            if dev.status == "beacon":
                sends += 1
                detectedIndex = deviceIndex
            if dev.status == "listen":
                listens += 1

            dev.energyBehaviour()
            totalEnergy[f"{deviceIndex}"].append(dev.energyConsumption)

            dev.currentState()

        if sends == 1 and listens > 0:
            detectedESPs[f"{deviceNumber_}"] += 1

            timeDetections[f"{detectedIndex}"].append(d)

    # energy calculations
    totalEnergy[f"{deviceNumber_}"] = [sum(dev.energyPeriods) for dev in devices]
    if deviceNumber_ > 0: avgTotalEnergyConsumed[f"{deviceNumber_}"] = sum(totalEnergy[f"{deviceNumber_}"]) / len(totalEnergy[f"{deviceNumber_}"])

    # time detection calculations
    avg = []
    for dev, times in timeDetections.items():
        s = 0
        for tIndex, t in enumerate(times):
            if tIndex > 0: 
                s += t - times[tIndex - 1]
        avg.append(s / len(times))
    avgDetectionTime[f"{deviceNumber_}"] = sum(avg) / len(avg)

    print(f"Done with {deviceNumber_} esps")


# #####################
# PLOTTING
# #####################

# manca solo plottare i 3 dizionari:
# detectedESPs
# avgDetectionTime
# avgTotalEnergyConsumed

x = list(detectedESPs.keys())

dicts = [detectedESPs, avgDetectionTime, avgTotalEnergyConsumed]
names = ["detected ESPs", "avg detection time", "energy total"]

fig, axes = plt.subplots(1, 3, figsize=(15, 4))  # 1 riga, 3 colonne

for ax, d, name in zip(axes, dicts, names):
    ax.plot(x, list(d.values()), marker="o")
    ax.set_title(name)         # titolo del singolo subplot
    ax.set_xlabel("device number")    # nome asse X
    ax.set_ylabel("Valori")    # nome asse Y
    ax.grid(True)

plt.tight_layout()
plt.savefig("dizionari_subplots.png", bbox_inches="tight")
plt.close()

        








































##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################
##################################################################################


# # # stores the power consumption of each esp considering range(deviceNumber+1)
# # timePower = [{f"{i}" : [] for i in range(deviceNumber)} for _ in range(deviceNumber)]
# # # timePower = {f"{i}" : [] for i in range(30)}
# # # stores the time instants of each esp beaing individuated considering range(deviceNumber+1)
# # timeInstansDetections = [{f"{i}" : [] for i in range(deviceNumber)} for _ in range(deviceNumber)]
# # # stores the total energy consumed in total
# # avgTotalEnergyConsumed = {}

# # #####################
# # MAIN SIMULATION LOOP
# # #####################
# for deviceNumber_ in range(1, deviceNumber+1):

#     # create object devices
#     devices = []
#     for i in range(deviceNumber_):
#         devices.append(device(name=f"device{i}",\
#                             minBeacon=minBeacon, maxBeacon=maxBeacon,\
#                             minListen=minListen, maxListen=maxListen,\
#                             minSleep=minSleep, maxSleep=maxSleep))
    
#     energyAvg = []
#     nearDeviceDetected = 0
    
#     # analysis
#     for d in range(duration):
            
#         sends = 0   # how many TX in one cycle
#         i = 0
#         l = 0       # how many listens in one cycle
#         statusDevice = []
#         detected = None    # stores the detected device index 
#         for i in range(deviceNumber_):
            
#             # Throughput parameters
#             if devices[i].status == "beacon":       # check TX
#                 sends += 1
#                 detected = i

#             if devices[i].status == "listen":       # check RX
#                 l += 1  

#             # energy behaviour  TODO: generalize with all devices
#             devices[i].energyBehaviour()
#             timePower[deviceNumber_ - 1][f"{i}"].append(devices[i].instantPower)
#             statusDevice.append(devices[i].status)

#             devices[i].currentState()       # update device status


#         if l > 0 and sends == 1:
#             # detection device counter
#             nearDeviceDetected += 1

#             # average time for an esp to be detected
#             timeInstansDetections[deviceNumber_-1][f"{detected}"].append(d)

#             index = 0
#             for index, status in enumerate(statusDevice):
#                 if status == "listen": devices[index].buffer += 1

#     for dev in range(deviceNumber_):
#         energyAvg.append(devices[dev].energyConsumption)  # usa il consumo totale accumulato
#     avgTotalEnergyConsumed[f"{deviceNumber_}"] = sum(energyAvg) / len(energyAvg)

        

#     detectedESPs[f"{deviceNumber_}"] = nearDeviceDetected

#     print(f"Analysis done with {deviceNumber_} devices")


# print("Finish simulation")



# # --- Dati da plottare ---
# # calcolo tempo medio di detection dai timeInstansDetections
# avgTimeEspDetected = {}
# for _ in range(len(timeInstansDetections)):
#     times = []
#     for key, value in timeInstansDetections[_].items():
#         if len(value) > 0:
#             for vIndex, v in enumerate(value):
#                 if vIndex > 0:
#                     times.append(v - value[vIndex-1])
#     if len(times) > 0:
#         avgTimeEspDetected[f"{_+1}"] = sum(times) / len(times)

# x_devices = list(avgTotalEnergyConsumed.keys())  # numero di dispositivi (stringhe "1","2",...)

# y_energy = []
# y_throughput = []
# y_detection = []

# for dev in x_devices:
#     # energia e throughput sempre presenti
#     y_energy.append(avgTotalEnergyConsumed[dev])
#     y_throughput.append(detectedESPs[dev])
#     # detection potrebbe mancare
#     if dev in avgTimeEspDetected:
#         y_detection.append(avgTimeEspDetected[dev])
#     else:
#         y_detection.append(0)   # oppure np.nan se preferisci


# # y_detection = list(avgTimeEspDetected.values())   # tempo medio detection

# # --- Plot ---
# x = np.arange(len(x_devices))  # posizioni sull'asse X
# width = 0.25                   # larghezza barre

# fig, ax = plt.subplots(figsize=(10,6))
# ax.bar(x - width, y_energy, width, label="Total Energy Consumed")
# ax.bar(x, y_detection, width, label="Avg Time Detection")
# ax.plot(x + width, y_throughput, width, label="Throughput")

# ax.set_xlabel("Device number")
# ax.set_title("Comparison of Energy, Detection Time and Throughput")
# ax.set_xticks(x)
# ax.set_xticklabels(x_devices)
# ax.legend()
# ax.grid(True, axis='y', linestyle="--", alpha=0.6)

# plt.tight_layout()
# plt.savefig("Comparison_results.png", dpi=300)
# plt.show()
# plt.close()




# # # print(f"Average period power consumption of device0 with 30 esps = "\
# # #       f"{sum(devices[0].energyPeriods) / len(devices[0].energyPeriods)} [J]")
# # # print(f"Total energy consumed = {sum(devices[0].energyPeriods)} [J]")


# # # time needed to be detected
# # s = 0

# # avgTimeEspDetected = {}
# # for _ in range(len(timeInstansDetections)):
# #     times = []
# #     for key, value in timeInstansDetections[_].items():
# #         if len(value) > 0:
# #             for vIndex, v in enumerate(value):
# #                 if vIndex > 0:
# #                     times.append(v - value[vIndex-1])

# #     if len(times) > 0:
# #         avgTimeEspDetected[_] = sum(times) / len(times)

# # print(f" Average cycles needed to be detected with a certain number of esps: \n {avgTimeEspDetected}")

# # xTime = list(avgTimeEspDetected.keys())
# # yTime = list(avgTimeEspDetected.values())

# # # instant energy plotted
# # x_timePower = list(range(len(timePower[3]["0"][100:500])))
# # y_timePower = list(timePower[3]["0"][100:500])

# # x_throughput = list(detectedESPs.keys()) # number of devices
# # y_throughput = list(detectedESPs.values())    # number of near devices detected

# # # FIGURA UNICA CON 3 PLOT
# # fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15,5))

# # # Primo plot: bar
# # ax1.bar(xTime, yTime)
# # ax1.set_xlabel("Device number")
# # ax1.set_ylabel("Average time detection")
# # ax1.set_title("Average time needed to be detected detected")

# # # Secondo plot: time-power
# # ax2.plot(x_timePower, y_timePower, linewidth=0.8)
# # ax2.set_xlabel("time over duration")
# # ax2.set_ylabel("instant power [W]")
# # ax2.set_title("time-power (device0 power)")
# # ax2.grid(True)

# # # Terzo plot: throughput
# # ax3.plot(x_throughput, y_throughput, linewidth=0.8)
# # ax3.set_xlabel("number of devices")
# # ax3.set_ylabel(f"number of devices detected")
# # ax3.set_title(f"throughput ({duration} cycles)")
# # ax3.grid(True)

# # plt.tight_layout()
# # plt.savefig("Final results.png", dpi=300)
# # plt.show()
# # plt.close()

# # # s = 0

# # # avgTimeEspDetected = {}
# # # for _ in range(len(timeInstansDetections)):
# # #     times = []
# # #     for key, value in timeInstansDetections[_].items():
# # #         if len(value) > 0:
# # #             for vIndex, v in enumerate(value):
# # #                 if vIndex > 0: times.append(v - value[vIndex-1])

# # #     if len(times) > 0: avgTimeEspDetected[_] = sum(times) / len(times)
# # # print(f" Average time needed to be detected with a certain number of esps: \n {avgTimeEspDetected}")

# # # xTime = list(avgTimeEspDetected.keys())
# # # yTime = list(avgTimeEspDetected.values())

# # # plt.bar(xTime, yTime)
# # # plt.xlabel("Device number")
# # # plt.ylabel("Average time detection")
# # # plt.title("Average time needed to be detected detected")
# # # plt.savefig("Average time to be detected")
# # # plt.show()
# # # plt.close()

# # # # instant energy plotted
# # # x_timePower = list(range(len(timePower["0"][100:500])))
# # # y_timePower = list(timePower["0"][100:500])

# # # x_throughput = list(detectedESPs.keys()) # number of devices
# # # y_throughput = list(detectedESPs.values())    # number of near devices detected

# # # fig, (ax_timePower, ax_throughput) =plt.subplots(2, 1, figsize=(8,6))

# # # ax_timePower.plot(x_timePower, y_timePower, linewidth=0.8)
# # # ax_timePower.set_xlabel("time over duration")
# # # ax_timePower.set_ylabel("instant power [W]")
# # # ax_timePower.set_title("time-power (device0 power)")
# # # ax_timePower.grid(True)

# # # ax_throughput.plot(x_throughput, y_throughput, linewidth=0.8)
# # # ax_throughput.set_xlabel("number of devices")
# # # ax_throughput.set_ylabel(f"number of devices detected")
# # # ax_throughput.set_title(f"throughput ({duration} cycles)")
# # # ax_throughput.grid(True)

# # # plt.tight_layout()
# # # plt.show()
# # input("Press something to exit ...")


        