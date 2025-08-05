#include <WiFi.h>
#include <WiFiUdp.h>
#include "wifimanager.h"


WifiManager::WifiManager(const char* ssid, const char* password, const char* server_ip, const int port) : 
  ssid(ssid),
  password(password),
  server_ip(server_ip),
  port(port)
{
  //Set the wifimode to (STA)tion (able to connect to routers)
  WiFi.mode(WIFI_STA);

  Serial.printf("Trying to connect to wifi...");
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }
  Serial.printf("Connected! ");
  Serial.println(WiFi.localIP());
}

void WifiManager::sendMessage() {
  this->udp.beginPacket(this->server_ip, this->port);
  this->udp.print("Prova\n");
  this->udp.endPacket();
}