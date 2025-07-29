#include <Arduino.h>
#include <NimBLEDevice.h>
#include <NimBLEEddystoneTLM.h>
#include <sys/time.h>
#include <esp_sleep.h>
// Documentazione necessaria -> https://h2zero.github.io/NimBLE-Arduino/index.html

/******************************/
/*    CONSTANT DEFINITIONS    */
/******************************/
// parametro qua sotto modificabile per tarare la distanza entro il quale si vede il dispositivo
#define BEACON_POWER             3  // 3dbm
// Definita da noi
#define PROTOCOL_VERSION 0x01
// Nome del device
#define DEVICE_NAME "ProximityNet"

/**************************/
/*    GLOBAL VARIABLES    */
/**************************/
// `pAdvertising` gestisce tutto ciò che è inerente alla trasmissione
NimBLEAdvertising* pAdvertising;
// `pBLEScan` gestisce tutto ciò che è inerente alla ricezione
NimBLEScan* pBLEScan;
// Definizion dello UUID dell'utente. Per ora è casuale
uint64_t UUID = ((uint64_t)esp_random() << 32) | esp_random();
// Variabile che contiene il delta time di ascolto
int listenDuration;
// Variabile che contiene il delta time di trasmissione
int advertisingDuration;


/******************/
/*    UTILITIES   */
/******************/
//^^^^ da spostare in un file a parte ^^^^

class ScanCallbacks : public NimBLEScanCallbacks {
  // Classe che gestisce i pacchetti ricevuti in ascolto. Per ora li logga sul monitor seriale
    void onResult(const NimBLEAdvertisedDevice* advertisedDevice) override {
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
            
            int device_rssi = (int)advertisedDevice->getRSSI();
            Serial.printf("Found custom beacon!\n");
            Serial.printf("Packet length: %d\n", (int)strManufacturerData.length());
            Serial.printf("RSSI: %d\n", device_rssi);

            // Utilizzare la protocolVersion è utile per gestire diverse versioni, in vista di una ipotetica "release". Attualmente però è inutile.
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
} scanCallbacks;


void setBeacon() {
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

void setup() {
  // Nel setup si accende tutto e si settano le impostazioni
  Serial.begin(115200);
  NimBLEDevice::init(DEVICE_NAME);
  NimBLEDevice::setPower(BEACON_POWER);

  pBLEScan = BLEDevice::getScan();
  pBLEScan->setScanCallbacks(&scanCallbacks);
  // Guardare la documentazione per queste, sono valori di default
  pBLEScan->setActiveScan(true);
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(100);

  pAdvertising = NimBLEDevice::getAdvertising();
  // Chiamando setBeacon() si prepara il messaggio che verrà pubblicizzato nell'etere
  setBeacon();
  delay(5000);
  Serial.printf("My UUID is 0x%016llX\n", UUID);
}

void loop() {
  advertisingDuration = random(100000, 150001);
  Serial.printf("Advertising started for %dms \n", advertisingDuration);
  pAdvertising->start();
  delay(advertisingDuration);
  pAdvertising->stop();
  listenDuration = random(5000, 5001);
  Serial.printf("Listening for %dms\n", listenDuration);
  NimBLEScanResults foundDevices = pBLEScan->getResults(listenDuration, false);
  pBLEScan->clearResults();
  Serial.printf("Scan done!\n");
  Serial.printf("Restarting...\n");
  delay(1);
}
