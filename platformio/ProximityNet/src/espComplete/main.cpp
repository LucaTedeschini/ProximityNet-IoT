#include <Arduino.h>
#include <NimBLEDevice.h>
#include <utilities.h>
#include <NimBLEAdvertisedDevice.h>
#include "NimBLEEddystoneTLM.h"
#include "NimBLEBeacon.h"


/******************************************************* GLOBAL VARIABLES ****************************************/
std::string deviceName = "esp00";
enum class State{ BEACON, LISTEN, SLEEP, BLE_CONNECTION };
State currentState = State::BEACON; //the esp32 starts in this state

struct BLElog{  //7 bytes
  uint32_t time;
  char my_uuid[8];
  char uuid[8];
  uint8_t rssi;
};
const uint8_t maxChunkSize = 1;
BLElog logFile[maxChunkSize];
uint8_t logIndex = 0;


/************************* BEACON ************************/
uint64_t UUID = ((uint64_t)esp_random() << 32) | esp_random();
NimBLEAdvertising* pAdvertising;

/************************** LISTEN *************************/
NimBLEScan* pScan = NimBLEDevice::getScan();

/************************** BLE_CONNECTION *************************/
#define SERVICE_UUID        "19B10000-E8F2-537E-4F6C-D104768A1214"
#define CHARACTERISTIC_UUID "19B10001-E8F2-537E-4F6C-D104768A1214"
bool once = false;
bool clientSubscribed = false;
NimBLEServer *pServer;
NimBLEService *pService;
NimBLECharacteristic *pCharacteristic;

/******************************************************* FUNCTIONS **********************************************/

// Callback per gestire connessioni/disconnessioni del server
class ServerCallbacks : public NimBLEServerCallbacks {
    void onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) override {
        Serial.println("✅ Client connesso!");
    }
    
    void onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) override {
        Serial.printf("❌ Client disconnesso, motivo: %d\n", reason);
        clientSubscribed = false;
        // NON riavviare l'advertising qui - lascia che sia gestito dal loop principale
        Serial.println("🔄 Gestione disconnessione completata");
    }
};

// Callback per le caratteristiche
class CharacteristicCallbacks : public NimBLECharacteristicCallbacks {
    void onSubscribe(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo, uint16_t subValue) override {
        if(subValue > 0) {
             Serial.println("🔔 ON_SUBSCRIBE ATTIVATO");
             clientSubscribed = true;
        } else {
             Serial.println("🔕 SOTTOSCRIZIONE ANNULLATA");
             clientSubscribed = false;
        }
    }
};

/************************* BEACON ************************/
void setBeacon() {
    NimBLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
    uint8_t customData[12];
    customData[0] = 0x37;
    customData[1] = 0x13;
    customData[2] = 0x01;
    memcpy(&customData[3], &UUID, 8);
    uint8_t crc = crc8(customData, 11);
    customData[11] = crc;

    oAdvertisementData.setName(deviceName);
    oAdvertisementData.setManufacturerData(std::string((char*)customData, sizeof(customData)));
    pAdvertising->setAdvertisementData(oAdvertisementData);
}

/************************** LISTEN *************************/
class ScanCallbacks : public NimBLEScanCallbacks {
  void onResult(const NimBLEAdvertisedDevice* advertisedDevice) override {
    if (advertisedDevice->haveName()) {
        Serial.print("Device name: ");
        Serial.println(advertisedDevice->getName().c_str());
        Serial.println("");
    }

    if (advertisedDevice->haveManufacturerData()) {
      std::string manufacturerData = advertisedDevice->getManufacturerData();
      if (manufacturerData.length() >= 12 &&
        manufacturerData[0] == 0x37 &&
        manufacturerData[1] == 0x13) {

          //Check CRC
          uint8_t received_crc = manufacturerData[11];
          if (crc8((uint8_t*)manufacturerData.c_str(), 11) != received_crc) {
              Serial.println("CRC Errato, pacchetto scartato.");
              return;
          }
          Serial.print("Dispositivo trovato: ");
          Serial.println(advertisedDevice->toString().c_str());
          if (logIndex < maxChunkSize) {
            logFile[logIndex].time = millis();
            memcpy(logFile[logIndex].my_uuid, &UUID, 8);
            memcpy(logFile[logIndex].uuid, &manufacturerData[3], 8);
            logFile[logIndex].rssi = (uint8_t)advertisedDevice->getRSSI();
          }
          
          Serial.print("RSSI: ");
          Serial.println(advertisedDevice->getRSSI());
          
          logIndex++; 
      
          if (logIndex >= maxChunkSize) {
            Serial.println("Buffer pieno, fermo la scansione.");
            currentState = State::BLE_CONNECTION;
          }
      }
    }
  }
} scanCallbacks;

/************************** BLE_CONNECTION *************************/
void setBLEConnection() {
    Serial.println("🔧 Configurazione advertising BLE...");
    
    // Ferma tutto prima di riconfigurare
    pAdvertising->stop();
    delay(200); // Aumenta il delay
    
    // Reset completo dell'advertising
    pAdvertising->reset();
    
    // Configurazione semplificata
    pAdvertising->setName(deviceName);
    pAdvertising->addServiceUUID(NimBLEUUID(SERVICE_UUID));
    
    // Configurazioni per connettibilità
    pAdvertising->setMinInterval(160); // 100ms
    pAdvertising->setMaxInterval(240); // 150ms
    
    Serial.println("✅ Configurazione BLE completata (semplificata)");
}

uint32_t ble_connection_timeout;

void setup() {
    Serial.begin(115200);
    delay(100);
    randomSeed(analogRead(A0));
    Serial.println("Avvio ESP32 (beacon, listen, sleep, ble_connection)");

    NimBLEDevice::init(deviceName);

    /************************* BEACON ************************/
    NimBLEDevice::setPower(3);
    pAdvertising = NimBLEDevice::getAdvertising();

    /************************** BLE SERVER *************************/
    // Crea e configura il server BLE subito nel setup
    pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());
    
    pService = pServer->createService(SERVICE_UUID);    
    pCharacteristic = pService->createCharacteristic(CHARACTERISTIC_UUID, 
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::NOTIFY
    );
    
    pCharacteristic->setCallbacks(new CharacteristicCallbacks());
    
    // IMPORTANTE: Avvia il servizio subito nel setup
    pService->start();
    Serial.println("✅ Servizio BLE creato nel setup");
    
    /************************** LISTEN *************************/
    pScan->setActiveScan(false);
    pScan->setDuplicateFilter(false);
    pScan->setScanCallbacks(new ScanCallbacks());
}

void loop() {
  switch(currentState) {
    case State::BEACON:{
      setBeacon();
      uint8_t beaconDuration = 1;
      Serial.printf("\n--- Stato: BEACON (per %d secondi) ---\n", beaconDuration);
      pAdvertising->start();
      delay(beaconDuration * 1000);
      pAdvertising->stop();
      currentState = State::LISTEN;
      delay(100);
      break;
    }

    case State::LISTEN:{
      uint8_t listenDuration = random(3, 11);
      Serial.printf("\n--- Stato: LISTEN (per %d secondi) ---\n", listenDuration);
      pScan->setInterval(45);
      pScan->setWindow(15);
      
      pScan->start(0);
      delay(listenDuration * 1000);
      pScan->stop();
      if (currentState != State::BLE_CONNECTION) {
        currentState = State::SLEEP;
      }
      delay(100);
      break;
    }

    case State::SLEEP:{
      uint8_t sleepDuration = random(3, 11);
      Serial.printf("\n--- Stato: SLEEP (per %d secondi) ---\n", sleepDuration);
      Serial.flush();
      esp_sleep_enable_timer_wakeup(sleepDuration * 1000000);
      esp_light_sleep_start();
      currentState = State::BEACON;
      break;
    }

    case State::BLE_CONNECTION:{
      if (once == false) {
        Serial.printf("\n--- Stato: BLE_CONNECTION ---\n"); 
        
        // Il servizio è già avviato nel setup, configura solo l'advertising
        setBLEConnection();
        pAdvertising->start();
        
        once = true;
        ble_connection_timeout = millis();
        Serial.println("📡 Advertising BLE avviato, in attesa di connessioni...");
      }

      // Timeout solo se non ci sono client connessi
      if (millis() - ble_connection_timeout > 30*1000 && !clientSubscribed) {
        Serial.println("⏰ Timeout BLE_CONNECTION, vado in SLEEP");
        currentState = State::SLEEP;
        pAdvertising->stop();
        once = false;
        break;
      }

      // Se c'è un client sottoscritto, invia i dati
      if (clientSubscribed == true && logIndex > 0) {
        Serial.printf("📤 Invio %d pacchetti al client...\n", logIndex);
        
        uint8_t packetsToSend = logIndex;
        
        for (int i = 0; i < packetsToSend; i++) {
          // Controlla se client ancora connesso prima di ogni invio
          if (!clientSubscribed) {
            Serial.println("❌ Client disconnesso durante invio");
            break;
          }
          
          pCharacteristic->setValue((uint8_t*)&logFile[i], sizeof(logFile[i]));

          bool ok = pCharacteristic->notify();
          if (!ok) {
            Serial.println("❌ Notify fallita, ritento...");
            delay(50);
            i--;
            continue;
          } 
          
          Serial.printf("✅ Inviato pkt %d: time=%lu, rssi=%d\n",
                          i, logFile[i].time, logFile[i].rssi);
          delay(20); // Aumenta il delay tra pacchetti
        }

        BLElog end_comm_packet;
        char zero_uuid[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
        end_comm_packet.time = millis();
        end_comm_packet.rssi = 0;
        memcpy(end_comm_packet.uuid, &zero_uuid, 8);
        memcpy(end_comm_packet.my_uuid, &zero_uuid, 8);

        pCharacteristic->setValue((uint8_t*)&end_comm_packet, sizeof(end_comm_packet));
        pCharacteristic->notify();
        delay(20);
        
        // Reset del buffer dopo invio
        logIndex = 0;
        Serial.println("✅ Tutti i pacchetti inviati!");
        pServer->disconnect(0); 

        unsigned long disconnectStart = millis();
        while (clientSubscribed && (millis() - disconnectStart < 2000)) {
            delay(10); // Aspetta che la callback di disconnessione sia chiamata
        }
        
        // Torna in SLEEP dopo aver inviato i dati
        currentState = State::SLEEP; 
        pAdvertising->stop();
        once = false;

      }
      
      // Piccolo delay per non saturare il loop
      delay(100);
      break;
    }
  } 
}