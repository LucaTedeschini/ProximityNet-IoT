#include <Arduino.h>
#include <NimBLEDevice.h>
#include <NimBLEEddystoneTLM.h>
#include <sys/time.h>
#include <esp_sleep.h>


#include "esp_system.h" 
#include "manager.h"
#include "wifimanager.h"
#include "esp_wifi.h"
// Documentazione necessaria -> https://h2zero.github.io/NimBLE-Arduino/index.html


/**************************/
/*    GLOBAL VARIABLES    */
/**************************/
uint64_t UUID = ((uint64_t)esp_random() << 32) | esp_random();
// REMEMBER TO CHANGE TEHESE VARIABLES
const char* ssid = "espwifi";
const char* password = "espwifii";
const char* server_ip = "172.26.252.207";
const int port = 9999;


Manager* blemanager = nullptr;
WifiManager* wifimanager = nullptr;


void setup() {
  Serial.begin(115200);
  delay(100);  
  randomSeed(analogRead(0));

  int minMs = 10000;
  int maxMs = 30000;

  int listenMs = 5000;
  int advMs = 10000;
  int power = 3;
  blemanager = new Manager(UUID, listenMs, advMs, power);
  wifimanager = new WifiManager(ssid, password, server_ip, port);
  delay(5000);
  Serial.printf("\n\n--------------------------------------------\n\n");
}

void loop() {
  int received_rssi;
  char buffer[32];
  for (int i = 0; i<10; i++) {
    Serial.printf("Prepare the test at %i meters! Starting in a few seconds\n", i+1);
    delay(5000);
    for (int j=0; j<5;j++) {
      Serial.printf("\tStarting %d/5 iteration...\n", j+1);
      received_rssi = blemanager->checkRSSI();
      sprintf(buffer, "%d / %d", i+1, received_rssi);
      wifimanager->sendMessage(buffer);
      Serial.printf("\t\tFinished %d/10 iteration...\n", j+1);
      delay(100);
    }
  }
}
