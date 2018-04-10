# Admin Commands
Invoke admin commands by typing `!` followed by the command name in the chat box.

Available commands:

Name | Usage | Example | Description | Admin Required
---|---|---|---|---
`help`|`!help [cmd_name]`|`!help item`| Show list of commands or usage of a given command.|No
`item`|`!item <item_id>`|`!item 23`| Obtain an item of a given item_id. Item is added to inventory on disconnect.|No
`level`|`!level <level>`|`!level 10`|Set level to given value. Will reset stats and disconnect player.|No
`godmode`|`!godmode`|`!godmode`| Toggle god mode.|No
`setspawn`|`!setspawn <location_num>`|`!setspawn 1`|Set spawn point to given location (1 to 8). Will disconnect player.|No
`spawn`|`!spawn <mob_id> [amount]`|`!spawn 0 10`| Spawn a mob of a given mob_id. The amount parameter is optional.|Yes
`spawnall`|`spawnall [amount]`|`!spawnall`| Spawn all mobs in the game.|Yes
`hurt`|`!hurt`|`!hurt`| Set all nearby mobs to 1 HP.|Yes
`hurtall`|`!hurtall`|`!hurtall`| Set all mobs in the world to 1 HP.|Yes
`kill`|`!kill`|`!kill`| Kill all nearby mobs.|Yes
`killall`|`!killall`|`!killall`| Kill all mobs in the world.|Yes
`kick`|`!kick <name>`|`!kick user1`| Kick a player.|Yes
`ban`|`!ban <name>`|`!ban user1`| Ban a player.|Yes
`unban`|`!unban <name>`|`!unban user1`| Unban a player.|Yes
`setadmin`|`!setadmin <name> <true false>`|`!setadmin user1 true`| Grant or revoke admin access. This will disconnect the target user.|Yes
