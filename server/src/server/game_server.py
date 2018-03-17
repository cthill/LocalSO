from datetime import datetime, timedelta
import logging
import signal
import socket
import sys
import threading
import traceback

import config
from client.client import Client
from event import scheduler
from world.world import World
from net import packet
from net.buffer import *
from util import buff_to_str, LockList, LockDict, acquire_all

class GameServer:
    def __init__(self, interface, port, master):
        self.logger = logging.getLogger('game_svr')

        self.interface = interface
        self.port = port
        self.master = master

        self.world = World(self)

        self.terminated = False

        # mutable data that needs locks
        self.clients = LockList() # Done!
        self.id_to_client = LockDict() # Done!
        self.client_to_id = LockDict() # Done!
        self.name_to_client = LockDict() # Done!

        scheduler.schedule_event_recurring(self._ev_step, 5)

    def __call__(self):
        # create udp server thread
        t = threading.Thread(target=self.udp_server, args=(self.interface, self.port))
        t.start()

        # create wolrd process
        t = threading.Thread(target=self.world)
        t.start()

        # listen on tcp
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.interface, self.port))
        s.listen(1)

        self.logger.info('listening %s:%s' % (self.interface, self.port))

        while not self.terminated:
            conn, addr = s.accept()
            self.logger.info('new connection: %s:%s' % (addr))

            try:
                self._client_accept(conn, addr)
            except Exception as e:
                self.logger.error('Unhandled exception _client_accept %s' % (e))
                traceback.print_exc()

    def udp_server(self, interface, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((interface, port))

        self.logger.info('udp listening %s:%s' % (interface, port))

        while not self.terminated:
            raw_data, addr = s.recvfrom(4096) # read up to 4096 bytes
            data = bytearray(raw_data)
            self.logger.debug('udp message: %s' % buff_to_str(data))

            client_id = read_ushort(data, 1)
            try:
                # we're just doing a single read so the lock is probably not strictly necessary
                with self.id_to_client:
                    client = self.id_to_client.get(client_id)

                if client is not None:
                    client.handle_udp_packet(data)
            except Exception as e:
                self.logger.error('Unhandled exception udp_server %s' % (e))
                traceback.print_exc()

    def _client_accept(self, conn, addr):
        # enable TCP_NODELAY
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        client_dat = self.master.get_pending_login(addr[0])
        with acquire_all(self.clients, self.id_to_client, self.client_to_id, self.name_to_client):
            client_id = client_dat['id']
            new_client = Client(self, self.world, conn, client_id, client_dat)
            self.clients.append(new_client)
            self.id_to_client[client_id] = new_client
            self.client_to_id[new_client] = client_id
            self.name_to_client[client_dat['name'].lower()] = new_client
            new_client.start()

    def client_disconnect(self, client):
        with acquire_all(self.clients, self.id_to_client, self.client_to_id, self.name_to_client):
            client_id = self.client_to_id[client]
            buff = [packet.RESP_CLIENT_DISCONNECT]
            write_ushort(buff, client_id)
            self._broadcast(buff, exclude=client)

            del self.id_to_client[client_id]
            del self.client_to_id[client]
            del self.name_to_client[client.name.lower()]
            self.clients.remove(client)

    def get_num_players(self):
        return len(self.clients)

    # this method acquires a lock on the clients list. So be careful not to call
    # it where deadlocks are possible
    def broadcast(self, data, exclude=None):
        with self.clients:
            self._broadcast(data, exclude)

    def _broadcast(self, data, exclude=None):
        for client in self.clients:
            if client is exclude:
                continue

            client.send_tcp_message(data)

    def _ev_step(self):
        # copy the clients list so that we don't deadlock when calling client.disconnect()
        connected = []
        with self.clients:
            connected = self.clients[:]

        now = datetime.now()
        for client in connected:
            # check server side client timeouts
            if now - client.last_recv_timestamp > timedelta(seconds=config.PLAYER_TIMEOUT):
                try:
                    client.disconnect()
                    self.logger.info('Client %s timeout socket close' % client)
                except:
                    pass
                self.logger.info('Client %s timed out.' % client)
            else:
                # this packet is ignored by the client but will reset the clientside connection timeout
                client.send_tcp_message([packet.MSG_NOP])

        # cleanup pending game server connections
        with self.master.pending_logins:
            to_delete = []
            for key in self.master.pending_logins:
                pending_login = self.master.pending_logins[key]
                if now - pending_login['login_timestamp'] > timedelta(seconds=config.LOGIN_PENDING_TIMEOUT):
                    self.logger.debug('deleting pending login %s %s' % (key, pending_login['name']))
                    to_delete.append(key)

            for key in to_delete:
                del self.master.pending_logins[key]

        # TODO: check if world thread is deadlocked
