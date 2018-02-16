import base64
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import logging
import SocketServer

import config

class WebServer(BaseHTTPRequestHandler):
    def _set_headers(self, status_code):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        if self.path == '/download/v2/Announcements.txt':
            self._set_headers(200)
            self.wfile.write(config.MENU_MOTD)

        elif self.path == '/download/v2/UpdateList.sul':
            self._set_headers(200)
            self.wfile.write('StickOnline.exe\n8eb7152684fd3a32d972e446cff4b9d0\nResources.sor\n57676b88206b77b251d352c941ac9e7f\nReadme.txt\na8d2a493f0caf171b9e51f82bbe2a8e0')

        elif self.path.startswith('/boards/index.php?action=keepalive'):
            self.send_response(200)
            self.send_header('Content-type', 'image/gif')
            self.end_headers()
            self.wfile.write(base64.b64decode('R0lGODlhAQABAIAAAAAAAAAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='))

        else:
            self._set_headers(404)
            self.wfile.write('Not found.')
            logging.info('Unknown http path: %s' % self.path)

    def do_HEAD(self):
        self._set_headers(200)

def run(interface, port):
    http_server = HTTPServer((interface, port), WebServer)
    logging.info('http server listening on %s:%s' % (interface, port))
    http_server.serve_forever()
