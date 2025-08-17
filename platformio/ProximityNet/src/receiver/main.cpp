/*
   Based on Neil Kolban example for IDF: https://github.com/nkolban/esp32-snippets/blob/master/cpp_utils/tests/BLE%20Tests/SampleScan.cpp
   Ported to Arduino ESP32 by Evandro Copercini
*/

#include <Arduino.h>
#include <NimBLEDevice.h>
#include <NimBLEAdvertisedDevice.h>
#include "NimBLEEddystoneTLM.h"
#include "NimBLEBeacon.h"
#include <utilities.h>

#define ENDIAN_CHANGE_U16(x) ((((x) & 0xFF00) >> 8) + (((x) & 0xFF) << 8))


/************ GLOBAL VARIABLES ************/
BLEAdvertising* pAdvertising;
NimBLEScan* pScan = NimBLEDevice::getScan();  // retrieve the object used to scan
NimBLEServer* pServer;// = NimBLEDevice::createServer();
NimBLECharacteristic* pCharacteristic;
NimBLEAdvertisementData serverAdvData;
NimBLEAdvertisementData beaconAdvData;

enum class State{ BEACON, LISTEN, SLEEP, BLE_DEVICE };
State currentState = State::BEACON; //the esp32 starts in this state
uint8_t beaconDuration = 1; //1 second

bool advStops = false;
const uint8_t maxChunkSize = 100;

struct BLElog{
  uint32_t time;
  char uuid[8];
  int8_t rssi;    // as defined in functions
};
BLElog logFile[maxChunkSize];
uint8_t logIndex = 0;

unsigned long bleDeviceStartTime = 0;     //timestamp of the esp32
const unsigned long bleDeviceTimeout = 300 * 1000;    //timer of 5 min (300 * 1000)

uint32_t now = 0;
uint8_t lDuration = 0;


/************************************* FUNCTIONS *******************************************/
void advertisingStopped(NimBLEAdvertising* pAdv){
  Serial.println("Advertisement finished");
  if(currentState == State::BEACON) currentState = State::LISTEN;
};


void sendDataToDevice(BLElog* data, int lenData) {
  Serial.println("Device connected, sendind data");
  for (int i = 0; i < logIndex; i++){
    uint8_t buffer[13];  //maximum 20 bytes per time

    memcpy(&buffer[0], &logFile[i].time, sizeof(uint32_t));
    memcpy(&buffer[4], &logFile[i].uuid, 8);
    memcpy(&buffer[12], &logFile[i].rssi, sizeof(int8_t));

    pCharacteristic->setValue(buffer, sizeof(buffer));
    pCharacteristic->notify();
    delay(20);                                                      // FIX: better add an akcnoledgment from the device 
  }
  Serial.println("Data sent");
  logIndex = 0;
};

// Callback per quando viene trovato un dispositivo durante la scansione
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
          logFile[logIndex].rssi = advertisedDevice->getRSSI();
          
          Serial.print("RSSI: ");
          Serial.println(logFile[logIndex].rssi);
          
          logIndex++; 
      
          if (logIndex >= maxChunkSize) {
            Serial.println("Buffer pieno, fermo la scansione.");
            pScan->stop();
            currentState = State::BLE_DEVICE;
            // La transizione di stato avverrà nel loop principale
            }

      }
    }
  }
} scanCallbacks;


// Callback per gli eventi del server (connessione/disconnessione)
class serverCallbacks : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer* pServer, ble_gap_conn_desc* desc) {
    Serial.println("Dispositivo connesso");
    sendDataToDevice(logFile, logIndex);
  }

  void onDisconnect(NimBLEServer* pServer) {
    Serial.println("Dispositivo disconnesso");
    // Dopo la disconnessione, si torna a dormire per ricominciare il ciclo
    currentState = State::SLEEP; 
  }
};

 



/************************************************ MAIN ********************************************/

void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(A0));
  char deviceName[] = "esp32_1";
  
  NimBLEDevice::init(deviceName);
  NimBLEDevice::setPower(3);  //-3dBm, to confirm
  
  

  /****************** CREATE ADVERTISEMENT DATA ***********************/
  NimBLEAdvertisementData advData;
  uint8_t customData[12]; //12 bytes
  
  customData[0] = 0x37;   //fake ID 0x1337 (little endian)
  customData[1] = 0x13;   //fake ID 0x1337 (little endian)
  
  uint8_t protocolVersion = 000;
  customData[2] = protocolVersion;
  
  char UUID[] = "try_uuid";
  memcpy(&customData[3], UUID, 8);  //copy 8 bytes of UUID in customData
  
  uint8_t crc = crc8(customData, 11);   //comput crc byte
  customData[11] = crc;
  
  // use the manufacturer data as payload field
  beaconAdvData.setName(deviceName);
  beaconAdvData.setManufacturerData(std::string((char*)customData, sizeof(customData)));  // maximum 31 bytes
  pAdvertising = NimBLEDevice::getAdvertising();
  pAdvertising->setAdvertisementData(advData);
  pAdvertising->setAdvertisingCompleteCallback(advertisingStopped); //callback function, called when the transmission is complete
    
    

  /****************** SETUP LISTEN ADVERTISING ***********************/
  pScan->setActiveScan(false);            //we are interestend on receiving only
  pScan->setDuplicateFilter(false);       //can receive the same packet multiple time
  pScan->setScanCallbacks(new ScanCallbacks());
  
  
  
  /****************** SETUP SLEEP ***********************/
  
  /****************** SETUP BLE_DEVICE ***********************/
  serverAdvData.setName(deviceName);
  serverAdvData.setFlags(BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP);
  serverAdvData.addServiceUUID("1234");

  pServer = NimBLEDevice::createServer(); //create an istance of a server
  pServer->setCallbacks(new serverCallbacks());
  
  char serviceUUID[] = "1234";
  NimBLEService* pService = pServer->createService(serviceUUID);
  pCharacteristic = pService->createCharacteristic(
    "ABCD",
    NIMBLE_PROPERTY::NOTIFY | NIMBLE_PROPERTY::READ /*the client receive notifications, there are also WRITE and READ*/
    );
  pService->start();
  }
  



void loop() {

  switch(currentState){
    /******************************* BEACON *******************************/
    case State::BEACON:{
      if (!pAdvertising->isAdvertising()) {
        Serial.printf("\n--- Stato: BEACON (per %d secondi) ---\n", beaconDuration);
        pAdvertising->setAdvertisementData(beaconAdvData);
        pAdvertising->start(beaconDuration * 1000);  //if beaconDuration == 0 will advertise forever
        // delay(20);
      }
      break;
    }

    /******************************* LISTEN *******************************/
    case State::LISTEN: {
      if (!pScan->isScanning()) {
        uint8_t listenDuration = random(3, 11);
        lDuration = listenDuration;
        Serial.printf("\n--- Stato: LISTEN (per %d secondi) ---\n", listenDuration);
        pScan->setInterval(45);//every scanInterval * 0.625ms starts the scan for a window period in a different channel among 37, 38 and 39 channels)
        pScan->setWindow(15);//scan for windowScan * 0.625ms (must be windowScan < scanInterval)
        
        now = millis();

        pScan->start(listenDuration*1000);
        
      }

      if (pScan->isScanning() && (millis() - now > lDuration * 1000)) {
        Serial.print("forced stop listen status");
        pScan->stop();
        currentState = State::SLEEP;
      }

      // if (logIndex >= maxChunkSize) currentState = State::BLE_DEVICE;
      // else currentState = State::SLEEP;
      break;
    }
      
    /******************************* SLEEP *******************************/
    case State::SLEEP: {
      uint8_t sleepDuration = random(3, 11);
      esp_sleep_enable_timer_wakeup(sleepDuration * 1000000);
      Serial.printf("\n--- Stato: SLEEP (per %d secondi) ---\n", sleepDuration);
      Serial.flush();
      esp_light_sleep_start();
      Serial.print("Light sleep finished");
      
      currentState = State::BEACON; //the data is already sended to the device
      break;
    }
        
    /******************************* BLE_DEVICE *******************************/
    case State::BLE_DEVICE: {
      if (!pAdvertising->isAdvertising()){      // only once time, execute the advertising and the timer
        Serial.println("State: BLE_DEVICE. Waiting for a client...");
        pAdvertising->setAdvertisementData(serverAdvData);
        pAdvertising->start();
        bleDeviceStartTime = millis();
      }
      
      if (pAdvertising->isAdvertising() && (millis() - bleDeviceStartTime > bleDeviceTimeout)) {
        Serial.println("BLE_DEVICE Timeout:No client connected");
        pAdvertising->stop(); 
        
        Serial.println("deleted data");                           // FIX: save data in the flash memory and send it later
        logIndex = 0;
        
        currentState = State::SLEEP;
      }
      break;
    }

  }
  delay(10);
  
}