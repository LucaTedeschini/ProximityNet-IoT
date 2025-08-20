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
  char uuid[8];
  uint8_t rssi;
};
const uint8_t maxChunkSize = 3;
BLElog logFile[maxChunkSize];
uint8_t logIndex = 0;


/************************* BEACON ************************/
uint64_t UUID = ((uint64_t)esp_random() << 32) | esp_random();
NimBLEAdvertising* pAdvertising;// = NimBLEDevice::getAdvertising();

/************************** LISTEN *************************/
NimBLEScan* pScan = NimBLEDevice::getScan();  // retrieve the object used to scan

/************************** BLE_CONNECTION *************************/
#define SERVICE_UUID        "19B10000-E8F2-537E-4F6C-D104768A1214"
#define CHARACTERISTIC_UUID "19B10001-E8F2-537E-4F6C-D104768A1214"
bool once = false;
bool clientSubscribed = false;
NimBLEServer *pServer;// = NimBLEDevice::createServer();
NimBLEService *pService;// = pServer->createService(SERVICE_UUID);
NimBLECharacteristic *pCharacteristic;// = pService->createCharacteristic(CHARACTERISTIC_UUID);
NimBLEAdvertising* pAdvServer;
// NimBLEAdvertising *pAdvertising;// = NimBLEDevice::getAdvertising();

/******************************************************* FUNCTIONS **********************************************/
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
      if (manufacturerData.length() >= 2 &&
        manufacturerData[0] == 0x37 &&
        manufacturerData[1] == 0x13) { //TODO: modify lenght check with our packet lenght


          //Check CRC
          uint8_t received_crc = manufacturerData[11];
          if (crc8((uint8_t*)manufacturerData.c_str(), 11) != received_crc) {
              Serial.println("CRC Errato, pacchetto scartato.");
              return;
          }
          Serial.print("Dispositivo trovato: ");
          Serial.println(advertisedDevice->toString().c_str());
          
          logFile[logIndex].time = millis();
          memcpy(logFile[logIndex].uuid, &manufacturerData[3], 8);
          logFile[logIndex].rssi = (uint8_t)advertisedDevice->getRSSI();// + 255;
          
          Serial.print("RSSI: ");
          Serial.println(advertisedDevice->getRSSI());
          // Serial.println(logFile[logIndex].rssi);
          
          logIndex++; 
      
          if (logIndex >= maxChunkSize) {
            Serial.println("Buffer pieno, fermo la scansione.");
            pScan->stop();
            currentState = State::BLE_CONNECTION;
            // La transizione di stato avverrà nel loop principale
            }

      }
    }
  }
} scanCallbacks;

/************************** BLE_CONNECTION *************************/
class CharacteristicCallbacks : public NimBLECharacteristicCallbacks {
    void onSubscribe(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo, uint16_t subValue) override {
        if(subValue > 0) {
             Serial.println("\n--- ON_SUBSCRIBE ATTIVATO ---");
             clientSubscribed = true;
        } else {
             Serial.println("\n--- SOTTOSCRIZIONE ANNULLATA ---");
             clientSubscribed = false;
        }
    }
};

void setBLEConnection() {
    NimBLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
    oAdvertisementData.setName(deviceName);
    pAdvServer->addServiceUUID(SERVICE_UUID); // advertise the UUID of our service
    pAdvServer->setAdvertisementData(oAdvertisementData);//setName(deviceName); // advertise the device name
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
    pAdvServer = NimBLEDevice::getAdvertising();

    
    pServer = NimBLEDevice::createServer();
    pService = pServer->createService(SERVICE_UUID);    
    pCharacteristic = pService->createCharacteristic(CHARACTERISTIC_UUID, 
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::NOTIFY
        );
    
    pCharacteristic->setCallbacks(new CharacteristicCallbacks());
    
    
    /************************** LISTEN *************************/
    pScan->setActiveScan(false);            //we are interestend on receiving only
    pScan->setDuplicateFilter(false);       //can receive the same packet multiple time
    pScan->setScanCallbacks(new ScanCallbacks());
    


}

void loop() {
  switch(currentState) {
    case State::BEACON:{
      setBeacon();
      /************************* BEACON ************************/
      uint8_t beaconDuration = 1;
      Serial.printf("\n--- Stato: BEACON (per %d secondi) ---\n", beaconDuration);
      pAdvertising->start();
      delay(beaconDuration * 1000);//5000);
      pAdvertising->stop();
      currentState = State::LISTEN;
      delay(100);
      break;
    }

    case State::LISTEN:{
      /************************** LISTEN *************************/
      uint8_t listenDuration = random(3, 11);
      uint8_t lDuration = listenDuration;
      Serial.printf("\n--- Stato: LISTEN (per %d secondi) ---\n", listenDuration);
      pScan->setInterval(45);//every scanInterval * 0.625ms starts the scan for a window period in a different channel among 37, 38 and 39 channels)
      pScan->setWindow(15);//scan for windowScan * 0.625ms (must be windowScan < scanInterval)
      
      uint32_t now = millis();
      pScan->start(0);//listenDuration*1000);
      delay(listenDuration * 1000);
      pScan->stop();
      if (currentState != State::BLE_CONNECTION) currentState = State::SLEEP;
      delay(100);
      break;
    }

    case State::SLEEP:{
      /************************** SLEEP *************************/
      uint8_t sleepDuration = random(3, 11);
      Serial.printf("\n--- Stato: SLEEP (per %d secondi) ---\n", sleepDuration);
      Serial.flush();
      esp_sleep_enable_timer_wakeup(sleepDuration * 1000000); //is in [us]
      esp_light_sleep_start();
      currentState = State::BEACON;
      break;
    }

    case State::BLE_CONNECTION:{
      /************************** BLE_CONNECTION *************************/
      if (once == false) {
        setBLEConnection();
        Serial.printf("\n--- Stato: BLE_CONNECTION ---\n"); 
        pService->start(); 
        pAdvServer->start(); 
        once = true;
        delay(50);
        ble_connection_timeout = millis();
      }

    
      if (millis() - ble_connection_timeout > 30*1000) {
        currentState = State::SLEEP;
        //pService->stop();
        pAdvServer->stop();
        once = false;
      }

      if (clientSubscribed == true) {
        pAdvServer->stop(); 
        delay(50);

        uint8_t app = logIndex;
    
        // create chunked data
        for (int i = 0; i<app; i++) {
          pCharacteristic->setValue((uint8_t*)&logFile[i], sizeof(logFile[i]));
  
          bool ok = pCharacteristic->notify();
          if (!ok) {
            Serial.println("Notify fallita, ritento...");
            delay(10);    // aspetta un po’ per non saturare lo stack
            i--;          // riprova lo stesso pacchetto
          } 
          else {
            Serial.printf("Inviato pkt %d: time=%lu, uuid=%d, rssi=%d\n",
                            i, logFile[i].time, logFile[i].uuid, logFile[i].rssi);
            delay(5);     // piccolo pacing per sicurezza
            logIndex--;
          }
          
          if (logIndex <= 0 | clientSubscribed == false) {
            currentState = State::SLEEP; 
            once = false;
          } 
        }
      }
    }
  } 
}

