import logging
from random import randint

import config
from mailbox import mail_header
from net import packet
from net.buffer import *
from world.mob import Mob

CHAT_RESPONSE_COLOR = 1
CHAT_PUBLIC_COLOR = 2

class CommandError(RuntimeError):
    pass

class UsageError(RuntimeError):
    pass

class Command:
    def __init__(self, name, handler, arg_str='', max_args=0, description='', admin=True):
        self.name = name
        self.handler = handler
        self.arg_str = arg_str
        self.max_args = max_args
        self.description = description
        self.admin = admin

    def handle(self, client, tokens):
        if self.admin and client.admin != 250:
            _unknown_cmd(client)
            return

        try:
            if len(tokens) - 1 > self.max_args:
                raise UsageError('too many arguments.')
            else:
                self.handler(client, tokens)
                client.logger.info('good command "!%s"' % (' '.join(tokens)))

        except CommandError as e:
            client.logger.info('command error "!%s": %s' % (' '.join(tokens), str(e)))
            _send_chat_response(client, 'Error: %s' % str(e))

        except UsageError as e:
            client.logger.info('usage error "!%s": %s' % (' '.join(tokens), str(e)))
            if len(str(e)) > 0:
                _send_chat_response(client, 'Error: %s' % str(e))
            _send_chat_response(client, 'Usage: %s' % self)

    def __str__(self):
        return '!%s %s' % (self.name, self.arg_str)

def handle_admin_command(client, command_string):
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

def _cmd_help(client, tokens):
    if len(tokens) == 1:
        lines = [
            'Available commands:'
        ]

        cmds_processed = 0
        line_str = ''
        for command in COMMANDS:
            if client.admin == 250 or not command.admin:
                if line_str:
                    line_str += ', '
                line_str += command.name

                cmds_processed += 1
                if cmds_processed % 4 == 0:
                    lines.append(' ' + line_str)
                    line_str = ''

        lines.append('Type !help <command_name> for usage information.')

        for line in lines:
            _send_chat_response(client, line)
    elif len(tokens) == 2:
        command = CMD_DICT.get(tokens[1])
        if command is not None and (client.admin == 250 or not command.admin):
            _send_chat_response(client, 'Description: %s' % command.description)
            _send_chat_response(client, 'Usage: %s' % command)
        else:
            raise CommandError('unknown command %s. Type !help for a list of commands.' % tokens[1])

def _cmd_item(client, tokens):
    if len(tokens) != 2:
        raise UsageError('missing item id.')

    item_id = int(tokens[1])
    if item_id >= 1 and item_id <= 72:
        db_ref = client.game_server.stick_online_server.db
        client_db = db_ref.get_client(client.name.lower())
        if client_db is not None:
            client_db_id = client_db['id']
            item_list = db_ref.get_items(client_db_id)
            with client.add_items_on_disconnect as new_items:
                if len(item_list) + len(new_items) < 20:
                    new_items.append(item_id)
                    item_name = config.ITEM_DATA[item_id]['name']
                    _send_chat_response(client, '%s will be added to your inventory on disconnect.' % item_name)
                else:
                    raise CommandError('too many items. Make room in inventory and disconnect before trying again.')
    else:
        raise CommandError('invalid item id.')

def _cmd_level(client, tokens):
    if len(tokens) != 2:
        raise UsageError('missing level.')

    level = int(tokens[1])
    if level < 1 or (client.admin != 250 and level > 100) or (client.admin == 250 and level > 255):
        raise CommandError('level must be between 1 and %s' % (255 if client.admin == 250 else 100))

    new_stats = {}
    if not client.admin:
        new_stats['level'] = level
        new_stats['stat_str'] = 1
        new_stats['stat_agi'] = 1
        new_stats['stat_int'] = 1
        new_stats['stat_vit'] = 1
        new_stats['stat_points'] = level - 1
        if level == 100:
            new_stats['stat_points'] += 4
    else:
        new_stats['level'] = level
        new_stats['stat_str'] = 150
        new_stats['stat_agi'] = 150
        new_stats['stat_int'] = 150
        new_stats['stat_vit'] = 150
        new_stats['stat_points'] = 0

    client.set_stats_on_disconnect = new_stats
    client.kick_with_reason('Level set to %s and stats reset. You will now be disconnected.' % level)

def _cmd_godmode(client, tokens):
    client.god_mode = not client.god_mode
    _send_chat_response(client, 'godmode is %s.' % ('on' if client.god_mode else 'off'))


# admin commands

def _cmd_spawn(client, tokens):
    if len(tokens) == 1:
        raise UsageError('missing mob_id.')

    mob_id = int(tokens[1])
    amount = 1
    if len(tokens) > 2:
        amount = int(tokens[2])
    if mob_id < len(config.MOB_DATA) and amount > 0:
        mob = config.MOB_DATA[mob_id]
        for i in range(amount):
            _spawn(client, mob)
    else:
        raise CommandError('unknown mob %s.' % tokens[1])


def _cmd_spawnall(client, tokens):
    count = 1
    if len(tokens) == 2:
        count = int(tokens[1])

    for mob in config.MOB_DATA:
        for i in range(count):
            _spawn(client, mob)

def _cmd_hurt(client, tokens):
    local_sections = client.world.get_local_sections(client.section)
    count = 0
    with client.world.section_to_mobs as section_to_mobs:
        for section in local_sections:
            for mob in section_to_mobs[section]:
                mob.hp = 1
                count += 1

    _send_chat_response(client, 'hurt %s mobs.' % count)

def _cmd_hurtall(client, tokens):
    count = 0
    with client.world.mobs as mobs:
        for mob_id in mobs:
            mobs[mob_id].hp = 1
            count += 1

    _send_chat_response(client, 'hurt %s mobs.' % count)

def _cmd_kill(client, tokens):
    local_sections = client.world.get_local_sections(client.section)
    count = 0
    with client.world.section_to_mobs as section_to_mobs:
        for section in local_sections:
            for mob in section_to_mobs[section]:
                mob.hit(mob.hp + mob.defense, 0, 0)
                count += 1

    _send_chat_response(client, 'killed %s mobs.' % count)

def _cmd_killall(client, tokens):
    count = 0
    with client.world.mobs as mobs:
        for mob_id in mobs:
            mob = mobs[mob_id]
            mob.hit(mob.hp + mob.defense, 0, 0)
            count += 1

    _send_chat_response(client, 'killed %s mobs.' % count)

def _cmd_kick(client, tokens):
    if len(tokens) != 2:
        raise UsageError('missing player name.')

    target_name = tokens[1]
    # we're just doing a single read so the lock is probably not strictly necessary
    with client.game_server.name_to_client as name_to_client:
        target_client_obj = name_to_client.get(target_name.lower())

    if target_client_obj is not None:
        _send_public_chat(client, '%s was kicked.' % target_client_obj.name)
        target_client_obj.terminated = True
    else:
        raise CommandError('player %s not found.' % target_name)


def _cmd_ban_unban(client, tokens):
    if len(tokens) != 2:
        raise UsageError('missing player name.')

    db_ref = client.game_server.stick_online_server.db
    target_name = tokens[1]
    target_client_db = db_ref.get_client(target_name.lower())

    if target_client_db is not None:
        db_ref.ban_unban_client(target_client_db['id'], tokens[0] == 'ban')
        _send_public_chat(client, '%s was %sned.' % (target_client_db['name'], tokens[0]))

        # we're just doing a single read so the lock is probably not strictly necessary
        with client.game_server.name_to_client as name_to_client:
            target_client_obj = name_to_client.get(target_name.lower())

        if target_client_obj is not None:
            target_client_obj.terminated = True
    else:
        raise CommandError('player %s not found.' % target_name)

def _cmd_setadmin(client, tokens):
    if len(tokens) != 3:
        raise UsageError('missing player name or admin val.')

    target_name = tokens[1]
    admin_val = tokens[2]
    if admin_val == 'true' or admin_val == 'false':
        db_ref = client.game_server.stick_online_server.db
        target_client_db = db_ref.get_client(target_name.lower())
        if target_client_db is not None:
            # we're just doing a single read so the lock is probably not strictly necessary
            with client.game_server.name_to_client as name_to_client:
                target_client_obj = name_to_client.get(target_name.lower())

            old_admin = target_client_db['admin_level']
            if old_admin == 250 and admin_val != 'true':
                # player is changing from admin to not admin so we may need to reset
                # their stat points since the client check for abnormal stats
                stats = {
                    'level': target_client_db['level'],
                    'stat_str': target_client_db['stat_str'],
                    'stat_agi': target_client_db['stat_agi'],
                    'stat_int': target_client_db['stat_int'],
                    'stat_vit': target_client_db['stat_vit'],
                    'stat_points': target_client_db['stat_points'],
                }

                reset_stat_points = False
                stats_sum = stats['stat_str'] + stats['stat_agi'] + stats['stat_int'] + stats['stat_vit'] + stats['stat_points']

                if stats['level'] < 100:
                    # check if player got more than one stat per level
                    if stats_sum - 4 != stats['level'] - 1:
                        reset_stat_points = True
                elif stats['level'] == 100:
                    # the player gets an extra 4 stat points when they reach level 100
                    if stats_sum - 4 != stats['level'] - 1 + 4:
                        reset_stat_points = True
                else:
                    stats['level'] = 100
                    reset_stat_points = True

                if reset_stat_points:

                    stats['stat_str'] = 1
                    stats['stat_agi'] = 1
                    stats['stat_int'] = 1
                    stats['stat_vit'] = 1
                    stats['stat_points'] = stats['level'] - 1
                    if stats['level'] == 100:
                        stats['stat_points'] += 4

                    if target_client_obj is not None:
                        target_client_obj.set_stats_on_disconnect = stats
                    else:
                        db_ref.set_stats(target_client_db['id'], stats)

            db_ref.set_admin_client(target_client_db['id'], admin_val == 'true')
            _send_chat_response(client, 'Set %s admin to %s.' % (target_name, admin_val))

            if target_client_obj is not None:
                # the client application has no way for the server to indicate
                # that the player's admin status has changed. So we must disconnect
                # them and write to the db while they are disconnected
                target_client_obj.kick_with_reason('There has been a change to your admin status. You will now be disconnected.')
        else:
            raise CommandError('player %s not found.' % target_name)
    else:
        raise CommandError('admin val must be true or false.')

def _send_chat_response(client, chat_str):
    buff = [packet.MSG_CHAT]
    write_string(buff, chat_str)
    write_byte(buff, CHAT_RESPONSE_COLOR)
    client.send_tcp_message(buff)

def _unknown_cmd(client):
    _send_chat_response(client, 'Unknown command. Type !help for a list of commands.')

def _cmd_error(client):
    _send_chat_response(client, 'An unknown error occured while processing your command.')

# Note: game_server.broadcast locks the game_server.clients list. Be careful not
# to cause deadlocks when using this method
def _send_public_chat(client, chat_str):
    buff = [packet.MSG_CHAT]
    write_string(buff, chat_str)
    write_byte(buff, CHAT_PUBLIC_COLOR)
    client.game_server.broadcast(buff)

def _spawn(client, mob):
    spawn_y = client.get_bbox().bottom() - mob['height'] * mob['scale']
    spawn_x = client.get_bbox().hcenter() + randint(0, 100) - 50
    client.world.send_mail_message(mail_header.MSG_ADD_MOB, (mob['id'], spawn_x, spawn_y, None))

COMMANDS = [
    # player commands
    Command('help', _cmd_help, arg_str='[cmd_name]', max_args=1, description='Display a help menu.', admin=False),
    Command('item', _cmd_item, arg_str='<item_id>', max_args=1, description='Obtain an item of id (1 to 72).', admin=False),
    Command('level', _cmd_level, arg_str='<level>', max_args=1, description='Set level (will reset stats).', admin=False),
    Command('godmode', _cmd_godmode, arg_str='', max_args=0, description='Toggle godmode.', admin=False),
    # admin commands
    Command('spawn', _cmd_spawn, arg_str='<mob_id> [amount]', max_args=2, description='Spawn mob(s) of given id (0 to 18).', admin=True),
    Command('spawnall', _cmd_spawnall, arg_str='[amount]', max_args=1, description='Spawn all mobs.', admin=True),
    Command('hurt', _cmd_hurt, arg_str='', max_args=0, description='Set nearby mobs to 1 hp.', admin=True),
    Command('hurtall', _cmd_hurtall, arg_str='', max_args=0, description='Set all mobs to 1 hp.', admin=True),
    Command('kill', _cmd_kill, arg_str='', max_args=0, description='Kill nearby mobs.', admin=True),
    Command('killall', _cmd_killall, arg_str='', max_args=0, description='Kill all mobs.', admin=True),
    Command('kick', _cmd_kick, arg_str='<name>', max_args=1, description='Kick a player.', admin=True),
    Command('ban', _cmd_ban_unban, arg_str='<name>', max_args=1, description='Ban a player.', admin=True),
    Command('unban', _cmd_ban_unban, arg_str='<name>', max_args=1, description='Unban a player.', admin=True),
    Command('setadmin', _cmd_setadmin, arg_str='<name> <true|false>', max_args=2, description='Change player admin status.', admin=True),
]
CMD_DICT = { cmd.name:cmd for cmd in COMMANDS }
