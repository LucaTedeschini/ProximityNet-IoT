#include <Arduino.h> // Per Serial
#include <NimBLEDevice.h>

#include "utilities.h"
#include "constants.h"

void ScanCallbacks::onResult(const NimBLEAdvertisedDevice* advertisedDevice) {
    // Questo if in realtà non ci serve, lavoriamo solamente con il ManufacturerData
    if (advertisedDevice->haveName()) {
        Serial.print("Device name: ");
        Serial.println(advertisedDevice->getName().c_str());
        Serial.println();
    }

    if (advertisedDevice->haveManufacturerData()) {
        // Il manufacturer data è salvato come stringa in quanto array di char (= array di bytes)
        std::string strManufacturerData = advertisedDevice->getManufacturerData();

        // Il nostro pacchetto ha 11 bytes = 2 (Company ID) + 1 (versione) + 8 (UUID). è espandibile
        if (strManufacturerData.length() >= 11 &&
            (uint8_t)strManufacturerData[0] == 0x37 &&
            (uint8_t)strManufacturerData[1] == 0x13) {
            
            int device_rssi = advertisedDevice->getRSSI();
            Serial.println("Found custom beacon!");
            Serial.printf("Packet length: %d\n", (int)strManufacturerData.length());
            Serial.printf("RSSI: %d\n", device_rssi);

            uint8_t protocolVersion = strManufacturerData[2];
            Serial.printf("Protocol version: 0x%02X\n", protocolVersion);

            uint64_t uuid = 0;
            memcpy(&uuid, strManufacturerData.data() + 3, 8);
            Serial.printf("UUID: 0x%016llX\n", uuid);
        } else {
            // Non ci serve gestire pacchetti diversi dai nostri
            //Serial.println("Found manufacturer data, but not our custom beacon.");
        }
    }
}

void setBeacon(NimBLEAdvertising* pAdvertising, uint64_t* UUID) {
  // Funzione che si occupa della trasmissione.

  NimBLEAdvertisementData oAdvertisementData;
  // Custom data di dimensione 10 byte
  uint8_t customData[11];

  // Company ID fittizio, 0x1337 è libero ed usabile per progetti (little endian, quindi scriverlo specchiato)
  customData[0] = 0x37;
  customData[1] = 0x13;

  // Qua invece si possono scrivere i dati CUSTOM. noi possiamo mettere un identificativo del protocollo e poi l'ID dell'utente
  customData[2] = PROTOCOL_VERSION;

  //Copio 8 bytes dello UUID (tutto) dentro customData dalla posizione 3
  memcpy(&customData[3], &UUID, 8);
  oAdvertisementData.setName(DEVICE_NAME);
  // Inserisci il Manufacturer Data
  oAdvertisementData.setManufacturerData(std::string((char*)customData, sizeof(customData)));
  pAdvertising->setAdvertisementData(oAdvertisementData);
}
