### Configure devices

For each device you have, click Add for appropriate device type and configure devices parameters.
Usually only *host name* is needed. *description* is optional but will help in ISY Admin Console.

After changing parameters, run *Re-Discover* command in AVRemote controller or restart AVRemote.


### Chromecast

Chromecast are auto detected if Chomecast Support Enabled is set to *true*. After setting it to *true*, run *Re-Discover* command in AVRemote controller. Chromecast devices require playlists configuration. Parameters needed are:
* *name* - appears in drop down list in Admin console
* *URL*
* *type* - which is a mime type of the URL. Could be *video/mp4* or *audio/mp3* or any other valid mime type.

### LG TV (Web OS devices)

If TV doesn't turn on using *Power On* command, set **Broadcast Address** parameter to you match your subnet. For example, if you TV's IP address is *192.168.0.xxx*, set **Broadcast Address** to *192.168.0.255*