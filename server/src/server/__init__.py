import logging
import threading
import time

import config
import db.sqlite
import server.account_server
import server.game_server
import server.web_server

logger = logging.getLogger('server')

class StickOnlineServer:

    def __init__(self):
        self.running = False
        self.db = db.sqlite.SQLiteDB(config.SQLITE_DB_FILE, self)
        self.web_server = server.web_server.WebServer(config.INTERFACE_HTTP, config.PORT_HTTP, self)
        self.game_server = server.game_server.GameServer(config.INTERFACE, config.PORT_GAME, self)
        self.account_server = server.account_server.AccountServer(config.INTERFACE, config.PORT_ACCOUNT, self)

    def start(self):
        threading.Thread(target=self.web_server).start()
        threading.Thread(target=self.account_server).start()
        threading.Thread(target=self.game_server).start()
        self.running = True

    def stop(self):
        self.web_server.stop()

        # calling client.disconnect() will lock the game_server client set.
        # so we need to copy it
        with self.game_server.clients as clients:
            clients_online = clients[:]

        # dc all the clients from the game server
        for client in clients_online:
            try:
                client.disconnect()
            except Exception as e:
                logger.info('Failed to disconnect client %s: %s', client, e)

        # sleep for 5 seconds so all the clients have time to save
        time.sleep(5)

        self.game_server.terminated = True
        self.account_server.terminated = True
        self.running = False
