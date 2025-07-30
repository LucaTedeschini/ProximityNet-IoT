#include <Arduino.h>
#include <NimBLEDevice.h>
#include <NimBLEEddystoneTLM.h>
#include <sys/time.h>
#include <esp_sleep.h>

#include "esp_system.h" 
#include "manager.h"
// Documentazione necessaria -> https://h2zero.github.io/NimBLE-Arduino/index.html


/**************************/
/*    GLOBAL VARIABLES    */
/**************************/
uint64_t UUID = ((uint64_t)esp_random() << 32) | esp_random();


Manager* blemanager = nullptr;


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
}

void loop() {
  delay(1000);
  blemanager->doOneCycle();
  Serial.printf("\n\n--------------------------------------------\n\n");
}
