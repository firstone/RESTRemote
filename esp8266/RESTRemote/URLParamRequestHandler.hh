#pragma once

#include <ESP8266WebServer.h>

#include <vector>
#include <memory>

#include <FS.h>

namespace ESoft {

namespace RESTRemote {

class URLParamRequestHandler : public RequestHandler {
public:
    static constexpr char URI_SEPARATOR[] = "/";
    static constexpr char VAR_BEGIN[] = "${";
    static constexpr char VAR_END[] = "}";

    URLParamRequestHandler(ESP8266WebServer::THandlerFunction func,
            const String &uri, HTTPMethod method)
        : func(func), method(method), paramCount(0) {
        uriBuffer.resize(uri.length() * 2);
        strcpy(uriBuffer.data(), uri.c_str());

        auto ptr = strtok(uriBuffer.data(), URI_SEPARATOR);
        while (ptr != NULL) {
            auto begin = strstr(ptr, VAR_BEGIN);
            if (begin != NULL) {
                auto end = strstr(begin, VAR_END);
                if (end != NULL) {
                    *end = '\0';
                }
                elements.emplace_back(std::make_shared<URIParameter>(
                    begin + sizeof(VAR_BEGIN) - 1));
                paramCount++;
            } else {
                elements.emplace_back(std::make_shared<URIElement>(ptr));
            }
            ptr = strtok(NULL, URI_SEPARATOR);
        }

    }

    bool canHandle(HTTPMethod requestMethod, String requestUri) override  {
        if (method != HTTP_ANY && method != requestMethod) {
           return false;
        }

        if (uriBuffer.size() <= requestUri.length()) {
            uriBuffer.resize(uriBuffer.size() * 2);
        }
        strcpy(uriBuffer.data(), requestUri.c_str());

        auto ptr = strtok(uriBuffer.data(), URI_SEPARATOR);
        int index = 0;
        while (ptr != NULL) {
            if (index >= elements.size()) {
                return false;
            }
            if (!elements[index++]->canUse(ptr)) {
                return false;
            }
            ptr = strtok(NULL, URI_SEPARATOR);
        }

        if (index < elements.size()) {
            return false;
        }

        return true;
    }

    bool canUpload(String uri) override { return false; }

    bool handle(ESP8266WebServer &server, HTTPMethod requestMethod,
        String requestUri) override;

protected:
    class URIElement;
    class URIParameter;

    ESP8266WebServer::THandlerFunction func;
    HTTPMethod method;
    int paramCount;
    std::vector<std::shared_ptr<URIElement>> elements;
    std::vector<char> uriBuffer;

    class URIElement {
    public:
        URIElement(const String &key) : key(key) {}

        virtual bool canUse(const String &arg) { return arg == key; }
        virtual void process(ESP8266WebServer &) {}

    protected:
        String key;
    };

    class URIParameter : public URIElement {
    public:
        URIParameter(const String &key) : URIElement(key) {}

        bool canUse(const String &arg) override {
            lastValue = arg;
            return true;
        }

        void process(ESP8266WebServer &server) override;

      private:
        String lastValue;
    };
};

}

}
