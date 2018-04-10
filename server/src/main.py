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
            server.stop()
        finally:
            os._exit(0)
