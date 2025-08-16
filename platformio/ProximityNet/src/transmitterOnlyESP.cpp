#include <Arduino.h>
#include <NimBLEDevice.h>
#include <utilities.h>

uint64_t UUID = ((uint64_t)esp_random() << 32) | esp_random();
auto pAdvertising = NimBLEDevice::getAdvertising();


void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("Avvio ESP32 come Beacon-Only...");
  esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT);
  char deviceName[] = "esp32_beacon_sender";

  NimBLEDevice::init(deviceName);
  NimBLEDevice::setPower(3);
  NimBLEAdvertisementData oAdvertisementData;
  // Custom data di dimensione 10 byte
  uint8_t customData[12];

  // Company ID fittizio, 0x1337 è libero ed usabile per progetti (little endian, quindi scriverlo specchiato)
  customData[0] = 0x37;
  customData[1] = 0x13;

  // Qua invece si possono scrivere i dati CUSTOM. noi possiamo mettere un identificativo del protocollo e poi l'ID dell'utente
  customData[2] = 0x01;

  //Copio 8 bytes dello UUID (tutto) dentro customData dalla posizione 3
  memcpy(&customData[3], &UUID, 8);
  //Aggiunta byte CRC
  uint8_t crc = crc8(customData, 11);
  customData[11] = crc;

  for(int i=0; i<12; i++) Serial.printf("%02X ", customData[i]);
  
  // Inserisci il Manufacturer Data
  oAdvertisementData.setName(deviceName);
  std::vector<uint8_t> dataVec(customData, customData + sizeof(customData));
  oAdvertisementData.setManufacturerData(dataVec);//std::string((char*)customData, sizeof(customData)));
  pAdvertising->setAdvertisementData(oAdvertisementData);

  
}

void loop() { 
  pAdvertising->start();

  delay(5000);
  pAdvertising->stop();

  // Il loop può rimanere vuoto.
  // Lo stack NimBLE gestirà l'advertising in background.
  // Aggiungiamo un delay per non sovraccaricare il processore inutilmente.
  delay(500);
}

