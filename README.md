# LocalSO
A cross platform Stick Online server emulator written in Python

#### What Is LocalSO?
LocalSO is a reimplementation of the original Stick Online game server. It is compatible with the original unmodified Stick Online client version 0.0227.

#### What Is Stick Online?
Stick Online was a small multiplayer online role playing game from the late 2000's. The servers were shut down many years ago. The game was built using GameMaker and was popular among member of the GameMaker Community. More info and the original client can be found at [stick-online.com](http://stick-online.com).

I am in no way affiliated with Stick Online or Team Stick Online.

![In game screenshot](media/screenshot_2.PNG)

#### Server Requirements
 - Python 2.7

#### Starting The Server
If on Windows, run `start_server.cmd` from explorer or the command line.

Otherwise, run `src/main.py` from the command line:
```
$ python src/main.py
```

#### Connecting To The Server
Before connecting, obtain a copy of the Stick Online client version 0.0227.

To connect with an unmodified client, you must add two entries to your hosts file. Add the following two entries to `C:\Windows\System32\drivers\etc\hosts`
```
127.0.0.1	stickonline.redirectme.net
127.0.0.1	www.stick-online.com
```
Start the client and it should connect to the server.

Note: you will not be able to connect to the official www.stick-online.com website without first undoing these changes.


## Features
Status of game features
#### Working
 - login and registration
 - account saving
 - everything that is handled client-side:
   - shops
   - gold and item drops
   - leveling
   - HP/MP
   - death
   - spawn points
   - rudimentary anticheat
 - mobs
   - mob spawning
   - mob movement
   - mobs attacks
   - attacking mobs
 - chat
 - PVP
 - admin features
   - admin chat announcements (use alt instead of enter to send a chat announcement)
   - custom admin commands
     - spawning and killing mobs
     - kicks
     - bans
     - grant admin access


#### Partially Working
 - clans
   - the original game never fully supported clans, but will display a clan name under the player name. It also prevents clanmate pvp. I may add clan support through a text-based chat interface.

#### Unimplemented
 - -
