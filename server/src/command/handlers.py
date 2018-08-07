import config
from bitmask import BITMASK_ADMIN
from mailbox import mail_header
from util import CommandError, UsageError, _send_chat_response, _spawn_multi, _send_public_chat

def cmd_help(client, tokens):
    if len(tokens) == 1:
        lines = [
            'Available commands:'
        ]

        cmds_processed = 0
        line_str = ''
        from command import COMMANDS
        for command in COMMANDS:
            if command.has_access(client.admin):
                if line_str:
                    line_str += ', '
                line_str += command.name

                cmds_processed += 1
                if cmds_processed % 5 == 0:
                    lines.append(' ' + line_str)
                    line_str = ''

        if line_str:
            lines.append(' ' + line_str)

        lines.append('Type !help <command_name> for usage information.')

        for line in lines:
            _send_chat_response(client, line)
    elif len(tokens) == 2:
        from command import CMD_DICT
        command = CMD_DICT.get(tokens[1])
        if command is not None and command.has_access(client.admin):
            _send_chat_response(client, 'Description: %s' % command.description)
            _send_chat_response(client, 'Usage: %s' % command)
        else:
            raise CommandError('unknown command %s. Type !help for a list of commands.' % tokens[1])


def cmd_statreset(client, tokens):
    client.reset_stats_on_disconnect = True
    client.kick_with_reason('Your stats have been reset. You will now be disconnected.')


def cmd_item(client, tokens):
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


def cmd_level(client, tokens):
    if len(tokens) != 2:
        raise UsageError('missing level.')

    level = int(tokens[1])
    if level < 1 or (client.admin != 250 and level > 100) or (client.admin == 250 and level > 255):
        raise CommandError('level must be between 1 and %s' % (255 if client.admin == 250 else 100))

    new_stats = {}
    if client.admin != 250 :
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


def cmd_godmode(client, tokens):
    client.god_mode = not client.god_mode
    _send_chat_response(client, 'godmode is %s.' % ('on' if client.god_mode else 'off'))


def cmd_setspawn(client, tokens):
    if len(tokens) == 1:
        raise UsageError('missing location_num.')

    location_num = int(tokens[1])
    if location_num < 1 or location_num > len(config.PLAYER_SPAWN):
        raise UsageError('invalid location_num. Must be 1 to %s.' % len(config.PLAYER_SPAWN))

    spawn_data = config.PLAYER_SPAWN[location_num]
    client.set_spawn_x_on_disconnect = spawn_data['x']
    client.kick_with_reason('Spawn point set to: %s. You will now be disconnected.' % spawn_data['name'])


def cmd_spawn(client, tokens):
    if len(tokens) == 1:
        raise UsageError('missing mob_id.')

    mob_id = int(tokens[1])
    amount = 1
    if len(tokens) > 2:
        amount = int(tokens[2])
    if mob_id < len(config.MOB_DATA) and amount > 0:
        mobs_to_spawn = [config.MOB_DATA[mob_id]]
        _spawn_multi(client, mobs_to_spawn, amount)
    else:
        raise CommandError('unknown mob %s.' % tokens[1])


def cmd_spawnall(client, tokens):
    amount = 1
    if len(tokens) == 2:
        amount = int(tokens[1])

    mobs_to_spawn = config.MOB_DATA
    _spawn_multi(client, mobs_to_spawn, amount)


def cmd_hurt(client, tokens):
    local_sections = client.world.get_local_sections(client.section)
    count = 0
    with client.world.section_to_mobs as section_to_mobs:
        for section in local_sections:
            for mob in section_to_mobs[section]:
                mob.hp = 1
                count += 1

    _send_chat_response(client, 'hurt %s mobs.' % count)


def cmd_hurtall(client, tokens):
    count = 0
    with client.world.mobs as mobs:
        for mob_id in mobs:
            mobs[mob_id].hp = 1
            count += 1

    _send_chat_response(client, 'hurt %s mobs.' % count)


def cmd_kill(client, tokens):
    local_sections = client.world.get_local_sections(client.section)
    count = 0
    with client.world.section_to_mobs as section_to_mobs:
        for section in local_sections:
            for mob in section_to_mobs[section]:
                mob.hit(mob.hp + mob.defense, 0, 0)
                count += 1

    _send_chat_response(client, 'killed %s mobs.' % count)


def cmd_killall(client, tokens):
    count = 0
    with client.world.mobs as mobs:
        for mob_id in mobs:
            mob = mobs[mob_id]
            mob.hit(mob.hp + mob.defense, 0, 0)
            count += 1

    _send_chat_response(client, 'killed %s mobs.' % count)


def cmd_kick(client, tokens):
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


def cmd_ban_unban(client, tokens):
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


def cmd_setadmin(client, tokens):
    if len(tokens) != 3:
        raise UsageError('missing player name or admin val.')

    target_name = tokens[1]
    admin_level = int(tokens[2])
    if admin_level < 0 or admin_level > 250:
        raise UsageError('admin level must be between 0 and 250.')

    if bool(admin_level & BITMASK_ADMIN) and admin_level != 250:
        raise UsageError('If admin bit is set, admin level bitmask must equal 250.')

    db_ref = client.game_server.stick_online_server.db
    target_client_db = db_ref.get_client(target_name.lower())
    if target_client_db is None:
        raise CommandError('player %s not found.' % target_name)

    # we're just doing a single read so the lock is probably not strictly necessary
    with client.game_server.name_to_client as name_to_client:
        target_client_obj = name_to_client.get(target_name.lower())

    old_admin = target_client_db['admin_level']
    if old_admin == 250 and admin_level != old_admin:
        # player is changing from admin 250 so we may need to reset
        # their stat points since the client checks for abnormal stats
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

    db_ref.set_admin_client(target_client_db['id'], admin_level)
    _send_chat_response(client, 'Set %s admin to %s.' % (target_name, admin_level))

    if target_client_obj is not None:
        # the client application has no way for the server to indicate
        # that the player's admin status has changed. So we must disconnect
        # them and write to the db while they are disconnected
        target_client_obj.kick_with_reason('There has been a change to your player command access. You will now be disconnected.')


def cmd_crashworld(client, tokens):
    client.world.send_mail_message(mail_header.MSG_POISON_PILL, None)
    _send_chat_response(client, 'crashed world thread')
