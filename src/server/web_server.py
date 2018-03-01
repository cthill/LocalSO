import base64
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import SocketServer

import config

# this is jank but whatever
master_obj = None

class WebServer(BaseHTTPRequestHandler):
    def _set_headers(self, status_code, content_type='text/html', content_length=0):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        if content_length != 0:
            self.send_header('Content-Length', str(content_length))
        self.end_headers()

    def do_GET(self):
        try:
            if self.path == '/status':
                self._set_headers(200, content_type='application/json')

                mgs = master_obj.get_game_server()
                mas = master_obj.get_account_server()
                status = 'online'
                players = len(mgs.clients)
                if mgs.terminated or mas.terminated:
                    players = 0
                    status = 'offline'

                self.wfile.write(json.dumps({
                    'status': status,
                    'players': players
                }))

            elif self.path == '/download/v2/Announcements.txt':
                self._set_headers(200)
                self.wfile.write(config.MENU_MOTD)

            elif self.path == '/download/v2/UpdateList.sul':
                resp_str = 'StickOnline.exe\n8eb7152684fd3a32d972e446cff4b9d0\nResources.sor\n57676b88206b77b251d352c941ac9e7f\nReadme.txt\na8d2a493f0caf171b9e51f82bbe2a8e0'
                self._set_headers(200, content_type='text/plain', content_length=len(resp_str))
                self.wfile.write(resp_str)

            elif self.path == '/download/v2/Resources.sor':
                self.send_file(config.GAME_BIN_DIR + '/Resources.sor')

            elif self.path == '/download/v2/StickOnline.exe':
                self.send_file(config.GAME_BIN_DIR + '/StickOnline.exe')

            elif self.path == '/download/v2/Readme.txt':
                self.send_file(config.GAME_BIN_DIR + '/Readme.txt')

            elif self.path.startswith('/boards/index.php?action=keepalive'):
                self._set_headers(200, content_type='image/gif')
                self.wfile.write(base64.b64decode('R0lGODlhAQABAIAAAAAAAAAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='))

            else:
                self._set_headers(404)
                self.wfile.write('Not found.')
                logging.info('Unknown http path: %s' % self.path)
        except Exception as e:
            logging.info('Error handling http request %s' % e)
            self._set_headers(500)
            self.wfile.write('Internal server error.')

    def do_HEAD(self):
        self._set_headers(200)

    def send_file(self, filename):
        file_bytes = open(filename, 'rb').read()
        self._set_headers(200, content_type='text/plain', content_length=len(file_bytes))
        self.wfile.write(file_bytes)

class StickOnlineHTTPServer:
    def __init__(self, interface, port, master):
        self.interface = interface
        self.port = port

        # this is jank but whatever
        self.master = master
        global master_obj
        master_obj = self.master

        self.http_server = HTTPServer((self.interface, self.port), WebServer)

    def __call__(self):
        logging.info('http server listening on %s:%s' % (self.interface, self.port))
        self.http_server.serve_forever()

    def stop(self):
        self.http_server.shutdown()
