#pragma once

#include <vector>

#include <FS.h>

namespace ESoft {

namespace RESTRemote {

class CodeRegistry {
public:
    static constexpr char CODES_DIR[] = "/codes";

    CodeRegistry() : initDone(false) {}

    bool init() {
        if (!initDone) {
            if (!SPIFFS.begin()) {
                Serial.println("Failed to mount file system");
                return false;
            }
        }

        return true;
    }

    std::vector<String> getCodeList() const {
        std::vector<String> result;

        auto dir =  SPIFFS.openDir(CODES_DIR);
        while (dir.next()) {
            result.push_back(dir.fileName());
        }

        return result;
    }

    bool saveCode(const String &codeName, uint16_t type, uint16_t bits,
        uint8_t len, const std::vector<uint8_t> &buf) {
        auto file = SPIFFS.open(String(CODES_DIR) + "/" + codeName, "w");
        if (!file) {
            Serial.println("Error creating code file");
            return false;
        }

        file.write(reinterpret_cast<uint8_t *>(&type), 2);
        file.write(reinterpret_cast<uint8_t *>(&bits), 2);
        file.write(len);
        file.write(buf.data(), len);
        file.close();

        return true;
    }

    bool loadCode(const String &codeName, uint16_t &type, uint16_t &bits,
        uint8_t &len, std::vector<uint8_t> &buf) {
        auto file = SPIFFS.open(String(CODES_DIR) + "/" + codeName, "r");
        if (!file) {
            Serial.println("Error reading code file");
            return false;
        }

        file.read(reinterpret_cast<uint8_t *>(&type), 2);
        file.read(reinterpret_cast<uint8_t *>(&bits), 2);
        file.read(&len, 1);
        if (buf.size() < len) {
            buf.resize(len);
        }
        file.read(buf.data(), len);
        file.close();

        return true;
    }

    bool deleteCode(const String &codeName) {
        return SPIFFS.remove(String(CODES_DIR) + "/" + codeName);
    }

    bool clearCodes() {
        auto dir =  SPIFFS.openDir(CODES_DIR);
        while (dir.next()) {
            if (SPIFFS.remove(dir.fileName()) != 0) {
                return false;
            }
        }

        return true;
    }

private:
    bool initDone;

};

}

}
