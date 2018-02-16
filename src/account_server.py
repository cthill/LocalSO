import datetime as dt
import logging
import socket
import threading
import traceback

from net.buffer import *
from net.socket import tcp_write
from util.util import buff_to_str

# packet headers
MSG_REGISTER = 0x00
MSG_LOGIN = 0x01
MSG_SAVE = 0x03

RESP_ACCEPT = 0x01
RESP_DENY = 0x02
RESP_DENY_WRONG_VERSION = 0x03
RESP_SAVE_SUCCESS = 0x03


class AccountServer:
    def __init__(self, interface, port, master):
        self.interface = interface
        self.port = port
        self.master = master

        self.terminated = False
        self.counter = 0

    def __call__(self):
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
        if header == MSG_REGISTER:
            logging.info('Account server register message')
        elif header == MSG_LOGIN:
            user_len = size - 62

            offset = 1

            client_version = read_double(data, offset)
            offset += 8

            username = read_string(data, offset)
            offset += len(username) + 1

            pass_hash = read_string(data, offset)
            offset += len(pass_hash) + 1


            mac = read_string(data, offset)
            offset += len(pass_hash) + 1

            logging.info('Login user: %s passhash: %s mac: %s' % (username, pass_hash, mac))

            buff = []

            banned = False

            if banned:
                write_byte(buff, RESP_DENY)
                write_string(buff, 'You have been banned.')
            else:
                clan = ''#'clan1'

                client_data = {
                    'id': 0x0000 + self.counter,
                    'name': username,
                    'clan': clan,
                    'hat': 0x20,
                    'weapon': 0x0a,
                    'admin': 0xfa #250 (0xfa) for admin, any other for not?
                }
                self.master.add_pending_game_server_connection(addr[0], client_data)
                self.counter += 1

                write_byte(buff, RESP_ACCEPT)

                write_uint(buff, 0x438 * 10) # spawn x, default is 1080 or 0x438
                #write_short(buff, 0x12C * 10) # spawn y (the client divides this value by 10), default is 300 or 12C, 0x825 is close to ground
                write_short(buff, 0x825 * 10)
                write_ushort(buff, 0x64) # start HP
                write_ushort(buff, 0x64) # start MP

                # these are probably stats (STR, AGI, VIT, INT, stat_points)
                write_byte(buff, 0xff) # str
                write_byte(buff, 0xff) # agi
                write_byte(buff, 0xff) # int
                write_byte(buff, 0xff) # vit
                write_byte(buff, 0x00) # ?? doesn't appear to be used

                # exp
                # write_double(buff, 10000) # 10000
                write_double(buff, 0) # 10000


                # write_byte(buff, 0xff) # level
                write_byte(buff, 0x01) # level
                write_byte(buff, client_data['admin']) # is admin. 250 (0xfa) for admin, any other for not?

                write_ushort(buff, 0x11) # stat points
                write_ushort(buff, 0x00) # ?? doesn't appear to be used
                write_ushort(buff, client_data['weapon']) # weapon equipped

                write_ushort(buff, client_data['hat']) # hat equipped

                write_ushort(buff, 0x0f) # ?? doesn't appear to be used
                write_ushort(buff, 0x16) # ?? doesn't appear to be used
                write_ushort(buff, 0x17) # ?? doesn't appear to be used

                # gold
                write_double(buff, 10000) # 10000


                # write num_items and ids
                items = [0x16, 0x20, 0x30, 0x32, 0x0a, 0x27] # whip and bunny ears and heavens wrath and scotty's axe
                write_byte(buff, len(items))
                for i in range(len(items)):
                    write_ushort(buff, items[i])

                # list size
                write_ushort(buff, 0x00)

                # another list size
                write_ushort(buff, 0x00)

                # list size (num players?)
                # clients = self.master.get_game_server().clients
                # write_ushort(buff, len(clients))
                # for client in clients:
                #     write_ushort(buff, client.id)

                write_string(buff, clan) # clan

                write_byte(buff, dt.datetime.today().hour)

            tcp_write(conn, buff, enc=True)

        elif header == MSG_SAVE:
            tcp_write(conn, [RESP_SAVE_SUCCESS], enc=True)

        else:
            logging.info('Account server got unknown packet %s' % buff_to_str(data))
