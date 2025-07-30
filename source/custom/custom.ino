#include <Arduino.h>
#include <NimBLEDevice.h>
#include <NimBLEEddystoneTLM.h>
#include <sys/time.h>
#include <esp_sleep.h>

#include "constants.h"
#include "utilities.h"
// Documentazione necessaria -> https://h2zero.github.io/NimBLE-Arduino/index.html


/**************************/
/*    GLOBAL VARIABLES    */
/**************************/
// `pAdvertising` gestisce tutto ciò che è inerente alla trasmissione
NimBLEAdvertising* pAdvertising;
// `pBLEScan` gestisce tutto ciò che è inerente alla ricezione
NimBLEScan* pBLEScan;
// Definizion dello UUID dell'utente. Per ora è casuale
uint64_t UUID = ((uint64_t)esp_random() << 32) | esp_random();
// Variabile che contiene il delta time di ascolto
int listenDuration;
// Variabile che contiene il delta time di trasmissione
int advertisingDuration;
// Definito in utilities.h
ScanCallbacks scanCallbacks;




void setup() {
  // Nel setup si accende tutto e si settano le impostazioni
  Serial.begin(115200);
  NimBLEDevice::init(DEVICE_NAME);
  NimBLEDevice::setPower(BEACON_POWER);

  pBLEScan = BLEDevice::getScan();
  pBLEScan->setScanCallbacks(&scanCallbacks);
  // Guardare la documentazione per queste, sono valori di default
  pBLEScan->setActiveScan(true);
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(100);

  pAdvertising = NimBLEDevice::getAdvertising();
  // Chiamando setBeacon() si prepara il messaggio che verrà pubblicizzato nell'etere
  setBeacon(pAdvertising, &UUID);
  delay(5000);
  Serial.printf("My UUID is 0x%016llX\n", UUID);
}

void loop() {
  advertisingDuration = random(1000, 1501);
  Serial.printf("Advertising started for %dms \n", advertisingDuration);
  pAdvertising->start();
  delay(advertisingDuration);
  pAdvertising->stop();
  listenDuration = random(5000, 5001);
  Serial.printf("Listening for %dms\n", listenDuration);
  NimBLEScanResults foundDevices = pBLEScan->getResults(listenDuration, false);
  pBLEScan->clearResults();
  Serial.printf("Scan done!\n");
  Serial.printf("Restarting...\n");
  delay(1);
}
