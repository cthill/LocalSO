import logging
from random import randint

import config
from mailbox import mail_header
from net import packet
from net.buffer import *
from world.mob import Mob

log = logging.getLogger('admin_cmd')
CHAT_RESPONSE_COLOR = 1
CHAT_PUBLIC_COLOR = 2

def handle_admin_command(client, command):
    cmd = ''
    try:
        cleaned = command.strip()[1:]
        tokens = cleaned.split(' ')

        cmd = tokens[0]
        if cmd == 'spawn':
            if len(tokens) > 1:
                mob_id = int(tokens[1])
                amount = 1
                if len(tokens) > 2:
                    amount = int(tokens[2])
                if mob_id < len(config.MOB_DATA) and amount > 0:
                    mob = config.MOB_DATA[mob_id]
                    for i in range(amount):
                        spawn(client, mob)
                else:
                    bad_command_single(client, cmd)
            else:
                bad_command_single(client, cmd)

        elif cmd == 'spawnall':
            count = 1
            if len(tokens) > 1:
                count = int(tokens[1])

            for mob in config.MOB_DATA:
                for i in range(count):
                    spawn(client, mob)

        elif cmd == 'hurt':
            local_sections = client.world.get_local_sections(client.section)
            count = 0
            with client.world.section_to_mobs as section_to_mobs:
                for section in local_sections:
                    for mob in section_to_mobs[section]:
                        mob.hp = 1
                        count += 1

            send_chat_response(client, 'hurt %s mobs.' % count)

        elif cmd == 'hurtall':
            count = 0
            with client.world.mobs as mobs:
                for mob_id in mobs:
                    mobs[mob_id].hp = 1
                    count += 1

            send_chat_response(client, 'hurt %s mobs.' % count)

        elif cmd == 'kill':
            local_sections = client.world.get_local_sections(client.section)
            count = 0
            with client.world.section_to_mobs as section_to_mobs:
                for section in local_sections:
                    for mob in section_to_mobs[section]:
                        mob.hit(mob.hp + mob.defense, 0, 0)
                        count += 1

            send_chat_response(client, 'killed %s mobs.' % count)

        elif cmd == 'killall':
            count = 0
            with client.world.mobs as mobs:
                for mob_id in mobs:
                    mob = mobs[mob_id]
                    mob.hit(mob.hp + mob.defense, 0, 0)
                    count += 1

            send_chat_response(client, 'killed %s mobs.' % count)

        elif cmd == 'godmode':
            client.god_mode = not client.god_mode
            send_chat_response(client, 'godmode is %s.' % ('on' if client.god_mode else 'off'))

        elif cmd == 'kick':
            if len(tokens) == 2:
                target_name = tokens[1]
                # we're just doing a single read so the lock is probably not strictly necessary
                with client.game_server.name_to_client as name_to_client:
                    target_client_obj = name_to_client.get(target_name.lower())

                if target_client_obj is not None:
                    log.info('%s kicked %s.' % (client, target_client_obj))
                    send_public_chat(client, '%s was kicked.' % target_client_obj.name)
                    target_client_obj.terminated = True
                else:
                    send_chat_response(client, 'player %s not found.' % target_name)
            else:
                bad_command_single(client, cmd)

        elif cmd == 'ban' or cmd == 'unban':
            if len(tokens) == 2:
                db_ref = client.game_server.master.db
                target_name = tokens[1]
                target_client_db = db_ref.get_client(target_name.lower())

                if target_client_db is not None:
                    db_ref.ban_unban_client(target_client_db['id'], cmd == 'ban')
                    log.info('%s %sned %s.' % (client, cmd, target_client_db['name']))
                    send_public_chat(client, '%s was %sned.' % (target_client_db['name'], cmd))

                    # we're just doing a single read so the lock is probably not strictly necessary
                    with client.game_server.name_to_client as name_to_client:
                        target_client_obj = name_to_client.get(target_name.lower())

                    if target_client_obj is not None:
                        target_client_obj.terminated = True
                else:
                    send_chat_response(client, 'player %s not found.' % target_name)
            else:
                bad_command_single(client, cmd)

        elif cmd == 'setadmin':
            if len(tokens) == 3:
                db_ref = client.game_server.master.db
                target_name = tokens[1]
                admin_val = tokens[2]
                if admin_val == 'true' or admin_val == 'false':
                    target_client_db = db_ref.get_client(target_name.lower())
                    if target_client_db is not None:
                        db_ref.set_admin_client(target_client_db['id'], admin_val == 'true')

                        log.info('%s set %s admin %s.' % (client, target_client_db['name'], admin_val))
                        send_chat_response(client, 'Set %s admin to %s.' % (target_name, admin_val))

                        # we're just doing a single read so the lock is probably not strictly necessary
                        with client.game_server.name_to_client as name_to_client:
                            target_client_obj = name_to_client.get(target_name.lower())

                        if target_client_obj is not None:
                            target_client_obj.kick_with_reason('There has been a change to your admin status. You will now be disconnected.')
                    else:
                        send_chat_response(client, 'player %s not found.' % target_name)
                else:
                    bad_command_single(client, cmd)
            else:
                bad_command_single(client, cmd)

        elif cmd == 'item':
            if len(tokens) == 2:
                item_id = int(tokens[1])
                if item_id >= 1 and item_id <= 72:
                    db_ref = client.game_server.master.db
                    client_db = db_ref.get_client(client.name.lower())
                    if client_db is not None:
                        client_db_id = client_db['id']
                        item_list = db_ref.get_items(client_db_id)
                        if len(item_list) < 20:
                            db_ref.add_item_on_save(client_db_id, item_id)
                            item_name = config.ITEM_DATA[item_id]['name']
                            client.kick_with_reason('%s added to your inventory. You will now be disconnected.' % item_name)
                        else:
                            send_chat_response(client, 'You have too many items. Please make room in your inventory.')
                else:
                    send_chat_response(client, 'Invalid item id.')
            else:
                bad_command_single(client, cmd)

        elif cmd == 'help':
            bad_command(client, help_text=True)

        else:
            bad_command(client)

    except Exception as e:
        bad_command_single(client, cmd)
        log.error('Error processing client %s command %s %s' % (client, command, e))
        import traceback
        traceback.print_exc()

def bad_command(client, help_text=False):
    lines = [
        ("" if help_text else "Invalid command. ") + "Available commands:",
        "  spawn <mob_id> [amount], spawnall [amount]",
        "  hurt, hurtall, kill, killall, godmode",
        "  kick <name>, ban <name>, unban <name>",
        "  setadmin <name> <true|false>, item <item_id>"
    ]

    for line in lines:
        send_chat_response(client, line)

def bad_command_single(client, cmd):
    usage = ''
    if cmd == 'spawn':
        usage = 'spawn <mob_id> [amount]'
    elif cmd == 'spawnall':
        usage = 'spawnall [count]'
    elif cmd == 'kick':
        usage = 'kick <name>'
    elif cmd == 'ban':
        usage = 'ban <name>'
    elif cmd == 'unban':
        usage = 'unban <name>'
    elif cmd == 'setadmin':
        usage = 'setadmin <name> <true|false>'
    elif cmd == 'item':
        usage = 'item <id>'
    else:
        bad_command(client)
        return

    send_chat_response(client, "Invalid command. Usage:")
    send_chat_response(client, "  %s" % usage)

def send_chat_response(client, chat_str):
    buff = [packet.MSG_CHAT]
    write_string(buff, chat_str)
    write_byte(buff, CHAT_RESPONSE_COLOR)
    client.send_tcp_message(buff)

# Note: game_server.broadcast locks the game_server.clients list. Be careful not
# to cause deadlocks when using this method
def send_public_chat(client, chat_str):
    buff = [packet.MSG_CHAT]
    write_string(buff, chat_str)
    write_byte(buff, CHAT_PUBLIC_COLOR)
    client.game_server.broadcast(buff)

def spawn(client, mob):
    spawn_y = client.get_bbox().bottom() - mob['height'] * mob['scale']
    spawn_x = client.get_bbox().hcenter() + randint(0, 100) - 50
    client.world.send_mail_message(mail_header.MSG_ADD_MOB, (mob['id'], spawn_x, spawn_y, None))
