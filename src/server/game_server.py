from datetime import datetime, timedelta
import logging
import signal
import socket
import sys
import threading

import config
from client.client import Client
from event import EventScheduler
from world.world import World
from net import packet
from net.buffer import *
from util import buff_to_str

class GameServer:
    def __init__(self, interface, port, master):
        self.log = logging.getLogger('game_svr')

        self.interface = interface
        self.port = port
        self.master = master

        self.event_scheduler = EventScheduler()
        self.world = World(self, self.event_scheduler)

        self.terminated = False
        self.clients = []
        self.id_to_client = {}
        self.client_to_id = {}
        self.name_to_client = {}

        self.event_scheduler.schedule_event_recurring(self.ev_ping_all_clients, 5)
        self.counter = 0

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

        self.log.info('listening %s:%s' % (self.interface, self.port))

        while not self.terminated:
            conn, addr = s.accept()
            self.log.info('new connection: %s:%s' % (addr))
            self._client_accept(conn, addr)

    def udp_server(self, interface, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((interface, port))

        self.log.info('udp listening %s:%s' % (interface, port))

        while not self.terminated:
            raw_data, addr = s.recvfrom(1024) # read up to 1024 bytes
            data = bytearray(raw_data)
            client_id = read_ushort(data, 1)
            if client_id in self.id_to_client:
                self.id_to_client[client_id].handle_udp_packet(data)

            self.log.debug('udp message: %s' % buff_to_str(data))

    def _client_accept(self, conn, addr):
        client_dat = self.master.get_pending_game_server_connection(addr[0])
        if client_dat is None:
            conn.close()
            return

        client_id = client_dat['id']
        new_client = Client(self, self.world, conn, client_id, client_dat)
        self.clients.append(new_client)
        self.id_to_client[client_id] = new_client
        self.client_to_id[new_client] = client_id
        self.name_to_client[client_dat['name']] = new_client
        new_client.start()

    def client_disconnect(self, client):
        client_id = self.client_to_id[client]

        buff = [packet.RESP_CLIENT_DISCONNECT]
        write_ushort(buff, client_id)
        self.broadcast(buff, exclude=client)

        del self.id_to_client[client_id]
        del self.client_to_id[client]
        del self.name_to_client[client.name]
        self.clients.remove(client)

    def get_num_players(self):
        return len(self.clients)

    def broadcast(self, data, exclude=None):
        for client in self.clients:
            if client is exclude:
                continue

            client.send_tcp_message(data)

    def broadcast_multiple(self, data, exclude=None):
        for client in self.clients:
            if client is exclude:
                continue

            for d in data:
                client.send_tcp_message(d)

    def broadcast_local(self, data, section, exclude=None):
        for i in self.world.get_local_sections(section):
            section_clients = self.world.get_clients_in_section(i)
            for client in section_clients:
                if client is exclude:
                    continue

                client.send_tcp_message(data)

    def broadcast_multiple_local(self, data, section, exclude=None):
        for i in self.world.get_local_sections(section):
            section_clients = self.world.get_clients_in_section(i)
            for client in section_clients:
                if client is exclude:
                    continue

                for d in data:
                    client.send_tcp_message(d)

    def ev_ping_all_clients(self):
        buff = [packet.MSG_NOP] # this packet is ignored by the client (but will reset the connection timeout)
        self.broadcast(buff)

        # check client timeouts
        now = datetime.now()
        for client in self.clients:
            if now - client.last_recv_timestamp > timedelta(seconds=config.PLAYER_TIMEOUT):
                client.terminated = True
                try:
                    client.socket.close()
                except:
                    pass
                self.log.info('Client %s timed out.' % client)

    def get_clients(self):
        return self.clients
