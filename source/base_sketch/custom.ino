#include <Arduino.h>
#include <NimBLEDevice.h>
#include <NimBLEEddystoneTLM.h>
#include <sys/time.h>
#include <esp_sleep.h>


#include "esp_system.h" 
// Purtoppo l'IDE di arduino non supporta gli import da directory diverse da quella dello sketch "main"
// Per tanto si perde la modularità dell'approccio a classi e vanno copia-incollate in ogni nuovo sketch, a meno che non si crei
// una vera e propria libreria per ciascuna di esse, ma poi diventa asimmetrico l'utilizzo e l'installazione tra linux e windows.
#include "manager.h"
#include "wifimanager.h"
#include "esp_wifi.h"
// Documentazione necessaria -> https://h2zero.github.io/NimBLE-Arduino/index.html


/**************************/
/*    GLOBAL VARIABLES    */
/**************************/
uint64_t UUID = ((uint64_t)esp_random() << 32) | esp_random();
const char* ssid = "****";
const char* password = "****";
const char* server_ip = "192.168.1.13";
const int port = 9999;


Manager* blemanager = nullptr;
WifiManager* wifimanager = nullptr;


void setup() {
  Serial.begin(115200);
  delay(100);  
  randomSeed(analogRead(0));

  int minMs = 10000;
  int maxMs = 30000;

  int listenMs = minMs + (esp_random() % (maxMs - minMs + 1));
  int advMs = 10000;
  int power = 3;
  blemanager = new Manager(UUID, listenMs, advMs, power);
  wifimanager = new WifiManager(ssid, password, server_ip, port);
}

void loop() {
  delay(1000);
  blemanager->doOneCycle();
  wifimanager->sendMessage();
  Serial.printf("\n\n--------------------------------------------\n\n");
}
