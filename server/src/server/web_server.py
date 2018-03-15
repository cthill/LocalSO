import base64
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import SocketServer

import config
from event import scheduler
from util import LockList

log = logging.getLogger('web_svr')
top_players = LockList()

class WebServer(BaseHTTPRequestHandler):
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

                game_svr = master_obj.get_game_server()
                acc_svr = master_obj.get_account_server()
                status = 'online'
                players = game_svr.get_num_players()
                if game_svr.terminated or acc_svr.terminated or not game_svr.world.running:
                    players = 0
                    status = 'offline'

                self.wfile.write(json.dumps({
                    'status': status,
                    'players': players
                }))

            elif self.path == '/players':
                with top_players:
                    self._set_headers(200, content_type='application/json')

                    # we're just doing a single read so the lock is probably not strictly necessary
                    with master_obj.get_game_server().name_to_client as name_to_client:
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
                log.info('Unknown http path: %s' % self.path)
        except Exception as e:
            log.error('Error handling http request %s' % e)
            self._set_headers(500)
            self.wfile.write('Internal server error.')

    def do_HEAD(self):
        self._set_headers(200)

    def send_file(self, filename):
        with open(filename, 'rb') as f:
            file_bytes = f.read()
            self._set_headers(200, content_type='text/plain', content_length=len(file_bytes))
            self.wfile.write(file_bytes)


def upadte_top_players():
    global top_players
    with top_players:
        del top_players[:]
        top_players += db_ref.get_top_clients(include_admin=True)

def serve(master):
    global master_obj
    global db_ref
    global http_server
    
    master_obj = master
    db_ref = master.db

    # setup top_players update job
    # update top_players list every five minutes
    scheduler.schedule_event_recurring(upadte_top_players, 60 * 5)
    upadte_top_players()

    http_server = HTTPServer((config.INTERFACE_HTTP, config.PORT_HTTP), WebServer)
    log.info('listening on %s:%s' % (config.INTERFACE_HTTP, config.PORT_HTTP))
    http_server.serve_forever()

def stop():
    http_server.shutdown()
