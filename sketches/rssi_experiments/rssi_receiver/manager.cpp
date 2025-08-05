#include <Arduino.h> // Per Serial
#include <NimBLEDevice.h>

#include "manager.h"

void ScanCallbacks::onResult(const NimBLEAdvertisedDevice* advertisedDevice) {
    if (advertisedDevice->haveManufacturerData()) {
        // Il manufacturer data è salvato come stringa in quanto array di char (= array di bytes)
        std::string strManufacturerData = advertisedDevice->getManufacturerData();

        // Il nostro pacchetto ha 11 bytes = 2 (Company ID) + 1 (versione) + 8 (UUID). è espandibile
        if (strManufacturerData.length() >= 11 &&
            (uint8_t)strManufacturerData[0] == 0x37 &&
            (uint8_t)strManufacturerData[1] == 0x13) {
            
            int device_rssi = advertisedDevice->getRSSI();
            this->lastRSSI = device_rssi;
            this->foundMatchingDevice = true;
        }
    }
}

void ScanCallbacks::reset() {
  this->foundMatchingDevice = false;
  this->lastRSSI = 0;
}

Manager::Manager(uint64_t uuid, int listenMs, int advMs, int beaconPower) :
  deviceName("ProximityNetNode") {
    Serial.printf("Building manager...\n");
    this->UUID = uuid;
    this->advertisingDuration = advMs;
    this->listenDuration = listenMs;
    this->protocolVersion = 0x01;
    this->beaconPower = beaconPower;
    this->cycle_counter = 0;

    //NimBLE initalization
    NimBLEDevice::init(this->deviceName);
    NimBLEDevice::setPower(this->beaconPower);
    this->pBLEScan = BLEDevice::getScan();
    this->pBLEScan->setScanCallbacks(&this->scanCallbacks);
    this->pBLEScan->setActiveScan(true);
    this->pBLEScan->setInterval(100);
    this->pBLEScan->setWindow(100);
    this->pAdvertising = NimBLEDevice::getAdvertising();
    this->setBeacon();
    Serial.printf("\tDone!\n");

}

void Manager::setBeacon() {
  NimBLEAdvertisementData oAdvertisementData;
  // Custom data di dimensione 10 byte
  uint8_t customData[11];

  // Company ID fittizio, 0x1337 è libero ed usabile per progetti (little endian, quindi scriverlo specchiato)
  customData[0] = 0x37;
  customData[1] = 0x13;

  // Qua invece si possono scrivere i dati CUSTOM. noi possiamo mettere un identificativo del protocollo e poi l'ID dell'utente
  customData[2] = this->protocolVersion;

  //Copio 8 bytes dello UUID (tutto) dentro customData dalla posizione 3
  memcpy(&customData[3], &this->UUID, 8);
  oAdvertisementData.setName(this->deviceName);
  // Inserisci il Manufacturer Data
  oAdvertisementData.setManufacturerData(std::string((char*)customData, sizeof(customData)));
  pAdvertising->setAdvertisementData(oAdvertisementData);
}

int Manager::listenMessages() {
  //do something with this
  NimBLEScanResults foundDevices = this->pBLEScan->getResults(this->listenDuration, false);
  this->pBLEScan->clearResults();
  return 0; //success
}

int Manager::advertiseMessage() {
  this->pAdvertising->start();
  delay(this->advertisingDuration);
  this->pAdvertising->stop();
  return 0; //success
}

void Manager::doOneCycle() {
  int result;
  Serial.printf("Starting advertising\n");
  result = this->advertiseMessage();
  if (result > 0){
    //do stuff, something broke
  }
  Serial.printf("Starting Scanning\n");
  result = this->listenMessages();
  if (result > 0){
    //do stuff, something broke
  }
  Serial.printf("Done\n");

  // do something with this cycle?
  this->cycle_counter += 1;
}

int Manager::checkRSSI() {
  this->scanCallbacks.reset();
  this->pBLEScan->getResults(this->listenDuration, false);
  this->pBLEScan->clearResults();

  if (this->scanCallbacks.foundMatchingDevice) {
    return this->scanCallbacks.lastRSSI;
  } else {
    return -999;
  }

}