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
        self.interface = interface
        self.port = port
        self.db = db
        self.master = master

        self.terminated = False
        self.counter = 0

    def __call__(self):
        # listen tcp
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.interface, self.port))
        s.listen(1)

        logging.info('Account server listening %s:%s' % (self.interface, self.port))

        while not self.terminated:
            conn, addr = s.accept()
            logging.info('Account server new connection: %s:%s' % (addr))
            t = threading.Thread(target=self._account_server_client, args=(conn, addr))
            t.start()

    def _account_server_client(self, conn, addr):
        try:
            while True:
                size = bytearray(conn.recv(2))
                if not size:
                    break
                size_int = read_short(size, 0)
                self._handle_packet(conn, addr, size_int)
        except Exception as e:
            logging.info('Unhandled exception in client %s thread %s' % (self, e))
            traceback.print_exc()
        finally:
            conn.close()
            logging.info('Account server client %s:%s disconnected' % addr)

    def _handle_packet(self, conn, addr, size):
        raw_data = conn.recv(size)
        data = bytearray(raw_data)
        enc_dec_buffer(data)

        logging.info("Account server client %s:%s data: %s" % (addr[0], addr[1], buff_to_str(data)))

        header = data[0]
        if header == packet.MSG_REGISTER:
            self._register(conn, addr, data)
        elif header == packet.MSG_LOGIN:
            self._login(conn, addr, data)
        elif header == packet.MSG_SAVE:
            self._save(conn, addr, data)
        else:
            logging.info('Account server unknown packet %s' % buff_to_str(data))

    def _deny_request(self, conn, reason):
        buff = [packet.RESP_DENY_REQUEST]
        write_string(buff, reason)
        tcp_write(conn, buff, enc=True)

    def _register(self, conn, addr, data):
        '''

        config.REGISTER_CLOSED
        config.COMPATIBLE_GAME_VERSION
        user >= 3
        user <= 12
        config.REGISTER_ILLEGAL_CHARACTERS
        passhash = 32
        banned
        '''

        offset = 1

        client_version = read_double(data, offset)
        offset += 8

        username = read_string(data, offset)
        offset += len(username) + 1

        pass_hash = read_string(data, offset)
        offset += len(pass_hash) + 1

        mac = read_string(data, offset)
        offset += len(mac) + 1

        logging.info("Register request %s:%s %s" % (username, pass_hash, mac))

        if config.REGISTER_CLOSED:
            self._deny_request(conn, "Registration is currently closed.")
            return

        if client_version != config.COMPATIBLE_GAME_VERSION:
            self._deny_request(conn, "You are using an incorrect version of the game. Please download version 0.0227")
            return

        if len(username) < 3:
            self._deny_request(conn, "Your username must be atleast 3 characters long.")
            return

        if len(username) > 12:
            self._deny_request(conn, "Your username can not be more than 12 characters.")
            return

        for c in config.REGISTER_ILLEGAL_CHARACTERS:
            if c in  username:
                self._deny_request(conn, "Your username contains illegal characters.")
                return

        if len(pass_hash) != 32:
            self._deny_request(conn, "Your password is invalid. Please try again.")
            return

        # TODO: ip bans
        banned = False
        if banned:
            self._deny_request(conn, "You are banned.")
            return

        if self.db.get_client(username) is not None:
            self._deny_request(conn, "That username is taken.")
            return


        self.db.create_client(username, pass_hash)

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

        logging.info('Login request %s:%s %s' % (username, pass_hash, mac))

        if client_version != config.COMPATIBLE_GAME_VERSION:
            self._deny_request(conn, "You are using an incorrect version of the game. Please download version 0.0227")
            return

        if len(username) < 3:
            self._deny_request(conn, "Your username must be atleast 3 characters long.")
            return

        if len(username) > 12:
            self._deny_request(conn, "Your username can not be more than 12 characters.")
            return

        for c in config.REGISTER_ILLEGAL_CHARACTERS:
            if c in  username:
                self._deny_request(conn, "Your username contains illegal characters.")
                return

        if len(pass_hash) != 32:
            self._deny_request(conn, "Your password is invalid. Please try again.")
            return

        if self.master.get_game_server().name_to_client.get(username) is not None:
            self._deny_request(conn, "The requested account is currently in use.")
            return

        db_client = self.db.get_client(username)
        if db_client is None:
            self._deny_request(conn, "Account does not exist.")
            return

        if db_client['banned']:
            self._deny_request(conn, "You are banned.")
            return

        if db_client['passhash'] != pass_hash:
            self._deny_request(conn, "Incorrect password.")
            return


        print db_client
        client_data = {
            'id': db_client['id'],
            'name': db_client['name'],
            'clan': db_client['clan'],
            'weapon': db_client['weapon_equipped'],
            'hat': db_client['hat_equipped'],
            'admin': db_client['admin_level'],
            'login_timestamp': datetime.now()
        }
        self.master.add_pending_game_server_connection(addr[0], client_data)

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
        #items = [0x16, 0x20, 0x30, 0x32, 0x0a, 0x27] # whip and bunny ears and heavens wrath and scotty's axe
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



        # buff = []
        # clan = ''#'clan1'
        #
        # client_data = {
        #     'id': 0x0000 + self.counter,
        #     'name': username,
        #     'clan': clan,
        #     'hat': 0x20,
        #     'weapon': 0x0a,
        #     'admin': 0xfa #250 (0xfa) for admin, any other for not?
        # }
        # self.master.add_pending_game_server_connection(addr[0], client_data)
        # self.counter += 1
        #
        # write_byte(buff, packet.RESP_ACCEPT)
        #
        # write_uint(buff, 0x438 * 10) # spawn x, default is 1080 or 0x438
        # #write_short(buff, 0x12C * 10) # spawn y (the client divides this value by 10), default is 300 or 12C, 0x825 is close to ground
        # write_short(buff, 0x825 * 10)
        # write_ushort(buff, 0x320) # start HP
        # write_ushort(buff, 0x320) # start MP
        #
        # # these are probably stats (STR, AGI, VIT, INT, stat_points)
        # write_byte(buff, 0xff) # str
        # write_byte(buff, 0xff) # agi
        # write_byte(buff, 0xff) # int
        # write_byte(buff, 0xff) # vit
        # write_byte(buff, 0x00) # ?? doesn't appear to be used
        #
        # # exp
        # # write_double(buff, 10000) # 10000
        # write_double(buff, 0) # 10000
        #
        #
        # # write_byte(buff, 0xff) # level
        # write_byte(buff, 0x01) # level
        # write_byte(buff, client_data['admin']) # is admin. 250 (0xfa) for admin, any other for not?
        #
        # write_ushort(buff, 0x11) # stat points
        # write_ushort(buff, 0x00) # ?? doesn't appear to be used
        # write_ushort(buff, client_data['weapon']) # weapon equipped
        #
        # write_ushort(buff, client_data['hat']) # hat equipped
        #
        # write_ushort(buff, 0x0f) # ?? doesn't appear to be used
        # write_ushort(buff, 0x16) # ?? doesn't appear to be used
        # write_ushort(buff, 0x17) # ?? doesn't appear to be used
        #
        # # gold
        # write_double(buff, 10000) # 10000
        #
        #
        # # write num_items and ids
        # items = [0x16, 0x20, 0x30, 0x32, 0x0a, 0x27] # whip and bunny ears and heavens wrath and scotty's axe
        # write_byte(buff, len(items))
        # for i in range(len(items)):
        #     write_ushort(buff, items[i])
        #
        # # list size
        # write_ushort(buff, 0x00)
        # # another list size
        # write_ushort(buff, 0x00)
        # write_string(buff, clan) # clan
        # write_byte(buff, datetime.today().hour)


        tcp_write(conn, buff, enc=True)

    def _save(self, conn, addr, data):
        offset = 1

        client_version = read_double(data, offset); offset += 8
        username = read_string(data, offset)
        offset += len(username) + 1
        pass_hash = read_string(data, offset)
        offset += len(pass_hash) + 1

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
            self._deny_request(conn, "Save Error: Incorrect game version.")
            return

        db_client = self.db.get_client(username)
        if db_client is None:
            self._deny_request(conn, "Save Error: Client not found.")
            return

        if db_client['passhash'] != pass_hash:
            self._deny_request(conn, "Save Error: Corrupt data packet.")
            return

        try:
            save_data['id'] = db_client['id']
            self.db.save_client(save_data)
        except Exception as e:
            self._deny_request(conn, "Save Error: Exception occured during save.")
            logging.error('Saving failed %s' % e)
            import traceback
            traceback.print_exc()
            return

        tcp_write(conn, [packet.RESP_SUCCESS], enc=True)
