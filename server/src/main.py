import logging
import os.path
import time

import server
from util import SigHandler

if __name__ == '__main__':
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    logging.info('LocalSO v1.3')

    server = server.StickOnlineServer()
    server.start()

    exit_code = 0
    try:
        handler = SigHandler()
        while True:
            time.sleep(1)
            if handler.caught_signal:
                logging.info('Caught signal...')
                break
            if not server.game_server.world.running:
                logging.info('World thread died...')
                exit_code = 1
                break
    except KeyboardInterrupt:
        logging.info('Caught KeyboardInterrupt...')
    finally:
        try:
            logging.info('Shutting down...')
            server.stop()
        finally:
            os._exit(exit_code)
