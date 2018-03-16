import threading
import logging
import os.path
import signal
import time

import config
from db.db import SQLiteDB
from server import web_server
from server.account_server import AccountServer
from server.game_server import GameServer
from util import LockDict

class StickOnlineMaster:
    def __init__(self):
        self.pending_game_server_connections = LockDict()
        self.db = SQLiteDB(config.SQLITE_DB_FILE)
        self.account_server = AccountServer(config.INTERFACE, config.PORT_ACCOUNT, self.db, self)
        self.game_server = GameServer(config.INTERFACE, config.PORT_GAME, self)

    def start(self):
        threading.Thread(target=web_server.serve, args=(self,)).start()
        threading.Thread(target=self.account_server).start()
        threading.Thread(target=self.game_server).start()

    def add_pending_game_server_connection(self, ip, data):
        with self.pending_game_server_connections:
            self.pending_game_server_connections[ip] = data

    def get_pending_game_server_connection(self, ip):
        with self.pending_game_server_connections:
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
        web_server.stop()

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

        # sleep for 5 seconds so all the clients have time to save
        time.sleep(5)

        self.game_server.terminated = True
        self.account_server.terminated = True


class SigHandler:
    def __init__(self):
        self.caught_signal = False
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum, frame):
        self.caught_signal = True


if __name__ == '__main__':
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    logging.info('LocalSO v1.2')

    files = ['Resources.sor', 'StickOnline.exe', 'Readme.txt']
    for filename in files:
        if not os.path.isfile(config.GAME_BIN_DIR + '/' + filename):
            logging.warn('Missing game file %s. Please place %s in %s' % ( config.GAME_BIN_DIR + '/' + filename, filename, config.GAME_BIN_DIR))

    # start the servers
    m_stick_online_master = StickOnlineMaster()
    m_stick_online_master.start()

    try:
        handler = SigHandler()
        while True:
            time.sleep(1)
            if handler.caught_signal:
                logging.info('Shutting down...')
                break
    except KeyboardInterrupt:
        logging.info('Shutting down...')
    finally:
        try:
            m_stick_online_master.stop()
        finally:
            os._exit(0)
