/*
   Based on Neil Kolban example for IDF: https://github.com/nkolban/esp32-snippets/blob/master/cpp_utils/tests/BLE%20Tests/SampleScan.cpp
   Ported to Arduino ESP32 by Evandro Copercini
*/

#include <Arduino.h>
#include <NimBLEDevice.h>
#include <NimBLEAdvertisedDevice.h>
#include "NimBLEEddystoneTLM.h"
#include "NimBLEBeacon.h"

// Penso che questo cambi da little endian a big endian e viceversa.
// avendo x a 16 bit, poniamolo a 1111111100000000. nel blocco a sinistra viene mascherato
// con un and con 1111111100000000 e a sinistra con 0000000011111111
// a sinistra viene poi shiftato di 8 bit a destra, per tanto diventa 000000000000000011111111. Viene sommato con l'altra parte shiftata di 8 bit a sinistra, per tanto
// 000000000000000011111111 +
// 111111110000000000000000 =
// 111111110000000011111111 ->  tagliato perchè è 16 bit -> 0000000011111111
//
// prendendo x = 0000000011111111 invece
// 000000000000000000000000 +
// 000000001111111100000000 = 1111111100000000
#define ENDIAN_CHANGE_U16(x) ((((x) & 0xFF00) >> 8) + (((x) & 0xFF) << 8))


int         scanTime = 5 * 1000; // In milliseconds
NimBLEScan* pBLEScan;

class ScanCallbacks : public NimBLEScanCallbacks {
    // Classe che eredita da NimBLEScanCallbacks. Tramite questa classe è possibile ridefinire i comportamenti
    // che l'esp32 deve fare per ogni callback. More here https://h2zero.github.io/NimBLE-Arduino/class_nim_b_l_e_scan_callbacks.html
    void onResult(const NimBLEAdvertisedDevice* advertisedDevice) override {
        // "Called when a new scan result is complete, including scan response data (if applicable)."
        // Il parametro in input di tipo NimBLEAdvertisedDevice (https://h2zero.github.io/NimBLE-Arduino/class_nim_b_l_e_advertised_device.html)
        // è l'oggetto contenente tutte le informazioni relative al dispositivo appena scansionato
        if (advertisedDevice->haveName()) {
            Serial.print("Device name: ");
            Serial.println(advertisedDevice->getName().c_str());
            Serial.println("");
        }

        if (advertisedDevice->haveServiceUUID()) {
            NimBLEUUID devUUID = advertisedDevice->getServiceUUID();
            Serial.print("Found ServiceUUID: ");
            Serial.println(devUUID.toString().c_str());
            Serial.println("");
        } else if (advertisedDevice->haveManufacturerData() == true) {
            //Il manufacturerdata è un campo di dati custom che un produttore di un dispositivo bluetooth può aggiungere nei pacchetti adv.
            //Noi qua dentro ci metteremo i nostri campi custom di cui avremo bisogno. Abbiamo circa 20 byte di spazio (dipende da come strutturiamo il pacchetto),
            //Può arrivare anche a 25. Il campo è strutturato in questo modo (idelamente)
            // Lenght (1 byte)
            // Type (0xFF) (1 byte)
            // Company ID (2 byte, little endian)
            // payload (N byte)
            std::string strManufacturerData = advertisedDevice->getManufacturerData();

            // Quando si usa getManufacturerData, il primo byte di lunghezza viene tolto e si può accedervi tramite .lenght().
            // il controllo sstrManufacturerData[0] == 0x4C && strManufacturerData[1] == 0x00 serve ad identificare il manufacturer, che in questo caso è Apple (0x4C00)
            // I campi iBeacon (di apple) hanno lunghezza di 25Byte, e sono strutturati diversamente, ma ciò non ci riguarda.

            if (strManufacturerData.length() == 25 && strManufacturerData[0] == 0x4C && strManufacturerData[1] == 0x00) {
                Serial.println("Found an iBeacon!");
                // NimBLEBeacon a quanto pare gestisce i pacchetti iBeacon. Noi possiamo farci la nostra classe
                NimBLEBeacon oBeacon = NimBLEBeacon();
                oBeacon.setData(reinterpret_cast<const uint8_t*>(strManufacturerData.data()), strManufacturerData.length());
                Serial.printf("iBeacon Frame\n");
                Serial.printf("ID: %04X Major: %d Minor: %d UUID: %s Power: %d\n",
                              oBeacon.getManufacturerId(),
                              ENDIAN_CHANGE_U16(oBeacon.getMajor()),
                              ENDIAN_CHANGE_U16(oBeacon.getMinor()),
                              oBeacon.getProximityUUID().toString().c_str(),
                              oBeacon.getSignalPower());
            } else {
                Serial.println("Found another manufacturers beacon!");
                Serial.printf("strManufacturerData: %d ", strManufacturerData.length());
                for (int i = 0; i < strManufacturerData.length(); i++) {
                    Serial.printf("[%X]", strManufacturerData[i]);
                }
                Serial.printf("\n");
            }
            return;
        }

        // Qua sotto la stessa logica ma per i pacchetti EddystoneTLM (0xFEAA), che sono di Google
        NimBLEUUID eddyUUID = (uint16_t)0xfeaa;

        if (advertisedDevice->getServiceUUID().equals(eddyUUID)) {
            std::string serviceData = advertisedDevice->getServiceData(eddyUUID);
            if (serviceData[0] == 0x20) {
                Serial.println("Found an EddystoneTLM beacon!");
                NimBLEEddystoneTLM foundEddyTLM = NimBLEEddystoneTLM();
                foundEddyTLM.setData(reinterpret_cast<const uint8_t*>(serviceData.data()), serviceData.length());

                Serial.printf("Reported battery voltage: %dmV\n", foundEddyTLM.getVolt());
                Serial.printf("Reported temperature from TLM class: %.2fC\n", (double)foundEddyTLM.getTemp());
                int   temp     = (int)serviceData[5] + (int)(serviceData[4] << 8);
                float calcTemp = temp / 256.0f;
                Serial.printf("Reported temperature from data: %.2fC\n", calcTemp);
                Serial.printf("Reported advertise count: %d\n", foundEddyTLM.getCount());
                Serial.printf("Reported time since last reboot: %ds\n", foundEddyTLM.getTime());
                Serial.println("\n");
                Serial.print(foundEddyTLM.toString().c_str());
                Serial.println("\n");
            }
        }
    }
} scanCallbacks;

// E qua fa tuttecose
void setup() {
    Serial.begin(115200);
    Serial.println("Scanning...");

    NimBLEDevice::init("Beacon-scanner");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setScanCallbacks(&scanCallbacks);
    pBLEScan->setActiveScan(true);
    pBLEScan->setInterval(100);
    pBLEScan->setWindow(100);
}

void loop() {
    NimBLEScanResults foundDevices = pBLEScan->getResults(scanTime, false);
    Serial.print("Devices found: ");
    Serial.println(foundDevices.getCount());
    Serial.println("Scan done!");
    pBLEScan->clearResults(); // delete results scan buffer to release memory
    delay(2000);
}