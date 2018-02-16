import logging
import threading
import traceback

import command
import config
from net import packet
from world.bounding_box import BoundingBox
from mailbox import mail_header
from mailbox import Mailbox
from world.mob import Mob
from net.buffer import *
from net.socket import tcp_write
from util import buff_to_str

class Client(Mailbox):

    def __init__(self, game_server, world, socket, id, client_data):
        super(Client, self).__init__()

        # setup params
        self.game_server = game_server
        self.world = world
        self.socket = socket
        self.id = id

        self.name = client_data['name']
        self.clan = client_data['clan']
        self.hat = client_data['hat']
        self.weapon = client_data['weapon']
        self.admin = client_data['admin']
        self.pvp_enabled = False

        self.x = 0
        self.y = 0
        self.x_speed = 0
        self.y_speed = 0
        self.sprite_index = 0x09
        self.image_index = 0x00
        self.animation_speed = 0.5
        self.facing_right = True

        # setup other
        self.terminated = False
        self.section = None
        self.update_position(0, 0)

        # write player id
        buff = []
        write_ushort(buff, self.id)
        self.send_tcp_message(buff)

    def send_tcp_message(self, data):
        self.send_mail_message(mail_header.MSG_CLIENT_SEND_TCP, data)

    def send_tcp_message_multiple(self, packets):
        for data in packets:
            self.send_mail_message(mail_header.MSG_CLIENT_SEND_TCP, data)


    def start(self):
        # start the msg_send thread
        t = threading.Thread(target=self._send_thread)
        t.start()

        # start the msg_recv thread
        t = threading.Thread(target=self._recv_thread)
        t.start()

        # write number of players online
        buff = [packet.RESP_NUM_PLAYERS]
        write_ushort(buff, self.game_server.get_num_players())
        self.send_tcp_message(buff)

        buff = [packet.RESP_CHAT]
        write_string(buff, config.GAME_MOTD)
        write_byte(buff, 2)
        self.send_tcp_message(buff)

        # self.world.event_scheduler.schedule_event_recurring(self.send_dmg, 10)

    def _send_thread(self):
        try:
            while not self.terminated:
                mail_message = self._get_mail_message_blocking()
                header = mail_message[0]
                payload = mail_message[1]
                if header == mail_header.MSG_CLIENT_SEND_TCP:
                    tcp_write(self.socket, payload)

        except Exception as e:
            if not self.terminated:
                logging.info('Unhandled exception in client %s send_thread %s' % (self, e))
                traceback.print_exc()
        finally:
            self._terminate()

    def _recv_thread(self):
        try:
            while not self.terminated:
                size = bytearray(self.socket.recv(2))
                if not size:
                    break
                size_int = read_short(size, 0)
                self._handle_packet(size_int)
        except Exception as e:
            if not self.terminated:
                logging.info('Unhandled exception in client %s recv_thread %s' % (self, e))
                traceback.print_exc()
        finally:
            self._terminate()

    def _terminate(self):
        if not self.terminated:
            self.terminated = True
            self.world.client_disconnect(self)
            self.game_server.client_disconnect(self)
            self.socket.close()
            logging.info('Client %s disconnected' % self)


    # def send_dmg(self):
    #     buff = [packet.RESP_DMG_PLAYER]
    #     write_ushort(buff, self.id)
    #     write_ushort(buff, 2)
    #     write_byte(buff, 30)
    #     write_ushort(buff, config.HIT_SOUND_ID)
    #     write_short(buff, 10 * 10)
    #     write_short(buff, -10 * 10)
    #     self.send_tcp_message(buff)

    def _handle_packet(self, size):
        raw_data = self.socket.recv(size)
        data = bytearray(raw_data)

        logging.info("Client %s data: %s" % (self, buff_to_str(data)))

        header = data[0]
        if header == packet.MSG_INIT:
            new_x = read_int(data, 2) / 10.0
            new_y = read_short(data, 6) / 10.0
            self.update_position(new_x, new_y)
            self.facing_right = read_byte(data, 8) > 0
            self.x_speed = read_short(data, 9) / 10.0
            self.y_speed = read_short(data, 11) / 10.0
            # mystery_byte = read_byte(data, 13)
            self.sprite_index = read_short(data, 14)
            self.image_index = read_short(data, 16) / 100.0
            self.animation_speed = read_short(data, 18) / 100.0
            self.hat = read_ushort(data, 20)
            # client_claim_is_admin = read_byte(data, 22)
            self.pvp_enabled = read_byte(data, 23) > 0

            # forward message (broadcast new player entered)
            buff = [packet.RESP_NEW_PLAYER]
            write_ushort(buff, self.id)
            buff.extend(data[2:])
            self.game_server.broadcast(buff, exclude=self)

            # tell self of all other players in area
            for other_client in self.game_server.get_clients():
                if other_client is self:
                    continue

                buff = [packet.RESP_NEW_PLAYER]
                other_client.write_full_client_data(buff)
                self.send_tcp_message(buff)

        elif header == packet.MSG_PLAYER_DEATH:
            buff = [packet.RESP_PLAYER_DEATH]
            write_uint(buff, self.id)
            self.game_server.broadcast(buff)

        elif header == packet.MSG_OTHER_PLAYER_NOT_FOUND:
            client_id = read_ushort(data, 2)
            if client_id not in self.game_server.id_to_client:
                return
            other_client = self.game_server.id_to_client[client_id]

            buff = [packet.RESP_NEW_PLAYER]
            other_client.write_full_client_data(buff)
            self.send_tcp_message(buff)

        elif header == packet.MSG_PVP_HIT_PLAYER:
            other_player_id = read_ushort(data, 2)
            print 'Client %s try hit player %s' % (self, other_player_id)
            if other_player_id in self.game_server.id_to_client:
                buff = [packet.RESP_DMG_PLAYER]
                buff.extend(data[2:])

                knockback_x = read_short(data, 9) / 10.0
                knockback_y = read_short(data, 11) / 10.0
                print 'Client %s hit player kbx %s kby %s' % (self, knockback_x, knockback_y)
                self.game_server.broadcast(buff, exclude=self)

        elif header == packet.MSG_CHAT:
            offset = 2
            message = read_string(data, offset)
            offset += len(message) + 1
            chat_type = read_byte(data, offset)

            if self.admin == 0xfa and message.strip().startswith('!'):
                command.handle_admin_command(self, message)
                return

            buff = [packet.RESP_CHAT]
            write_string(buff, "%s: %s" % (self.name, message))
            write_byte(buff, chat_type)
            self.game_server.broadcast(buff)

        elif header == packet.MSG_HIT_MOB:
            mob_id = read_ushort(data, 2) # mob id
            damage = read_ushort(data, 4) # damage
            invincible_frames = read_byte(data, 6)
            sound_id = read_ushort(data, 7) # sound_id
            knockback_x = read_short(data, 9) / 10.0
            knockback_y = read_short(data, 11) / 10.0
            print 'sound id %s knockback_x %s, knockback_y %s' % (sound_id, knockback_x, knockback_y)

            # damage = 3 # for testing
            damage = damage * config.PLAYER_DAMAGE_MULTIPLIER

            # notify the world that we hit a mob
            self.world.send_mail_message(mail_header.MSG_HIT_MOB, (mob_id, damage, knockback_x, knockback_y))

            # broadcast the hit out
            buff = [packet.RESP_HIT_MOB]
            write_ushort(buff, mob_id)
            write_ushort(buff, damage)
            write_byte(buff, invincible_frames)
            write_ushort(buff, sound_id)
            self.game_server.broadcast(buff)

        elif header == packet.MSG_CLIENT_ERROR:
            error_code = read_short(data, 2)
            logging.info('Client %s error %s' % (self, error_code))
            # TODO: write to an error log

        elif header == packet.MSG_HAT_CHANGE:
            val1 = read_byte(data, 2)
            new_hat = read_ushort(data, 3)
            pvp_enabled = read_byte(data, 6)

            self.hat = new_hat
            self.pvp_enabled = pvp_enabled > 0

            buff = [packet.RESP_HAT_CHANGE]
            write_ushort(buff, self.id)
            write_byte(buff, val1)
            write_ushort(buff, new_hat)
            write_byte(buff, self.admin)
            write_byte(buff, pvp_enabled)
            self.game_server.broadcast(buff, exclude=self)

        elif header == packet.MSG_GET_NUM_PLAYERS:
            # write number of players online
            buff = [packet.RESP_NUM_PLAYERS]
            write_ushort(buff, self.game_server.get_num_players())
            self.send_tcp_message(buff)

        elif header == packet.MSG_SPAWN_MOB:
            if self.admin != 250:
                return

            mob_type = read_ushort(data, 3)
            x = read_uint(data, 5) / 10.0
            y = read_short(data, 9) / 10.0
            # logging.info('Client %s wants to spawn %s at (%s,%s)' % (self, mob_type, x, y))

            new_mob = Mob(self.world.generate_mob_id(), mob_type, x, y, None, self.world)
            self.world.send_mail_message(mail_header.MSG_ADD_MOB, new_mob)

        elif header == packet.MSG_LEVEL_UP:
            new_level = read_byte(data, 2)

            buff = [packet.RESP_LEVEL_UP]
            write_string(buff, self.name)
            write_byte(buff, new_level)
            self.game_server.broadcast(buff)

        else:
            logging.info('Client %s unknown packet %s' % (self, buff_to_str(data)))

    def write_full_client_data(self, buff):
        write_ushort(buff, self.id) # id
        write_uint(buff, int(round(self.x * 10))) # x
        write_short(buff, int(round(self.y * 10))) # y

        write_byte(buff, self.facing_right) # facing right
        write_short(buff, self.x_speed * 10) # x speed
        write_short(buff, self.y_speed * 10) # y speed
        write_byte(buff, 0x00) # ?? should always be 0?
        write_ushort(buff, self.sprite_index) # sprite
        write_short(buff, self.image_index * 100) # image_index

        write_short(buff, self.animation_speed * 100) # animation speed?
        write_ushort(buff, self.hat) # hat equipped
        write_byte(buff, self.admin) # is admin
        write_byte(buff, self.pvp_enabled) # pvp enabled
        write_string(buff, self.name) # username
        write_string(buff, self.clan) # clan

    def update_position(self, x, y):
        self.x = x
        self.y = y

        old_section = self.section
        new_section = self.world.find_section_index(int(round(x)))

        if old_section != new_section:
            self.section = new_section
            self.world.send_mail_message(mail_header.UPDATE_CLIENT_SECTION, (self, old_section, new_section))

            logging.info('Client %s new section %s' % (self, new_section))
            logging.info('Active sections: %s' % (self.world.get_active_sections()))

    def get_bbox(self):
        return BoundingBox(self.x - config.PLAYER_OFFSET_X, self.y - config.PLAYER_OFFSET_Y, config.PLAYER_MASK_WIDTH, config.PLAYER_MASK_HEIGHT)

    def handle_udp_packet(self, data):
        header = data[0]
        if header == packet.MSG_UDP_PLAYER_POS_CHANGE or header == packet.MSG_UDP_PLAYER_SPRITE_CHANGE:
            # TODO: only broadcast this info to local players

            # client_id = read_uint(data, 1)
            new_x = read_int(data, 3) / 10.0
            new_y = read_short(data, 7) / 10.0
            self.update_position(new_x, new_y)
            self.x_speed = read_short(data, 9) / 10.0
            self.y_speed = read_short(data, 11) / 10.0

            if header == packet.MSG_UDP_PLAYER_SPRITE_CHANGE:
                self.sprite_index = read_short(data, 13)
                self.image_index = read_short(data, 15) / 100.0
                self.animation_speed = read_short(data, 17) / 100.0
                self.facing_right = read_byte(data, 19) > 0
            else:
                if self.x_speed < 0:
                    self.facing_right = False
                elif self.x_speed > 0:
                    self.facing_right = True

            self.game_server.broadcast(data, exclude=self)

        elif header == packet.MSG_UDP_PING:
            buff = [packet.RESP_PING]
            self.send_tcp_message(buff)

    def __str__(self):
        return '(%s, %s)' % (self.id, self.name)
