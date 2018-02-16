import logging

import config
from mailbox import mail_header
from net import packet
from net.buffer import *
from world.mob import Mob

CHAT_COLOR = 1

def handle_admin_command(client, command):
    try:
        cleaned = command.strip()[1:]
        tokens = cleaned.split(' ')

        if tokens[0] == 'spawnall':
            count = 1
            if len(tokens) > 1:
                count = int(tokens[1])

            for mob in config.MOB_DATA:
                for i in range(count):
                    new_mob = Mob(client.world.generate_mob_id(), mob['id'], client.x, client.y - 300, None, client.world)
                    client.world.send_mail_message(mail_header.MSG_ADD_MOB, new_mob)

        elif tokens[0] == 'spawn':
            try:
                mob_id = int(tokens[1])
                amount = 1
                if len(tokens) > 2:
                    amount = int(tokens[2])
                if mob_id < len(config.MOB_DATA) and amount > 0:
                    for i in range(amount):
                        new_mob = Mob(client.world.generate_mob_id(), mob_id, client.x, client.y - 300, None, client.world)
                        client.world.send_mail_message(mail_header.MSG_ADD_MOB, new_mob)
                else:
                    bad_command(client)
            except Exception:
                bad_command(client)

        elif tokens[0] == 'hurtall':
            count = 0
            for mob_id in client.world.mobs.keys():
                mob = client.world.mobs[mob_id]
                mob.hp = 1
                count += 1

            buff = [packet.MSG_CHAT]
            write_string(buff, 'hurt %s mobs.' % count)
            write_byte(buff, CHAT_COLOR)
            client.send_tcp_message(buff)

        elif tokens[0] == 'killall':
            count = 0
            for mob_id in client.world.mobs.keys():
                mob = client.world.mobs[mob_id]
                mob.hit(mob.hp + mob.defense, 0, 0)
                count += 1

            buff = [packet.MSG_CHAT]
            write_string(buff, 'killed %s mobs.' % count)
            write_byte(buff, CHAT_COLOR)
            client.send_tcp_message(buff)

        else:
            bad_command(client)

    except Exception as e:
        bad_command(client)
        logging.error('Error processing client %s command %s %s' % (client, command, e))


def bad_command(client):
    lines = [
        "Invalid command. Available commands:",
        "  spawnall [amount],  spawn <mob_id> [amount]",
        "  hurtall,  killall"
    ]

    for line in lines:
        buff = [packet.MSG_CHAT]
        write_string(buff, line)
        write_byte(buff, CHAT_COLOR)
        client.send_tcp_message(buff)
