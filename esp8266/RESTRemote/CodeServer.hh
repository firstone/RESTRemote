#pragma once

#include <ArduinoJson.h>
#include <ESP8266WebServer.h>

#include "CodeRegistry.hh"
#include "IRInterface.hh"
#include "URLParamRequestHandler.hh"

namespace ESoft {

namespace RESTRemote {

class CodeServer : public ESP8266WebServer {
public:
    static constexpr int PORT = 80;
    static constexpr int OUTPUT_BUF_SIZE = 1024;
    static constexpr size_t DEFAULT_JSON_BUF_SIZE = JSON_OBJECT_SIZE(2);

    CodeServer(CodeRegistry &arg, IRInterface &irInt)
            : ESP8266WebServer(PORT), registry(arg), irInterface(irInt),
                outputBuffer(OUTPUT_BUF_SIZE), jsonBuffer(DEFAULT_JSON_BUF_SIZE) {
        on("/", HTTP_GET, std::bind(&CodeServer::mainPage, this));
        on("/ping", HTTP_GET, std::bind(&CodeServer::emptyResponse, this));
        on("/list", HTTP_GET, std::bind(&CodeServer::list, this));
        on("/clear", HTTP_POST, std::bind(&CodeServer::clear, this));
        on("/cancel_learn", HTTP_POST, std::bind(&CodeServer::cancelLearn, this));
        _addRequestHandler(new URLParamRequestHandler(
            std::bind(&CodeServer::learn, this),
            "/learn/${codeName}", HTTP_POST));
        _addRequestHandler(new URLParamRequestHandler(
            std::bind(&CodeServer::remove, this),
            "/remove/${codeName}", HTTP_POST));
        _addRequestHandler(new URLParamRequestHandler(
            std::bind(&CodeServer::sendCode, this),
            "/send/${led}/${codeName}", HTTP_POST));
    }

    bool init() {
        if (!registry.init()) {
            return false;
        }
        Serial.println("Starting HTTP server");
        begin();
    }

    void mainPage() {
        setContentLength(CONTENT_LENGTH_UNKNOWN);
        send(200, "text/html; charset=utf-8", "");
        sendContent("<!DOCTYPE html>");
        sendContent("<html>");
        sendContent("<head>");
        sendContent("<title>REST Remote IR Module</title>");
        sendContent("<style>");
        sendFile("/main.css");
        sendContent("</style>");
        sendContent("</head>");
        sendContent("<body>");
        sendContent("<span class=\"controls\">");
        sendContent("   <label>IR emitter</label>");
        sendContent("   <select id=\"irEmitter\">");
        for (int i = 0; i < irInterface.getSendersCount(); i++) {
            sendContent(String("       <option>") + i + "</option>");
        }
        sendContent("   </select>");
        sendContent("</span>");
        sendContent("<table class=\"commandTable\">");
        auto codeList = registry.getCodeList();
        for (auto &it : registry.getCodeList()) {
            auto codeName = it.substring(sizeof(CodeRegistry::CODES_DIR));
            sendContent("   <tr>");
            sendContent(String("        <td>") + codeName + "</td>");
            sendContent(String("        <td><button class=\"send\" onclick=\"sendCode('") + codeName + "')\">Send</button></td>");
            sendContent(String("        <td><button class=\"delete\" onclick=\"confirmDeleteCode('") + codeName + "')\">Delete</button></td>");
            sendContent("   </tr>");
        }
        sendContent("</table>");
        sendFile("/main.html");
        sendContent("</body>");
        sendContent("<script>");
        sendFile("/main.js");
        sendContent("</script>");
        sendContent("</html>");
    }

    void emptyResponse() {
        sendResult(true, "");
    }

    void list() {
        Serial.println("Listing codes");

        auto codeList = registry.getCodeList();
        const size_t bufferSize = JSON_ARRAY_SIZE(codeList.size())
            + JSON_OBJECT_SIZE(3);

        DynamicJsonBuffer jsonBuffer(bufferSize);

        auto &root = jsonBuffer.createObject();
        auto &list = root.createNestedArray("codes");
        for (auto &it : codeList) {
            list.add(it.substring(sizeof(CodeRegistry::CODES_DIR)));
        }

        sendResult(true, "", root);
    }

    void learn() {
        irInterface.learn(arg(0));
        sendResult(true, String("You have ") + IRInterface::LEARN_TIMEOUT
            + " seconds to send IR signal");
    }

    void cancelLearn() {
        irInterface.stopLearn();
        sendResult(true, "");
    }

    void remove() {
        Serial.println("Deleting code");
        Serial.println(arg(0));
        registry.deleteCode(arg(0));
        sendResult(true, "");
    }

    void clear() {
        Serial.println("Clearing codes");
        registry.clearCodes();
        sendResult(true, "");
    }

    void resetParameters(int paramCount) {
        _currentArgCount = paramCount;
        _currentArgs = new RequestArgument[_currentArgCount];
        currentParamIndex = 0;
    }

    void setParameter(const String &key, const String &value) {
        auto &param = _currentArgs[currentParamIndex++];
        param.key = key;
        param.value = value;
    }

    void sendCode() {
        if (!irInterface.sendCode(arg(0).toInt(), arg(1))) {
            sendResult(false, "Failed to load IR code");
        } else {
            sendResult(true, "");
        }
    }

    void sendResult(bool isSuccess, const String &msg) {
        sendResult(isSuccess, msg, jsonBuffer.createObject());
    }

    void sendResult(bool isSuccess, const String &msg, JsonObject &root) {
        int retCode;
        if (isSuccess) {
            retCode = 200;
            root["result"] = "success";
            if (msg.length() > 0) {
                root["message"] = msg;
            }
        } else {
            retCode = 404;
            root["result"] = "failure";
            root["error"] = msg;
        }

        auto len = root.measureLength();
        if (outputBuffer.size() <= len) {
            outputBuffer.resize(len + 1);
        }
        root.printTo(outputBuffer.data(), outputBuffer.size());

        setContentLength(CONTENT_LENGTH_UNKNOWN);
        send(retCode, "application/json", "");
        sendHeader("Access-Control-Allow-Origin", "*");
        sendContent(outputBuffer.data());
    }

    bool sendFile(const String &fileName) {
        auto file = SPIFFS.open(fileName, "r");
        if (!file) {
            Serial.print("Error readig file ");
            Serial.println(fileName);
            return false;
        }

        while (true) {
            auto len = file.read(reinterpret_cast<uint8_t *>(outputBuffer.data()),
                outputBuffer.size() - 1);
            if (len <= 0) {
                break;
            }
            outputBuffer[len] = '\0';
            sendContent(outputBuffer.data());
        }
        file.close();
    }
private:
    CodeRegistry &registry;
    IRInterface &irInterface;
    std::vector<char> outputBuffer;
    DynamicJsonBuffer jsonBuffer;
    int currentParamIndex;
};

}

}
