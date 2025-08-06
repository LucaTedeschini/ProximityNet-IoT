#include <Arduino.h> // Per Serial
#include <NimBLEDevice.h>

#include "manager.h"
#include "utilities.h"

void ScanCallbacks::onResult(const NimBLEAdvertisedDevice* advertisedDevice) {
    if (advertisedDevice->haveManufacturerData()) {
      // Il manufacturer data è salvato come stringa in quanto array di char (= array di bytes)
      std::string strManufacturerData = advertisedDevice->getManufacturerData();
      // Il nostro pacchetto ha 11 bytes = 2 (Company ID) + 1 (versione) + 8 (UUID). è espandibile
      if (strManufacturerData.length() >= 11 &&
          (uint8_t)strManufacturerData[0] == 0x37 &&
          (uint8_t)strManufacturerData[1] == 0x13) {

            // Extract CRC byte
            const uint8_t* received_packet = (const uint8_t*)strManufacturerData.data();
            uint8_t received_crc = received_packet[11];
            uint8_t calculated_crc = crc8(received_packet, 11);

            if (calculated_crc == received_crc) {
              int device_rssi = advertisedDevice->getRSSI();
              Serial.println("Found custom beacon!");
              Serial.printf("Packet length: %d\n", (int)strManufacturerData.length());
              Serial.printf("RSSI: %d\n", device_rssi);

              uint8_t protocolVersion = strManufacturerData[2];
              Serial.printf("Protocol version: 0x%02X\n", protocolVersion);

              uint64_t uuid = 0;
              memcpy(&uuid, strManufacturerData.data() + 3, 8);
              Serial.printf("UUID: 0x%016llX\n", uuid);
            }
            else {
              // Packet is corrupted!
              Serial.println("Found custom beacon, but CRC is INVALID. Discarding packet.");
            }
            

      } else {
          // Non ci serve gestire pacchetti diversi dai nostri
          //Serial.println("Found manufacturer data, but not our custom beacon.");
      }
    }
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
  uint8_t customData[12];

  // Company ID fittizio, 0x1337 è libero ed usabile per progetti (little endian, quindi scriverlo specchiato)
  customData[0] = 0x37;
  customData[1] = 0x13;

  // Qua invece si possono scrivere i dati CUSTOM. noi possiamo mettere un identificativo del protocollo e poi l'ID dell'utente
  customData[2] = this->protocolVersion;

  //Copio 8 bytes dello UUID (tutto) dentro customData dalla posizione 3
  memcpy(&customData[3], &this->UUID, 8);
  //Aggiunta byte CRC
  uint8_t crc = crc8(customData, 11);
  customData[11] = crc;
  
  // Inserisci il Manufacturer Data
  oAdvertisementData.setName(this->deviceName);
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

void Manager::setTimeWakeUp(int seconds) {
  //This function initialize the deep sleep working mode
  esp_sleep_enable_timer_wakeup(seconds * 1000000);  //is in microseconds
  Serial.println("Deep sleep setted at " + String(seconds) + " seconds.\n");
}