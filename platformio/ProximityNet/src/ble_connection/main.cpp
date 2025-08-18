#include <Arduino.h>
#include <NimBLEDevice.h>

#define SERVICE_UUID        "19B10000-E8F2-537E-4F6C-D104768A1214"
#define CHARACTERISTIC_UUID "19B10001-E8F2-537E-4F6C-D104768A1214"

NimBLEServer* pServer;
NimBLECharacteristic* pCharacteristic;

// Variabili di stato globali
bool deviceConnected = false;
bool clientSubscribed = false;
uint16_t connection_handle = 0; // Per memorizzare l'ID della connessione
int packetsSent = 0;            // Contatore per i pacchetti inviati

class ServerCallbacks : public NimBLEServerCallbacks {
public:
    void onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) override {
        Serial.println("\n\n✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅");
        Serial.print("✅   CALLBACK ON_CONNECT ATTIVATO! Client: ");
        Serial.println(connInfo.getAddress().toString().c_str());
        Serial.println("✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅\n\n");
        
        deviceConnected = true;
        connection_handle = connInfo.getConnHandle(); // <-- Memorizziamo l'handle
        packetsSent = 0;                              // <-- Azzeriamo il contatore per la nuova sessione
    }

    void onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) override {
        Serial.println("\n--- ON_DISCONNECT ATTIVATO ---");
        deviceConnected = false;
        clientSubscribed = false;
        connection_handle = 0; // Reset dell'handle
    }
};

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

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n===== AVVIO Notifier (5 Pacchetti e Disconnessione) =====");

    NimBLEDevice::init("ESP-FIX"); 

    pServer = NimBLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());

    NimBLEService* pService = pServer->createService(SERVICE_UUID);
    pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY | NIMBLE_PROPERTY::WRITE
    );
    pCharacteristic->setCallbacks(new CharacteristicCallbacks());
    pCharacteristic->setValue("Ready");
    
    pService->start();
    NimBLEAdvertising* pAdvertising = NimBLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->start();
    Serial.println("📡 Advertising avviato...");
}

// --- LOOP MODIFICATO ---
void loop() {
    // La condizione per iniziare a inviare è sempre la stessa
    if (deviceConnected && clientSubscribed) {
        
        // Controlliamo se abbiamo già inviato i 5 pacchetti
        if (packetsSent < 5) {
            static unsigned long lastSend = 0;
            // Inviamo un pacchetto ogni 2 secondi
            if (millis() - lastSend > 2000) {
                lastSend = millis();
                
                packetsSent++; // Incrementiamo il contatore
                String value = "Pacchetto #" + String(packetsSent) + "/5";
                
                pCharacteristic->setValue(value);
                pCharacteristic->notify();
                
                Serial.print("-> Notifica inviata: ");
                Serial.println(value);
            }
        } 
        // Se abbiamo inviato 5 pacchetti, inviamo il segnale di fine e chiudiamo la connessione
        else {
            // Controlliamo di non aver già inviato il segnale "END"
            // (il loop è veloce, potremmo entrare qui più volte)
            if (packetsSent == 5) {
                Serial.println("--- 5 pacchetti inviati. Invio segnale 'END'. ---");
                pCharacteristic->setValue("END");
                pCharacteristic->notify();
                
                packetsSent++; // Incrementiamo a 6 per non rientrare in questo blocco
                
                delay(100); // Diamo un istante allo stack BLE per inviare il pacchetto
                
                if (connection_handle != 0) {
                    Serial.println("--- Chiusura connessione. ---");
                    pServer->disconnect(connection_handle);
                }
            }
        }
    }
    
    delay(100);
}



/****************************** below for test behaviour, implemented in espComplete *********************/
// #include "NimBLEDevice.h"

// #define SERVICE_UUID        "19B10000-E8F2-537E-4F6C-D104768A1214"
// #define CHARACTERISTIC_UUID "19B10001-E8F2-537E-4F6C-D104768A1214"

// // Variabili di stato globali
// bool deviceConnected = false;
// bool clientSubscribed = false;
// uint16_t connection_handle = 0; // Per memorizzare l'ID della connessione
// int packetsSent = 0;            // Contatore per i pacchetti inviati
// uint32_t startAdv = 0;

// class CharacteristicCallbacks : public NimBLECharacteristicCallbacks {
//     void onSubscribe(NimBLECharacteristic* pCharacteristic, NimBLEConnInfo& connInfo, uint16_t subValue) override {
//         if(subValue > 0) {
//              Serial.println("\n--- ON_SUBSCRIBE ATTIVATO ---");
//              clientSubscribed = true;
//         } else {
//              Serial.println("\n--- SOTTOSCRIZIONE ANNULLATA ---");
//              clientSubscribed = false;
//         }
//     }
// };


// std::string deviceName = "espName01";

// NimBLEServer *pServer;// = NimBLEDevice::createServer();
// NimBLEService *pService;// = pServer->createService(SERVICE_UUID);
// NimBLECharacteristic *pCharacteristic;// = pService->createCharacteristic(CHARACTERISTIC_UUID);
// NimBLEAdvertising *pAdvertising;// = NimBLEDevice::getAdvertising();

// const uint8_t maxChunkSize = 100;
// struct BLElog{
//   uint32_t time;
//   uint16_t uuid;
//   int8_t rssi;    // as defined in functions
// };
// BLElog logFile[maxChunkSize];
// uint8_t logIndex = 40;
// uint8_t numData = 40;


// void setup() {
//     Serial.begin(115200);
//     delay(100);
//     randomSeed(analogRead(A0));
//     NimBLEDevice::init(deviceName);

//     pServer = NimBLEDevice::createServer();
//     pService = pServer->createService(SERVICE_UUID);
//     pCharacteristic = pService->createCharacteristic(CHARACTERISTIC_UUID, 
//         NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::NOTIFY
//         );
//     pAdvertising = NimBLEDevice::getAdvertising();
    
//     pCharacteristic->setCallbacks(new CharacteristicCallbacks());
//     pService->start();
//     // pCharacteristic->setValue("Hello BLE");
//     pAdvertising->addServiceUUID(SERVICE_UUID); // advertise the UUID of our service
//     pAdvertising->setName(deviceName); // advertise the device name
// }

// void loop() {
//     if (clientSubscribed == false) pAdvertising->start(); delay(50);

//     if (clientSubscribed == true) {
//         pAdvertising->stop(); delay(50);

//         // create data
//         logIndex = numData;
//         for (int i = 0; i<numData; i++) {
//             logFile[i].time = millis();
//             logFile[i].uuid = 12;
//             logFile[i].rssi = random(1,100);
//             logIndex--;
//             delay(random(500,1500));
//         }
    
//         // create chunked data
//         for (int i = 0; i<numData; i++) {
//             pCharacteristic->setValue((uint8_t*)&logFile[i], sizeof(logFile[i]));
    
//             bool ok = pCharacteristic->notify();
//             if (!ok) {
//             Serial.println("Notify fallita, ritento...");
//             delay(10);    // aspetta un po’ per non saturare lo stack
//             i--;          // riprova lo stesso pacchetto
//             } 
//             else {
//             Serial.printf("Inviato pkt %d: time=%lu, uuid=%d, rssi=%d\n",
//                             i, logFile[i].time, logFile[i].uuid, logFile[i].rssi);
//             delay(5);     // piccolo pacing per sicurezza
    
//             }
//         }
//     }
//     // uint32_t value1 = millis();
//     // uint8_t value2 = random(1, 100);
//     // uint8_t payload[5];
//     // payload[0] = (value1 >> 24) & 0xFF;  // byte più significativo
//     // payload[1] = (value1 >> 16) & 0xFF;
//     // payload[2] = (value1 >> 8)  & 0xFF;
//     // payload[3] = value1 & 0xFF;          // byte meno significativo
//     // payload[4] = value2;
//     // uint32_t millisValue = (payload[0] << 24) | payload[1] << 16 | payload[2] << 8 | payload[3];
//     // uint8_t randomValue = payload[4];
//     // Serial.printf("millis=%d, random=%d\n", millisValue, payload[4]);
//     // delay(50);
//     // pAdvertiùsing->start(); 
//     // delay(10000);
    
//     // if (pAdvertising->isAdvertising() && (millis() - startAdv) >= 10000000) {
//     // pAdvertising->stop();
//     // delay(5000);
//     // }
// }