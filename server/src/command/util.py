import config
from random import randint

from bitmask import BITMASK_ADMIN
from mailbox import mail_header
from net import packet
from net.buffer import write_string, write_byte

CHAT_RESPONSE_COLOR = 1
CHAT_PUBLIC_COLOR = 2

class CommandError(RuntimeError):
    pass

class UsageError(RuntimeError):
    pass

class Command:
    def __init__(self, name, handler, arg_str='', max_args=0, description='', bitmask=BITMASK_ADMIN):
        self.name = name
        self.handler = handler
        self.arg_str = arg_str
        self.max_args = max_args
        self.description = description
        self.bitmask = bitmask

    def handle(self, client, tokens):
        if not self.has_access(client.admin):
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

    def has_access(self, client_bitmask):
        return self.bitmask == 0 or bool(client_bitmask & self.bitmask)

    def __str__(self):
        return '!%s %s' % (self.name, self.arg_str)

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

def _spawn_multi(client, mobs, amount):
    client_mob_spawn = client.get_mob_spawn()

    # limit spawn counts for non-admin players
    amount_clamped = amount
    max_mobs = config.ADMIN_MAX_MOB_SPAWN if client.admin == 250 else config.NON_ADMIN_MAX_MOB_SPAWN
    amount_clamped = min(max_mobs - len(client_mob_spawn.mobs), amount)

    # spawn the mobs
    total_spawned = 0
    for i in range(amount_clamped):
        for mob in mobs:
            spawn_y = client.get_bbox().bottom() - mob['height'] * mob['scale']
            spawn_x = client.get_bbox().hcenter() + randint(0, 100) - 50
            client.world.send_mail_message(mail_header.MSG_ADD_MOB, (mob['id'], spawn_x, spawn_y, client_mob_spawn))
            total_spawned += 1

    # send chat response
    if amount_clamped < amount:
        _send_chat_response(client, 'Spawned %s mobs. (You can only have %s at one time).' % (total_spawned, max_mobs))
    else:
        _send_chat_response(client, 'Spawned %s mobs.' % (total_spawned))
