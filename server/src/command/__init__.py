import config
import handlers
from bitmask import *
from util import Command, CommandError, UsageError, _send_chat_response, _unknown_cmd, _cmd_error

# register commands
COMMANDS = [
    # tier 0 (player) commands
    # bitmask 0b1111111
    Command('help', handlers.cmd_help, arg_str='[cmd_name]', max_args=1, description='Display a help menu.', bitmask=BITMASK_ALL), #min_admin_level=0),
    Command('statreset', handlers.cmd_statreset, arg_str='', max_args=0, description='Reset all stats.', bitmask=BITMASK_ALL), #min_admin_level=0),
    Command('setspawn', handlers.cmd_setspawn, arg_str='<location_num>', max_args=1, description='Set spawn point to location (1 to %s).' % len(config.PLAYER_SPAWN), bitmask=BITMASK_ALL), #min_admin_level=0),

    # Group 1 commands (self-effecting 1)
    Command('item', handlers.cmd_item, arg_str='<item_id>', max_args=1, description='Obtain an item of id (1 to 72).', bitmask=BITMASK_GROUP_1), #min_admin_level=190),
    Command('godmode', handlers.cmd_godmode, arg_str='', max_args=0, description='Toggle godmode.', bitmask=BITMASK_GROUP_1), #min_admin_level=190),

    # Group 2 commands (self-effecting 2)
    Command('level', handlers.cmd_level, arg_str='<level>', max_args=1, description='Set level (will reset stats).', bitmask=BITMASK_GROUP_2), #min_admin_level=200),

    # Group 3 commands (local-effecting)
    Command('spawn', handlers.cmd_spawn, arg_str='<mob_id> [amount]', max_args=2, description='Spawn mob(s) of given id (0 to 18).', bitmask=BITMASK_GROUP_3), #min_admin_level=210),
    Command('spawnall', handlers.cmd_spawnall, arg_str='[amount]', max_args=1, description='Spawn all mobs.', bitmask=BITMASK_GROUP_3), #min_admin_level=210),
    Command('hurt', handlers.cmd_hurt, arg_str='', max_args=0, description='Set nearby mobs to 1 hp.', bitmask=BITMASK_GROUP_3), #min_admin_level=210),
    Command('kill', handlers.cmd_kill, arg_str='', max_args=0, description='Kill nearby mobs.', bitmask=BITMASK_GROUP_3), #min_admin_level=210),

    # Group 4 commands (world-effecting)
    Command('hurtall', handlers.cmd_hurtall, arg_str='', max_args=0, description='Set all mobs to 1 hp.', bitmask=BITMASK_GROUP_4), #min_admin_level=220),
    Command('killall', handlers.cmd_killall, arg_str='', max_args=0, description='Kill all mobs.', bitmask=BITMASK_GROUP_4), #min_admin_level=220),

    # Group 5 commands (mod)
    Command('kick', handlers.cmd_kick, arg_str='<name>', max_args=1, description='Kick a player.', bitmask=BITMASK_GROUP_5), #min_admin_level=230),
    Command('ban', handlers.cmd_ban_unban, arg_str='<name>', max_args=1, description='Ban a player.', bitmask=BITMASK_GROUP_5), #min_admin_level=240),
    Command('unban', handlers.cmd_ban_unban, arg_str='<name>', max_args=1, description='Unban a player.', bitmask=BITMASK_GROUP_5), #min_admin_level=240),

    # Admin commands
    Command('setadmin', handlers.cmd_setadmin, arg_str='<name> <level>', max_args=2, description='Change player admin status (0 to 250).', bitmask=BITMASK_ADMIN), #min_admin_level=250),
    Command('crashworld', handlers.cmd_crashworld, arg_str='', max_args=0, description='Crash world thread.', bitmask=BITMASK_ADMIN), #min_admin_level=250),
]
CMD_DICT = { cmd.name:cmd for cmd in COMMANDS }

def bitmask_is_admin(bitmask):
    return bool(bitmask & BITMASK_ADMIN)

def process_command(client, command_string):
    try:
        cleaned = command_string.strip()[1:]
        tokens = cleaned.split(' ')
        client.logger.debug('command "!%s"' % ' '.join(tokens))

        if len(tokens) < 1 or tokens[0] not in CMD_DICT:
            _unknown_cmd(client)
        else:
            CMD_DICT[tokens[0]].handle(client, tokens)

    except Exception as e:
        _cmd_error(client)
        client.logger.error('command processing exception "%s": %s' % (cleaned, e))
        import traceback
        traceback.print_exc()
