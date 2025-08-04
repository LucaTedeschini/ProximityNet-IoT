#ifndef WIFIMANAGER_H
#define WIFIMANAGER_H

#include <WiFiUdp.h>


// TODO: add logic to restore connection after a disconnection
class WifiManager {
  public:
    WifiManager(const char* ssid, const char* password, const char* server_ip, const int port);
    void sendMessage();
  private:
    const char* ssid;
    const char* password;
    const char* server_ip;
    const int port;
    WiFiUDP udp;
};




#endif