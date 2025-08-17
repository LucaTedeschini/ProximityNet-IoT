#include <Arduino.h>
#include <NimBLEDevice.h>
#include <utilities.h>

uint64_t UUID = ((uint64_t)esp_random() << 32) | esp_random();
NimBLEAdvertising* pAdvertising = NimBLEDevice::getAdvertising();


void setBeacon() {
    NimBLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
    uint8_t customData[12];
    customData[0] = 0x37;
    customData[1] = 0x13;
    customData[2] = 0x01;
    memcpy(&customData[3], &UUID, 8);
    uint8_t crc = crc8(customData, 11);
    customData[11] = crc;

    for(int i=0; i<12; i++) Serial.printf("%02X ", customData[i]);



    oAdvertisementData.setName("esp32-sender");
    oAdvertisementData.setManufacturerData(std::string((char*)customData, sizeof(customData)));
    pAdvertising->setAdvertisementData(oAdvertisementData);

}

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("Avvio ESP32 come Beacon-Only...");
  //esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT);

  NimBLEDevice::init("esp32-init");
  NimBLEDevice::setPower(3);
  setBeacon();
  NimBLEAdvertisementData oAdvertisementData;
  
}

void loop() { 
  Serial.println("Start adv\n");
  pAdvertising->start();
  delay(5000);
  pAdvertising->stop();
  Serial.println("Stop adv\n");
  delay(500);
}

