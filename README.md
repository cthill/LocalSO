# LocalSO
A cross platform Stick Online server emulator written in Python

#### What Is Stick Online?
Stick Online was a small multiplayer online role playing game from the late 2000's. The servers were shut down many years ago. The game was built using GameMaker and was popular among member of the GameMaker Community. More info and the original client can be found at [stick-online.com](http://stick-online.com).

I am in no way affiliated with Stick Online or Team Stick Online.

#### What Is LocalSO?
LocalSO is a reimplementation of the original Stick Online game server. It is compatible with the original unmodified Stick Online client.

#### Requirements
 - Python 2.7

#### Starting The Server
Run `main.py` from the command line:
```
$ python main.py
```

#### Connecting To The Server
To connect to the game server with an unmodified client, you must add two entries to your hosts file. Add the following two lines to `C:\Windows\System32\drivers\etc\hosts`
```
127.0.0.1	stickonline.redirectme.net
127.0.0.1	www.stick-online.com
```
Start the client and it should connect to the server emulator.

Note: you will not be able to connect to the official stick-online website without first undoing these changes.


## Features
Status of game features
#### Working
 - everything that is handled client-side:
  - shops
  - gold and item drops
  - leveling
  - HP/MP
  - death
  - spawn points
  - rudimentary anticheat
 - attacking and killing mobs
 - chat
 - PVP
 - admin features
  - custom admin commands (prefixed by !)
  - blue colored admin chat
  - mob spawning with scroll wheel and F12
    - the client checks your player name against a list of admin names before trying to spawn a mob. This list is hard coded.
    - because of this, I have implemented text-based admin commands.


#### Partially Working
 - mob AI
  - mob movement is not like the original game
  - mobs show attack animation but deal no damage
 - clans
  - the original game never fully supported clans, but will display a clan name under the player name. It also prevents clanmate pvp. I may add clan support through a text-based chat interface.

#### Unimplemented
 - login and registration (the login screen accepts any username and password)
 - account saving
 - admin features
  - bans
  - kicks
  - donor status

#### Misc
If you are an admin:
 - use alt (instead of enter) to have your text show up blue when chatting

#### mob to implement:
 - atk_stat
 - knockback
 - spawn_y_offset_neg
