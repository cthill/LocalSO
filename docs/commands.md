# In Game Commands
Invoke commands by typing `!` followed by the command name in the chat box. Commands are tiered based on the player's admin_level.

Available commands:

Name | Usage | Example | Description | Admin Level Required
---|---|---|---|---
`help`|`!help [cmd_name]`|`!help item`| Show list of commands or usage of a given command.|0
`setspawn`|`!setspawn <location_num>`|`!setspawn 1`|Set spawn point to given location (1 to 8). Will disconnect player.|0
`statreset`|`!statreset`|`!statreset`|Reset all stats. Will disconnect player.|0
`item`|`!item <item_id>`|`!item 23`| Obtain an item of a given item_id. Item is added to inventory on disconnect.|190
`godmode`|`!godmode`|`!godmode`| Toggle god mode.|190
`level`|`!level <level>`|`!level 10`|Set level to given value. Will reset stats and disconnect player.|200
`spawn`|`!spawn <mob_id> [amount]`|`!spawn 0 10`| Spawn a mob of a given mob_id. The amount parameter is optional.|210
`spawnall`|`spawnall [amount]`|`!spawnall`| Spawn all mobs in the game.|210
`hurt`|`!hurt`|`!hurt`| Set all nearby mobs to 1 HP.|210
`kill`|`!kill`|`!kill`| Kill all nearby mobs.|210
`hurtall`|`!hurtall`|`!hurtall`| Set all mobs in the world to 1 HP.|220
`killall`|`!killall`|`!killall`| Kill all mobs in the world.|220
`kick`|`!kick <name>`|`!kick user1`| Kick a player.|230
`ban`|`!ban <name>`|`!ban user1`| Ban a player.|240
`unban`|`!unban <name>`|`!unban user1`| Unban a player.|240
`setadmin`|`!setadmin <name> <admin_level>`|`!setadmin user1 190`| Grant or revoke admin access. This will disconnect the target user.|250
