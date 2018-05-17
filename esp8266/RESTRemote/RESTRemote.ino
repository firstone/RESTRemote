#include <WiFiManager.h>

#include "Blinker.hh"
#include "CodeRegistry.hh"
#include "CodeServer.hh"
#include "IRInterface.hh"

constexpr char MODULE_NAME[] = "RESTRemote IR Module";

constexpr int PIN_IN = 14; // Receiving pin
constexpr int PIN_OUT_1 = 4; // Transmitting preset 1
constexpr int PIN_OUT_2 = 5; // Transmitting preset 2
constexpr int PIN_OUT_3 = 12; // Transmitting preset 3
constexpr int PIN_OUT_4 = 13; // Transmitting preset 4
constexpr int CONFIG_PIN = 10; // Reset Pin

constexpr int SENDER_PINS[] = { PIN_OUT_1 };

using namespace std;
using namespace ESoft::RESTRemote;


Blinker blinker;
CodeRegistry registry;
IRInterface irInterface(registry, PIN_IN, SENDER_PINS, blinker);
CodeServer server(registry, irInterface);

void lostWiFi(const WiFiEventStationModeDisconnected& evt) {
    Serial.println("Lost Wifi");
    // reset and try again, or maybe put it to deep sleep
    ESP.reset();
    delay(1000);
}

void setup() {
    blinker.start(Blinker::Type::SLOW);

    Serial.begin(115200);

    WiFiManager wifiManager;

    pinMode(CONFIG_PIN, INPUT_PULLUP);
    if (digitalRead(CONFIG_PIN) == LOW) {
        Serial.print("WiFI reset pin detected. Resetting...");
        wifiManager.resetSettings();
    }

    wifiManager.autoConnect(MODULE_NAME);

    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
    }

    WiFi.onStationModeDisconnected(&lostWiFi);

    delay(5000);
    Serial.println("");
    Serial.print("Starting ");
    Serial.println(MODULE_NAME);

    server.init();
    irInterface.init();

    blinker.off();


}

void loop() {
    server.handleClient();
    irInterface.processReceive();
    delay(IRInterface::TICK_DELAY);
}
