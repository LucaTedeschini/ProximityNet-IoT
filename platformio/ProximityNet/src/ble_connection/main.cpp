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