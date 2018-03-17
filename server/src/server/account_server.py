from datetime import datetime
import logging
import socket
import threading
import traceback

import config
from db.db import SQLiteDB
from net import packet
from net.buffer import *
from net.socket import tcp_write
from util import buff_to_str

class AccountServer:
    def __init__(self, interface, port, db, master):
        self.log = logging.getLogger('account_svr')

        self.interface = interface
        self.port = port
        self.db = db
        self.master = master

        self.terminated = False

    def __call__(self):
        # listen tcp
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.interface, self.port))
        s.listen(1)

        self.log.info('listening %s:%s' % (self.interface, self.port))

        while not self.terminated:
            conn, addr = s.accept()
            self.log.info('new connection: %s:%s' % (addr))
            t = threading.Thread(target=self._account_server_client, args=(conn, addr))
            t.start()

    def _account_server_client(self, conn, addr):
        try:
            input_buffer = bytearray()
            while not self.terminated:
                data = bytearray(conn.recv(4096))
                if not data:
                    break
                input_buffer += data

                while len(input_buffer) >= 2:
                    packet_size = read_ushort(input_buffer, 0)
                    if len(input_buffer) - 2 < packet_size:
                        break

                    packet_data = input_buffer[2:packet_size+2]
                    input_buffer = input_buffer[packet_size+2:]
                    self._handle_packet(conn, addr, packet_data)

        except Exception as e:
            self.log.error('Unhandled exception in client %s:%s thread %s' % (addr[0], addr[1], e))
            traceback.print_exc()
        finally:
            conn.close()
            self.log.info('client %s:%s disconnected' % addr)

    def _handle_packet(self, conn, addr, data):
        enc_dec_buffer(data)

        self.log.debug('client %s:%s data: %s' % (addr[0], addr[1], buff_to_str(data)))

        header = data[0]
        if header == packet.MSG_REGISTER:
            self._register(conn, addr, data)
        elif header == packet.MSG_LOGIN:
            self._login(conn, addr, data)
        elif header == packet.MSG_SAVE:
            self._save(conn, addr, data)
        else:
            self.log.info('client %s:%s unknown packet %s' % (addr[0], addr[1], buff_to_str(data)))

    def _deny_request(self, conn, addr, reason):
        buff = [packet.RESP_DENY_REQUEST]
        write_string(buff, reason)
        tcp_write(conn, buff, enc=True)
        self.log.info('request denied %s:%s %s' % (addr[0], addr[1], reason))


    def _register(self, conn, addr, data):
        offset = 1

        client_version = read_double(data, offset)
        offset += 8

        username = read_string(data, offset)
        offset += len(username) + 1

        pass_hash = read_string(data, offset)
        offset += len(pass_hash) + 1

        mac = read_string(data, offset)
        offset += len(mac) + 1

        self.log.info('register request %s:%s %s:%s %s' % (addr[0], addr[1], username, pass_hash, mac))

        if config.REGISTER_CLOSED:
            self._deny_request(conn, addr, 'Registration is currently closed.')
            return

        if client_version != config.COMPATIBLE_GAME_VERSION:
            self._deny_request(conn, addr, 'You are using an incorrect version of the game. Please download version 0.0227')
            return

        if len(username) < 3:
            self._deny_request(conn, addr, 'Your username must be atleast 3 characters long.')
            return

        if len(username) > 12:
            self._deny_request(conn, addr, 'Your username can not be more than 12 characters.')
            return

        for c in config.REGISTER_ILLEGAL_CHARACTERS:
            if c in  username:
                self._deny_request(conn, addr, 'Your username contains illegal characters.')
                return

        if len(pass_hash) != 32:
            self._deny_request(conn, addr, 'Your password is invalid. Please try again.')
            return

        # TODO: ip/mac bans
        banned = False
        if banned:
            self._deny_request(conn, addr, 'You are banned.')
            return

        if self.db.get_client(username.lower()) is not None:
            self._deny_request(conn, addr, 'That username is taken.')
            return

        self.db.create_client(username, pass_hash)
        self.log.info('account created %s:%s %s' % (addr[0], addr[1], username))

        buff = [packet.RESP_SUCCESS]
        tcp_write(conn, buff, enc=True)

    def _login(self, conn, addr, data):
        offset = 1

        client_version = read_double(data, offset)
        offset += 8

        username = read_string(data, offset)
        offset += len(username) + 1

        pass_hash = read_string(data, offset)
        offset += len(pass_hash) + 1


        mac = read_string(data, offset)
        offset += len(mac) + 1

        self.log.info('login request %s:%s %s:%s %s' % (addr[0], addr[1], username, pass_hash, mac))

        if client_version != config.COMPATIBLE_GAME_VERSION:
            self._deny_request(conn, addr, 'You are using an incorrect version of the game. Please download version 0.0227')
            return

        if len(username) < 3:
            self._deny_request(conn, addr, 'Your username must be atleast 3 characters long.')
            return

        if len(username) > 12:
            self._deny_request(conn, addr, 'Your username can not be more than 12 characters.')
            return

        for c in config.REGISTER_ILLEGAL_CHARACTERS:
            if c in  username:
                self._deny_request(conn, addr, 'Your username contains illegal characters.')
                return

        if len(pass_hash) != 32:
            self._deny_request(conn, addr, 'Your password is invalid. Please try again.')
            return

        # we're just doing a single read so the lock is probably not strictly necessary
        with self.master.get_game_server().name_to_client as name_to_client:
            account_in_use = name_to_client.get(username.lower()) is not None

        if account_in_use:
            self._deny_request(conn, addr, 'The requested account is currently in use.')
            return

        db_client = self.db.get_client(username.lower())
        if db_client is None:
            self._deny_request(conn, addr, 'Account does not exist.')
            return

        if db_client['banned']:
            self._deny_request(conn, addr, 'You are banned.')
            return

        if db_client['passhash'] != pass_hash:
            self._deny_request(conn, addr, 'Incorrect password.')
            return

        if self.master.get_pending_login(addr[0]):
            self._deny_request(conn, addr, 'A login attempt for this account is already in process. Please wait a moment and try again.')
            return

        client_data = {
            'id': db_client['id'],
            'name': username,#db_client['name'], # in the original game, usernames were not case sensitive. But if you signed in with case changed in your name, people would see it.
            'clan': db_client['clan'],
            'weapon': db_client['weapon_equipped'],
            'hat': db_client['hat_equipped'],
            'admin': db_client['admin_level'],
            'login_timestamp': datetime.now()
        }
        self.master.add_pending_login(addr[0], client_data)

        buff = []
        write_byte(buff, packet.RESP_LOGIN_ACCEPT)
        write_uint(buff, db_client['spawn_x'] * 10)
        write_short(buff, db_client['spawn_y'] * 10)
        write_ushort(buff, db_client['hp']) # start HP
        write_ushort(buff, db_client['mp']) # start MP

        write_byte(buff, db_client['stat_str']) # str
        write_byte(buff, db_client['stat_agi']) # agi
        write_byte(buff, db_client['stat_int']) # int
        write_byte(buff, db_client['stat_vit']) # vit
        write_byte(buff, db_client['int_unknown_1']) # ?? doesn't appear to be used

        write_double(buff, db_client['experience'])
        write_byte(buff, db_client['level']) # level
        write_byte(buff, db_client['admin_level']) # is admin. 250 (0xfa) for admin, any other for not?
        write_ushort(buff, db_client['stat_points']) # stat points
        write_ushort(buff, db_client['int_unknown_2']) # ?? doesn't appear to be used
        write_ushort(buff, db_client['weapon_equipped']) # weapon equipped
        write_ushort(buff, db_client['hat_equipped']) # hat equipped

        write_ushort(buff, db_client['int_unknown_3']) # ?? doesn't appear to be used
        write_ushort(buff, db_client['int_unknown_4']) # ?? doesn't appear to be used
        write_ushort(buff, db_client['int_unknown_5']) # ?? doesn't appear to be used

        # gold
        write_double(buff, db_client['gold'])

        # write num_items and
        items = self.db.get_items(db_client['id'])
        write_byte(buff, len(items))
        for i in range(len(items)):
            write_ushort(buff, items[i])

        list_1 = self.db.get_unknown_list_1(db_client['id'])
        write_ushort(buff, len(list_1))
        for i in range(len(list_1)):
            write_ushort(buff, list_1[i])

        list_2 = self.db.get_unknown_list_2(db_client['id'])
        write_ushort(buff, len(list_2))
        for i in range(len(list_2)):
            write_ushort(buff, list_2[i])

        write_string(buff, db_client['clan'])

        write_byte(buff, datetime.today().hour)

        tcp_write(conn, buff, enc=True)

    def _save(self, conn, addr, data):
        offset = 1

        client_version = read_double(data, offset); offset += 8
        username = read_string(data, offset)
        offset += len(username) + 1
        pass_hash = read_string(data, offset)
        offset += len(pass_hash) + 1

        self.log.info('save request %s:%s %s:%s' % (addr[0], addr[1], username, pass_hash))

        save_data = {}
        save_data['spawn_x'] = int(round(read_int(data, offset) / 10.0)); offset += 4
        save_data['spawn_y'] = int(round(read_short(data, offset) / 10.0)); offset += 2
        save_data['hp'] = read_ushort(data, offset); offset += 2
        save_data['mp'] = read_ushort(data, offset); offset += 2

        save_data['stat_str'] = read_byte(data, offset); offset += 1
        save_data['stat_agi'] = read_byte(data, offset); offset += 1
        save_data['stat_int'] = read_byte(data, offset); offset += 1
        save_data['stat_vit'] = read_byte(data, offset); offset += 1
        save_data['int_unknown_1'] = read_byte(data, offset); offset += 1
        save_data['experience'] = read_double(data, offset); offset += 8
        save_data['level'] = read_byte(data, offset); offset += 1
        save_data['admin_level'] = read_byte(data, offset); offset += 1

        save_data['stat_points'] = read_ushort(data, offset); offset += 2
        save_data['int_unknown_2'] = read_ushort(data, offset); offset += 2
        save_data['weapon_equipped'] = read_ushort(data, offset); offset += 2
        save_data['hat_equipped'] = read_ushort(data, offset); offset += 2
        save_data['int_unknown_3'] = read_ushort(data, offset); offset += 2
        save_data['int_unknown_4'] = read_ushort(data, offset); offset += 2
        save_data['int_unknown_5'] = read_ushort(data, offset); offset += 2
        save_data['gold'] = read_double(data, offset); offset += 8

        save_data['inventory'] = []
        num_items = read_byte(data, offset); offset += 1
        for i in range(num_items):
            save_data['inventory'].append(read_ushort(data, offset))
            offset += 2

        save_data['unknown_list_1'] = []
        num_items = read_ushort(data, offset); offset += 2
        for i in range(num_items):
            save_data['unknown_list_1'].append(read_ushort(data, offset))
            offset += 2

        save_data['unknown_list_2'] = []
        num_items = read_ushort(data, offset); offset += 2
        for i in range(num_items):
            save_data['unknown_list_1'].append(read_ushort(data, offset))
            offset += 2

        if client_version != config.COMPATIBLE_GAME_VERSION:
            self._deny_request(conn, addr, 'Save Error: Incorrect game version.')
            return

        db_client = self.db.get_client(username.lower())
        if db_client is None:
            self._deny_request(conn, addr, 'Save Error: Client not found.')
            return

        if db_client['passhash'] != pass_hash:
            self._deny_request(conn, addr, 'Save Error: Corrupt data packet.')
            return

        try:
            save_data['id'] = db_client['id']
            self.db.save_client(save_data)
        except Exception as e:
            self._deny_request(conn, addr, 'Save Error: Exception occured during save.')
            self.log.error('Saving failed %s' % e)
            import traceback
            traceback.print_exc()
            return

        tcp_write(conn, [packet.RESP_SUCCESS], enc=True)
