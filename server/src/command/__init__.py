import config
import handlers
from util import Command, CommandError, UsageError, _send_chat_response, _unknown_cmd, _cmd_error

# register commands
COMMANDS = [
    # tier 0 (player) commands
    Command('help', handlers.cmd_help, arg_str='[cmd_name]', max_args=1, description='Display a help menu.', min_admin_level=0),
    Command('statreset', handlers.cmd_statreset, arg_str='', max_args=0, description='Reset all stats.', min_admin_level=0),
    Command('setspawn', handlers.cmd_setspawn, arg_str='<location_num>', max_args=1, description='Set spawn point to location (1 to %s).' % len(config.PLAYER_SPAWN), min_admin_level=0),

    # tier 190 commands
    Command('item', handlers.cmd_item, arg_str='<item_id>', max_args=1, description='Obtain an item of id (1 to 72).', min_admin_level=190),
    Command('godmode', handlers.cmd_godmode, arg_str='', max_args=0, description='Toggle godmode.', min_admin_level=190),

    # tier 200
    Command('level', handlers.cmd_level, arg_str='<level>', max_args=1, description='Set level (will reset stats).', min_admin_level=200),

    # tier 210 commands
    Command('spawn', handlers.cmd_spawn, arg_str='<mob_id> [amount]', max_args=2, description='Spawn mob(s) of given id (0 to 18).', min_admin_level=210),
    Command('spawnall', handlers.cmd_spawnall, arg_str='[amount]', max_args=1, description='Spawn all mobs.', min_admin_level=210),
    Command('hurt', handlers.cmd_hurt, arg_str='', max_args=0, description='Set nearby mobs to 1 hp.', min_admin_level=210),
    Command('kill', handlers.cmd_kill, arg_str='', max_args=0, description='Kill nearby mobs.', min_admin_level=210),

    # tier 220 commands
    Command('hurtall', handlers.cmd_hurtall, arg_str='', max_args=0, description='Set all mobs to 1 hp.', min_admin_level=220),
    Command('killall', handlers.cmd_killall, arg_str='', max_args=0, description='Kill all mobs.', min_admin_level=220),

    # tier 230 commands
    Command('kick', handlers.cmd_kick, arg_str='<name>', max_args=1, description='Kick a player.', min_admin_level=230),

    # tier 240 commands
    Command('ban', handlers.cmd_ban_unban, arg_str='<name>', max_args=1, description='Ban a player.', min_admin_level=240),
    Command('unban', handlers.cmd_ban_unban, arg_str='<name>', max_args=1, description='Unban a player.', min_admin_level=240),

    # tier 250 (gm) commands
    Command('setadmin', handlers.cmd_setadmin, arg_str='<name> <level>', max_args=2, description='Change player admin status (0 to 250).', min_admin_level=250),
    # Command('crashworld', handlers.cmd_crashworld, arg_str='', max_args=0, description='Crash world thread.', min_admin_level=250),
]
CMD_DICT = { cmd.name:cmd for cmd in COMMANDS }


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
