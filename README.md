# RESTRemote

## Summary

Simple REST service that allows multiple devices control via similar interface. It allows easy additional of other device drivers. It current supports following:

* LG Web OS TV (via WebSockets)
* Tivo (via Tivo IP interface)
* nVidia Shield (and probably other Android devices, via adb debug capability)
* Denon AVR (via Denon IP interface)
* Most IR devices (via ESP8266 board)

## Getting Started

Install python3 and run *install.sh*

Configuration is done via configuration file (*cfg/config.yaml*). If you don't have one, it will be copied from *cfg/config_sample.yaml*.

If you don't have a particular device and don't want to load its driver, you can turn disable it by changing `enabled: false`.

Most devices require only host name defined.

You need to specify both, config file and server config file (*cfg/server_config.yaml*) in the command line. Run `restremote.py --help` for command line options.

Once service is running, you can execute GET calls via browser:

http://localhost:5000/devices

or via command line. For example, curl:

`curl -i -X GET http://localhost:5000/living_tivo/commands`

PUT commands have to be done from command line or tool:

`curl -i -X PUT http://localhost:5000/living_tv/mute/on`

## Basic commands

* */devices* - list configured drivers
* */`<device name>`/commands* - list all available commands with method (**GET**, **PUT**)


## Devices

Devices represent your physical AV devices and use drivers to communicated with them.

Each device has key (short name), which is what you use in REST command, a driver associated with it, as well as configuration parameters. Configuration parameters depend on the driver. See the driver section for configuration details.

## Drivers

### Tivo

There is not much to set up, other than *hostName*. Just look up IP in Tivo and plug it in. If you configure it for static IP in a router, this will never need to be changed. I'm not aware of any way to auto discover it.

### Denon AVR

Denon ARV has auto discovery but I didn't see any of it documented. Just plug in host name or IP into *hostName*. If you configure your router for static IP, this never needs to be changed.

### LG TV (Web OS devices)

Latest models don't need to be configured. They respond on WebSocket hostname of *lgwebostv*. If your device doesn't, plug host name or IP into *hostName*. There is a way to auto discover but I didn't code it since *lgwebostv* works.

The first time you start the service, it needs to be accepted on TV. Start the server, turn TV on and issue any command. You will see the prompt on TV. Clicks 'Accept'. If this fails for any reason, restart the service and try again. This will write client key so config directory needs to be writable. Or else, change *clientKeyFile* to point to writable location.

For some reason listing available launch point or available app doesn't work for me. So you can usually turn on an app, then issue get running app status command, and use that ID to configure launch commands.

### Shield (Android devices)

Android based devices use adb debugging mode. Make sure you have adb installed and configured in *executable*. It either has to be in path or have absolute path specified. Not sure if there's auto discovery so just plug host name or IP into *hostName*.

Android device needs to be configured for network debugging. Usually you need to turn on USB debugging first. Once that's done, option for network debugging is available.

First time you turn it on, make sure your device is on, and it will prompt you to accept connection from your server MAC address. You only need to accept it once.

If you're getting *unauthorized* errors, try `adb kill-server`, followed by `adb connect <host name>:5555`. This should bring authorization dialog again.

If commands don't work, run `adb devices`. If device is listed *offline*, reboot it, run `adb kill-server` and run `adb connect <host name>:5555`. After that, `adb devices` should show status as *online*. It appears that only one MAC address can control Android device at a time. So every time you connect from another MAC, this needs to be repeated to switch to a new MAC.

In order to configure launching apps, issue command to list installed apps (it takes a while). This will return list off apps and launch activities.

### ESP8266

This one requires most work. Schematics can be obtained here:

https://github.com/mdhiggins/ESP8266-HTTP-IR-Blaster

Do not load firmware from that page. Instead load firmware from esp8266 directory. You need Arduino IDE, ESP8266 libraries, ESPWebServer and IRRemoteESP8266.

*DO THIS STEP BEFORE YOU TEACH ANY CODES. IT WILL REMOVE ANY EXISTING CODES*
Follow instruction for ESP8266 to setup file system transfer in Arduino IDE. After that, transfer files. It will pick up files in data directory. You don't need to specify them.

Connect to the blaster via browser and teach IR commands. After that you need to edit *cfg/server_config.yaml* file and assign command names to driver commands. At that point you should be able to send them though RESTRemote server.
