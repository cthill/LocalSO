import threading
import logging
import os.path
import time

import config
from db.db import SQLiteDB
from server.web_server import StickOnlineHTTPServer
from server.account_server import AccountServer
from server.game_server import GameServer

class StickOnlineMaster:

    def __init__(self):
        self.pending_game_server_connections = {}
        self.db = SQLiteDB(config.SQLITE_DB_FILE)

    def start(self):
        self.webserver = StickOnlineHTTPServer(config.INTERFACE_HTTP, config.PORT_HTTP, self)
        t = threading.Thread(target=self.webserver)
        t.start()

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
        self.webserver.stop()


        # calling client.disconnect() will lock the game_server client set.
        # so we need to copy it
        with self.game_server.clients as clients:
            clients_online = clients[:]

        # dc all the clients from the game server
        for client in clients_online:
            try:
                client.disconnect()
            except Exception as e:
                logging.info('Failed to disconnect client %s: %s' % (client, e))

        self.game_server.terminated = True
        self.account_server.terminated = True

if __name__ == '__main__':
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    logging.info('LocalSO v1.0')

    files = ['Resources.sor', 'StickOnline.exe', 'Readme.txt']
    for filename in files:
        if not os.path.isfile(config.GAME_BIN_DIR + '/' + filename):
            logging.warn('Missing game file %s. Please place %s in %s' % ( config.GAME_BIN_DIR + '/' + filename, filename, config.GAME_BIN_DIR))

    # start the servers
    m_stick_online_master = StickOnlineMaster()
    m_stick_online_master.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info('Shutting down...')
        m_stick_online_master.stop()
        time.sleep(5)
        os._exit(0)
