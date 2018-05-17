#include "URLParamRequestHandler.hh"

#include "CodeServer.hh"

namespace ESoft {

namespace RESTRemote {

constexpr char URLParamRequestHandler::URI_SEPARATOR[];
constexpr char URLParamRequestHandler::VAR_BEGIN[];
constexpr char URLParamRequestHandler::VAR_END[];

bool URLParamRequestHandler::handle(ESP8266WebServer &serverArg,
    HTTPMethod requestMethod, String requestUri) {
    auto &server = static_cast<CodeServer &>(serverArg);
    server.resetParameters(paramCount);
    for (auto &it : elements) {
        it->process(server);
    }
    func();
    return true;
}

void URLParamRequestHandler::URIParameter::process(ESP8266WebServer &server) {
    static_cast<CodeServer &>(server).setParameter(key, lastValue);
}

}

}
