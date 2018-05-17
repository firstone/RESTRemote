#pragma once

#include <Ticker.h>

namespace ESoft {

namespace RESTRemote {

class Blinker {
public:
    enum class Type { FASTEST = 2, FAST = 5, SLOW = 7 };

    Blinker() {
        pinMode(BUILTIN_LED, OUTPUT);
    }

    void off() {
        ticker.detach();
        digitalWrite(BUILTIN_LED, HIGH);
    }

    void start(Type type) {
        ticker.attach(static_cast<double>(static_cast<int>(type)) / 10,
            &Blinker::blink);
        digitalWrite(BUILTIN_LED, LOW);
    }

    static void blink() {
        digitalWrite(BUILTIN_LED, !digitalRead(BUILTIN_LED));
    }

private:
    Ticker ticker;

};

}

}
