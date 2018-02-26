import socket
import threading
import logging
import signal
import sys

import config
from db.db import SQLiteDB
from server.web_server import run as web_server_run
from server.account_server import AccountServer
from server.game_server import GameServer

class StickOnlineMaster:

    def __init__(self):
        self.pending_game_server_connections = {}
        self.db = SQLiteDB(config.SQLITE_DB_FILE)

    def start_server(self):
        self.account_server = AccountServer(config.INTERFACE, config.PORT_ACCOUNT, self.db, self)
        t = threading.Thread(target=self.account_server)
        t.start()

        self.game_server = GameServer(config.INTERFACE, config.PORT_GAME, self)
        t = threading.Thread(target=self.game_server)
        t.start()

    def add_pending_game_server_connection(self, ip, data):
        self.pending_game_server_connections[ip] = data
        logging.info('added pending conn %s' % (ip))

    def get_pending_game_server_connection(self, ip):
        if ip in self.pending_game_server_connections:
            dat = self.pending_game_server_connections[ip]
            del self.pending_game_server_connections[ip]
            return dat

        return None

    def get_game_server(self):
        return self.game_server

    def get_account_server(self):
        return self.account_server

    def stop(self):
        # dc all the clients from the game server
        for client in self.game_server.clients:
            try:
                client.socket.close()
            except Exception as e:
                logging.info('Failed to disconnect client %s: %s' % (client, e))

        self.game_server.terminated = True
        self.account_server.terminated = True

if __name__ == '__main__':
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    logging.info('LocalSO v0.1')

    m_stick_online_master = StickOnlineMaster()
    m_stick_online_master.start_server()

    t = threading.Thread(target=web_server_run, args=(config.INTERFACE_HTTP, config.PORT_HTTP))
    t.start()
