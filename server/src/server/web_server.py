from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import os
from threading import Lock

import config
from event import scheduler

logger = logging.getLogger('web_svr')
m_stick_online_server = None
top_players = []
top_players_lock = Lock()

class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code, content_type='text/plain', content_length=0):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        if content_length != 0:
            self.send_header('Content-Length', str(content_length))
        self.end_headers()

    def do_GET(self):
        try:
            if self.path == '/status':
                self._set_headers(200, content_type='application/json')

                status = 'online'
                players = m_stick_online_server.game_server.get_num_players()
                if m_stick_online_server.game_server.terminated or m_stick_online_server.account_server.terminated or not m_stick_online_server.game_server.world.running:
                    players = 0
                    status = 'offline'

                self.wfile.write(json.dumps({
                    'status': status,
                    'players': players
                }))

            elif self.path == '/players':
                with top_players_lock:
                    self._set_headers(200, content_type='application/json')

                    # we're just doing a single read so the lock is probably not strictly necessary
                    with m_stick_online_server.game_server.name_to_client as name_to_client:
                        for player in top_players:
                            player['online'] = name_to_client.get(player['name']) is not None

                    self.wfile.write(json.dumps({
                        'players': top_players
                    }))

            elif self.path == '/download/v2/Announcements.txt':
                self._set_headers(200, content_length=len(config.MENU_MOTD))
                self.wfile.write(config.MENU_MOTD)

            elif self.path == '/download/v2/UpdateList.sul':
                resp_str = 'StickOnline.exe\n8eb7152684fd3a32d972e446cff4b9d0\nResources.sor\n57676b88206b77b251d352c941ac9e7f\nReadme.txt\na8d2a493f0caf171b9e51f82bbe2a8e0'
                self._set_headers(200, content_length=len(resp_str))
                self.wfile.write(resp_str)

            elif self.path == '/download/v2/Resources.sor':
                self.send_file(config.GAME_BIN_DIR + '/Resources.sor')

            elif self.path == '/download/v2/StickOnline.exe':
                self.send_file(config.GAME_BIN_DIR + '/StickOnline.exe')

            elif self.path == '/download/v2/Readme.txt':
                self.send_file(config.GAME_BIN_DIR + '/Readme.txt')

            else:
                self._set_headers(404, content_type='text/html')
                self.wfile.write('Error: not found. If you are trying to connect to www.stick-online.com, please edit your hosts file and try again.')
                logger.info('Unknown http path: %s' % self.path)
        except Exception as e:
            logger.error('Error handling http request %s' % e)
            self._set_headers(500)
            self.wfile.write('Internal server error.')

    def do_HEAD(self):
        self._set_headers(200)

    def send_file(self, filename):
        with open(filename, 'rb') as f:
            file_bytes = f.read()
            self._set_headers(200, content_type='text/plain', content_length=len(file_bytes))
            self.wfile.write(file_bytes)

class WebServer:
    def __init__(self, interface, port, stick_online_server):
        self.interface = interface
        self.port = port
        self.stick_online_server = stick_online_server
        global m_stick_online_server
        m_stick_online_server = stick_online_server

        self.http_server = HTTPServer((self.interface, self.port), RequestHandler)

        files = ['Resources.sor', 'StickOnline.exe', 'Readme.txt']
        for filename in files:
            if not os.path.isfile(config.GAME_BIN_DIR + '/' + filename):
                logger.warn('Missing game file %s. Please place %s in %s' % ( config.GAME_BIN_DIR + '/' + filename, filename, config.GAME_BIN_DIR))

    def __call__(self):
        # setup top_players update job
        # update top_players list every five minutes
        scheduler.schedule_event_recurring(self.upadte_top_players, 60 * 5)
        self.upadte_top_players()

        logger.info('listening on %s:%s' % (self.interface, self.port))
        self.http_server.serve_forever()

    def upadte_top_players(self):
        global top_players, top_players_lock
        with top_players_lock:
            top_players = self.stick_online_server.db.get_top_clients(include_admin=True)

    def stop(self):
        self.http_server.shutdown()
