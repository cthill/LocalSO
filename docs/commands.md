# Admin Commands
Invoke admin commands by typing `!` followed by the command name in the chat box.

Available commands:

Name | Usage | Example | Description
---|---|---|---
`help`|`!help`|`!help`| Show list of commands.
`spawn`|`!spawn <mob_id> [amount]`|`!spawn 0 10`| Spawn a mob of a given mob_id. The amount parameter is optional.
`spawnall`|`spawnall [amount]`|`!spawnall`| Spawn all mobs in the game.
`hurt`|`!hurt`|`!hurt`| Set all nearby mobs to 1 HP.
`hurtall`|`!hurtall`|`!hurtall`| Set all mobs in the world to 1 HP.
`kill`|`!kill`|`!kill`| Kill all nearby mobs.
`killall`|`!killall`|`!killall`| Kill all mobs in the world.
`godmode`|`!godmode`|`!godmode`| Toggle god mode.
`kick`|`!kick <name>`|`!kick user1`| Kick a player.
`ban`|`!ban <name>`|`!ban user1`| Ban a player.
`unban`|`!unban <name>`|`!unban user1`| Unban a player.
`setadmin`|`!setadmin <name> <true false>`|`!setadmin user1 true`| Grant or revoke admin access. This will disconnect the target user.
`item`|`!item <item_id>`|`!item 23`| Obtain an item of a give item_id. This will disconnect the admin.
