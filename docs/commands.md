# In Game Commands
Invoke commands by typing `!` followed by the command name in the chat box. Access to commands is granted by using the player's admin_level as a bitmask.

### Available commands:

Name | Usage | Example | Description | Command Group
---|---|---|---|---
`help`|`!help [cmd_name]`|`!help item`| Show list of commands or usage of a given command.| Unrestricted
`setspawn`|`!setspawn <location_num>`|`!setspawn 1`|Set spawn point to given location (1 to 8). Will disconnect player.|All
`statreset`|`!statreset`|`!statreset`|Reset all stats. Will disconnect player.|All
`item`|`!item <item_id>`|`!item 23`| Obtain an item of a given item_id. Item is added to inventory on disconnect.|Group 1
`godmode`|`!godmode`|`!godmode`| Toggle god mode.|Group 1
`level`|`!level <level>`|`!level 10`|Set level to given value. Will reset stats and disconnect player.|Group 2
`spawn`|`!spawn <mob_id> [amount]`|`!spawn 0 10`| Spawn a mob of a given mob_id. The amount parameter is optional.|Group 3
`spawnall`|`spawnall [amount]`|`!spawnall`| Spawn all mobs in the game.|Group 3
`hurt`|`!hurt`|`!hurt`| Set all nearby mobs to 1 HP.|Group 3
`kill`|`!kill`|`!kill`| Kill all nearby mobs.|Group 3
`hurtall`|`!hurtall`|`!hurtall`| Set all mobs in the world to 1 HP.|Group 4
`killall`|`!killall`|`!killall`| Kill all mobs in the world.|Group 4
`kick`|`!kick <name>`|`!kick user1`| Kick a player.|Group 5
`ban`|`!ban <name>`|`!ban user1`| Ban a player.|Group 5
`unban`|`!unban <name>`|`!unban user1`| Unban a player.|Group 5
`setadmin`|`!setadmin <name> <admin_level>`|`!setadmin user1 190`| Grant or revoke admin access. This will disconnect the target user.|Admin

### Groups and Bitmasks

Access to commands is granted using the player's admin_level (class) as a bitmask.
The admin_level is a byte with 2 unused bits, thus allowing for 6 commands groups.

```text
bit 0 = unused
bit 1 = group 1 commands
bit 2 = unused
bit 3 = group 2 commands
bit 4 = group 3 commands
bit 5 = group 4 commands
bit 6 = group 5 commands
bit 7 = admin commands
```

```python
BITMASK_ALL     = 0b00000000
BITMASK_NONE    = 0b00000101
BITMASK_GROUP_1 = 0b00000010
BITMASK_GROUP_2 = 0b00001000
BITMASK_GROUP_3 = 0b00010000
BITMASK_GROUP_4 = 0b00100000
BITMASK_GROUP_5 = 0b01000000
BITMASK_ADMIN   = 0b10000000
```

Admin Level | Unrestricted Commands | Group 1 | Group 2 | Group 3 | Group 4 | Group 5 | Admin Commands
---|---|---|---|---|---|---
0|✔️|-|-|-|-|-|-
2|✔️|✔️|-|-|-|-|-
8|✔️|-|✔️|-|-|-|-
10|✔️|✔️|✔️|-|-|-|-
16|✔️|-|-|✔️|-|-|-
18|✔️|✔️|-|✔️|-|-|-
24|✔️|-|✔️|✔️|-|-|-
26|✔️|✔️|✔️|✔️|-|-|-
32|✔️|-|-|-|✔️|-|-
34|✔️|✔️|-|-|✔️|-|-
40|✔️|-|✔️|-|✔️|-|-
42|✔️|✔️|✔️|-|✔️|-|-
48|✔️|-|-|✔️|✔️|-|-
50|✔️|✔️|-|✔️|✔️|-|-
56|✔️|-|✔️|✔️|✔️|-|-
58|✔️|✔️|✔️|✔️|✔️|-|-
64|✔️|-|-|-|-|✔️|-
66|✔️|✔️|-|-|-|✔️|-
72|✔️|-|✔️|-|-|✔️|-
74|✔️|✔️|✔️|-|-|✔️|-
80|✔️|-|-|✔️|-|✔️|-
82|✔️|✔️|-|✔️|-|✔️|-
88|✔️|-|✔️|✔️|-|✔️|-
90|✔️|✔️|✔️|✔️|-|✔️|-
96|✔️|-|-|-|✔️|✔️|-
98|✔️|✔️|-|-|✔️|✔️|-
104|✔️|-|✔️|-|✔️|✔️|-
106|✔️|✔️|✔️|-|✔️|✔️|-
112|✔️|-|-|✔️|✔️|✔️|-
114|✔️|✔️|-|✔️|✔️|✔️|-
120|✔️|-|✔️|✔️|✔️|✔️|-
122|✔️|✔️|✔️|✔️|✔️|✔️|-
250|✔️|✔️|✔️|✔️|✔️|✔️|✔️
