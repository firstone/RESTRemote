#pragma once

#include <memory>
#include <vector>

#include <IRrecv.h>
#include <IRsend.h>

#include "Blinker.hh"
#include "CodeRegistry.hh"

namespace ESoft {

namespace RESTRemote {

class IRInterface {
public:
    static constexpr unsigned int CAPTURE_BUF_SIZE = 150;
    static constexpr int START_SEND_BUF_SIZE = 8;
    static constexpr int TICK_DELAY = 500; // ms
    static constexpr int LEARN_TIMEOUT = 30; // seconds
    static constexpr int LEARN_TIMEOUT_TICK_COUNT
        = LEARN_TIMEOUT * 1000 / TICK_DELAY;
    static constexpr int  KNOWN_DATA_LEN = sizeof(uint64_t) / sizeof(uint8_t);
    static constexpr unsigned int RAW_HZ = 38000;

    IRInterface(CodeRegistry &arg, int receiverPin, const int senderPins[],
                Blinker &blinker)
            : registry(arg), receiver(receiverPin, CAPTURE_BUF_SIZE),
                blinker(blinker), isReceiving(false),
                sendBuffer(START_SEND_BUF_SIZE) {
        for (int i = 0; i < sizeof(senderPins) / sizeof(senderPins[0]); i++) {
            senders.emplace_back(std::make_shared<IRsend>(senderPins[i]));
        }
    }

    bool init() {
        if (!registry.init()) {
            return false;
        }
        for (auto &it : senders) {
            it->begin();
        }
    }

    void learn(const String &codeName) {
        Serial.print("Learning code ");
        Serial.println(codeName);
        currentCodeName = codeName;
        currentTickCount = 0;
        isReceiving = true;
        blinker.start(Blinker::Type::FAST);
        receiver.enableIRIn();
    }

    void stopLearn() {
        isReceiving = false;
        blinker.off();
        receiver.disableIRIn();
    }

    bool sendCode(int senderIndex, const String &codeName) {
        blinker.start(Blinker::Type::FASTEST);
        uint16_t type;
        uint16_t bits;
        uint8_t len;
        if (!registry.loadCode(codeName, type, bits, len, sendBuffer)) {
            Serial.println("Failed to load IR code");
            blinker.off();
            return false;
        }

        switch (type) {
            case PANASONIC:
                senders[senderIndex]->sendPanasonic64(
                    *reinterpret_cast<uint64_t *>(sendBuffer.data()), bits);
                break;

            case SANYO:
                senders[senderIndex]->sendSanyoLC7461(
                    *reinterpret_cast<uint64_t *>(sendBuffer.data()), bits);
                break;

            case PRONTO:
                senders[senderIndex]->sendPronto(
                    reinterpret_cast<uint16_t *>(sendBuffer.data()), len / 2);
                break;

            case GLOBALCACHE:
                senders[senderIndex]->sendGC(
                    reinterpret_cast<uint16_t *>(sendBuffer.data()), len / 2);
                break;

            case RAW:
                senders[senderIndex]->sendRaw(
                    reinterpret_cast<uint16_t *>(sendBuffer.data()), len / 2,
                    RAW_HZ);
                break;

            default:
                senders[senderIndex]->send(type,
                    *reinterpret_cast<uint64_t *>(sendBuffer.data()), bits);
        }
        blinker.off();
    }

    void processReceive() {
        if (!isReceiving) {
            return;
        }

        if (currentTickCount++ >= LEARN_TIMEOUT_TICK_COUNT) {
            Serial.println("Learn timeout reached. Cancelling...");
            stopLearn();
            return;
        }

        Serial.println("Waiting for IR signal");
        if (receiver.decode(&results)) {
            if (results.overflow) {
                Serial.println("IR Signal overflow. Increase receiver buffer size");
                return;
            }
            isReceiving = false;
            Serial.println("Signal received. Storing...");
            receiver.disableIRIn();
            memcpy(sendBuffer.data(), reinterpret_cast<uint16_t *>(&results.value),
                KNOWN_DATA_LEN);
            if (!registry.saveCode(currentCodeName, results.decode_type, results.bits,
                    KNOWN_DATA_LEN, sendBuffer)) {
                Serial.println("Failed to save IR code");
                return;
            }
            blinker.off();
        }
    }

    int getSendersCount() { return senders.size(); }

private:
    CodeRegistry &registry;
    IRrecv receiver;
    Blinker &blinker;
    bool isReceiving;
    decode_results results;
    std::vector<uint8_t> sendBuffer;
    int currentTickCount;
    std::vector<std::shared_ptr<IRsend>> senders;
    String currentCodeName;

};

}

}
