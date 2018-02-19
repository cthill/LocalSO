import logging

import config
from mailbox import mail_header
from net import packet
from net.buffer import *
from world.mob import Mob

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

        elif cmd == 'hurtall':
            count = 0
            for mob_id in client.world.mobs.keys():
                mob = client.world.mobs[mob_id]
                mob.hp = 1
                count += 1

            send_chat_response(client, 'hurt %s mobs.' % count)

        elif cmd == 'killall':
            count = 0
            for mob_id in client.world.mobs.keys():
                mob = client.world.mobs[mob_id]
                mob.hit(mob.hp + mob.defense, 0, 0)
                count += 1

            send_chat_response(client, 'killed %s mobs.' % count)

        elif cmd == 'godmode':
            client.god_mode = not client.god_mode
            send_chat_response(client, 'godmode is %s.' % ('on' if client.god_mode else 'off'))

        elif cmd == 'kick':
            if len(tokens) > 1:
                name_to_kick = tokens[1]
                client_to_kick = client.game_server.name_to_client.get(name_to_kick)
                if client_to_kick is not None:
                    logging.info('%s kicked %s.' % (client, client_to_kick))
                    client_to_kick.terminated = True
                    send_public_chat(client, '%s was kicked.' % client_to_kick.name)
                else:
                    send_chat_response(client, 'player %s not found.' % name_to_kick)
            else:
                bad_command_single(client, cmd)

        else:
            bad_command(client)

    except Exception as e:
        bad_command_single(client, cmd)
        logging.error('Error processing client %s command %s %s' % (client, command, e))


def bad_command(client):
    lines = [
        "Invalid command. Available commands:",
        "  spawn <mob_id> [amount], spawnall [amount]",
        "  hurtall,  killall, godmode",
        "  kick <name>"
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

def send_public_chat(client, chat_str):
    buff = [packet.MSG_CHAT]
    write_string(buff, chat_str)
    write_byte(buff, CHAT_PUBLIC_COLOR)
    client.game_server.broadcast(buff)

def spawn(client, mob):
    spawn_y = client.get_bbox().bottom() - mob['height'] * mob['scale']
    new_mob = Mob(client.world.generate_mob_id(), mob['id'], client.x, spawn_y, None, client.world)
    client.world.send_mail_message(mail_header.MSG_ADD_MOB, new_mob)
