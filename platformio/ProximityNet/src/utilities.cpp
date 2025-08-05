#include <Arduino.h>

uint8_t crc8(const uint8_t *data, int len) {
  uint8_t crc = 0x00;
  while (len--) {
    uint8_t extract = *data++;
    for (uint8_t tempI = 8; tempI; tempI--) {
      uint8_t sum = (crc ^ extract) & 0x01;
      crc >>= 1;
      if (sum) {
        crc ^= 0x8C; // Polinomio invertito per CRC-8-DVB-S2
      }
      extract >>= 1;
    }
  }
  return crc;
}