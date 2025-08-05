#ifndef MANAGER_H
#define MANAGER_H

#include <NimBLEDevice.h>

class ScanCallbacks : public NimBLEScanCallbacks {
public:
    void onResult(const NimBLEAdvertisedDevice* advertisedDevice) override;
    int lastRSSI = 0;
    bool foundMatchingDevice = false;

    void reset();
};

class Manager {
public:
  Manager(uint64_t uuid, int listenMs, int advMs, int beaconPower);
  void doOneCycle();
  int checkRSSI();
private:
  void setBeacon(); //done
  int listenMessages(); //done
  int advertiseMessage(); //done
  const char* deviceName; //done
  char protocolVersion; //done
  int advertisingDuration; //done
  int listenDuration; //done 
  uint64_t UUID; //done
  int cycle_counter;
  int beaconPower; //done
  NimBLEAdvertising* pAdvertising; //done
  NimBLEScan* pBLEScan; //done
  ScanCallbacks scanCallbacks; //done
};

#endif