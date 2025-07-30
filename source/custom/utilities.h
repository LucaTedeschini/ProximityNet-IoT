#ifndef UTILITIES_H
#define UTILITIES_H

#include <NimBLEDevice.h>

/**
 * Classe che gestisce i pacchetti ricevuti in ascolto.
 * Per ora li logga sul monitor seriale.
 */
class ScanCallbacks : public NimBLEScanCallbacks {
public:
    void onResult(const NimBLEAdvertisedDevice* advertisedDevice) override;
};

void setBeacon(NimBLEAdvertising* pAdvertising, uint64_t* UUID);

#endif