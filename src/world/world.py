import logging
import math
import time

import config
from mailbox import mail_header
from net import packet
from bounding_box import BoundingBox
from mailbox import Mailbox
from spawner import MobSpawner
from net.buffer import *
from util import ceildiv

class WorldSection:
    def __init__(self, index):
        self.index = index
        self.x = config.WORLD_SECTION_WIDTH * self.index
        self.solid_blocks = []

    def add_solid_block(self, block):
        self.solid_blocks.append(block)

class World(Mailbox):
    def __init__(self, game_server, event_scheduler):
        super(World, self).__init__()

        self.game_server = game_server
        self.event_scheduler = event_scheduler
        self.solid_blocks = []
        self.sections = []
        self.mob_spawn = []
        self.mobs = {}
        self.section_to_clients = {}
        self.section_to_mobs = {}
        self.active_sections = set()
        self.mob_id_gen_counter = 0
        self.world_step_num = 0

        # create sections. This makes collision detection faster because we only have to check for collision within the section (and adjacent sections)
        for i in range(ceildiv(config.WORLD_WIDTH, config.WORLD_SECTION_WIDTH)):
            sec = WorldSection(i)
            self.sections.append(sec)
            self.section_to_clients[i] = set()
            self.section_to_mobs[i] = set()

        # add the solid blocks to the world
        for d in config.SOLID_BLOCK_DATA:
            x = d['x']
            y = d['y']
            w = d['box_w'] * d['x_scale']
            h = d['box_h'] * d['y_scale']
            bbox = BoundingBox(x, y, w, h)

            section_range = self._find_section_range(bbox)
            for i in range(*section_range):
                self.sections[i].add_solid_block(bbox)

            self.solid_blocks.append(bbox)

        # create the mob spawners
        for i in range(len(config.MOB_SPAWN)):
            spawner_data = config.MOB_SPAWN[i]
            new_spawner = MobSpawner(i, spawner_data, self.game_server, self)
            self.mob_spawn.append(new_spawner)


    def get_event_scheduler(self):
        return self.event_scheduler

    def find_section_index(self, x):
        if x < 0:
            return 0
        elif x > config.WORLD_WIDTH:
            return config.NUM_SECTIONS - 1

        return x // config.WORLD_SECTION_WIDTH

    def _find_section_range(self, bbox):
        origin_section = self.find_section_index(bbox.x)
        section_span = ceildiv((bbox.x % config.WORLD_SECTION_WIDTH) + bbox.w, config.WORLD_SECTION_WIDTH)
        return (origin_section, origin_section + section_span)

    def get_clients_in_section(self, section):
        return self.section_to_clients[section]

    def _update_client_section(self, client, old_section, new_section):
        if old_section in self.section_to_clients:
            self.section_to_clients[old_section].remove(client)
            if len(self.section_to_clients[old_section]) == 0:
                self.active_sections.remove(old_section)

        if new_section in self.section_to_clients:
            self.section_to_clients[new_section].add(client)
            self.active_sections.add(new_section)

    def _update_mob_section(self, mob, old_section, new_section):
        if old_section in self.section_to_mobs:
            self.section_to_mobs[old_section].remove(mob)

        if new_section in self.section_to_mobs:
            self.section_to_mobs[new_section].add(mob)

    def get_active_sections(self):
        return self.active_sections

    def get_local_sections(self, section, section_radius=3):
        if section_radius < 0:
            section_radius = 0
        start = max(section - section_radius, 0)
        end = min(section + section_radius + 1, config.NUM_SECTIONS)
        return range(start, end)

    def __call__(self):
        target_frame_interval = 1.0/config.ROOM_SPEED
        while True:
            step_start_timestamp = time.time()

            self._step()

            # compute time to next frame
            now = time.time()
            time_to_wait = target_frame_interval - (now - step_start_timestamp)
            if time_to_wait < 0:
                time_to_wait = 0
            time.sleep(time_to_wait)

    def _process_mail_messages(self):
        # check the mailbox
        mail_messages = self._get_mail_messages()
        for mail_message in mail_messages:
            header = mail_message[0]
            payload = mail_message[1]

            if header == mail_header.MSG_HIT_MOB:
                mob_id = payload[0]
                if mob_id in self.mobs:
                    self.mobs[mob_id].hit(*payload[1:])
            elif header == mail_header.MSG_ADD_MOB:
                mob = payload
                self.mobs[mob.id] = mob

            elif header == mail_header.MSG_DELETE_MOB:
                self._remove_mob(payload)

            elif header == mail_header.UPDATE_MOB_SECTION:
                self._update_mob_section(*payload)

            elif header == mail_header.UPDATE_CLIENT_SECTION:
                self._update_client_section(*payload)

    def _step(self):

        self._process_mail_messages()

        # run the spawners
        for spawner in self.mob_spawn:
            spawner.step()

        # find all sections in which mobs should be stepped
        active_sections_expanded = set()
        for section_index in self.active_sections:
            active_sections_expanded.update(self.get_local_sections(section_index))

        # step the mobs
        to_remove = set()
        for mob_id in self.mobs:
            mob = self.mobs[mob_id]
            if mob.dead:
                to_remove.add(mob)
                if mob.broadcast_death:
                    buff = [packet.RESP_MOB_DEATH]
                    write_uint(buff, mob.id)
                    self.game_server.broadcast_local(buff, mob.section)
            elif mob.section in active_sections_expanded:
                # mob.step() is an expensive call, so we only want to do it in the active world sections (where the players are)
                mob.step()

        # remove dead mobs
        for mob in to_remove:
            self._remove_mob(mob)

        # broadcast mob updates
        # first find each client
        for client in self.game_server.clients:
            # then get the client's nearby sections
            local_sections = self.get_local_sections(client.section)
            # if self.world_step_num % 1 == 0:
            for section in local_sections:
                # find all the mobs in the nearby section
                for mob in self.section_to_mobs.get(section, []):
                    # send that client the mob status
                    if mob.write_packet_this_step:
                        client.send_tcp_message(mob.get_status_packet())

            # interpolate the client's state
            client.interpolate_state()

        self.world_step_num += 1

    def solid_block_at(self, bbox):
        section_range = self._find_section_range(bbox)
        for i in range(*section_range):
            for solid_block in self.sections[i].solid_blocks:
                if solid_block.check_collision(bbox):
                    return True

        return False

    def get_solid_blocks_at(self, bbox):
        touching = []
        section_range = self._find_section_range(bbox)
        for i in range(*section_range):
            for solid_block in self.sections[i].solid_blocks:
                if solid_block.check_collision(bbox):
                    touching.append(solid_block)

        return touching

    def find_player_nearest(self, x, section_radius=3):
        section = self.find_section_index(x)
        sections_to_search = self.get_local_sections(section, section_radius=section_radius)
        players_found = []
        for section in sections_to_search:
            players_found.extend(self.section_to_clients[section])

        nearest = None
        nearest_dist = config.WORLD_WIDTH
        for player in players_found:
            if abs(player.x - x) < nearest_dist:
                nearest = player
                nearest_dist = abs(player.x - x)

        return nearest

    def generate_mob_id(self):
        new_id = (0b111111 << 10) | (self.mob_id_gen_counter % 1024)
        self.mob_id_gen_counter += 1
        return new_id

    def _remove_mob(self, mob):
        if mob.id in self.mobs:
            del self.mobs[mob.id]
        if mob.section in self.section_to_mobs:
            self.section_to_mobs[mob.section].remove(mob)
        if mob.spawner is not None:
            mob.spawner.mob_death(mob)

    def client_disconnect(self, client):
        if client.section in self.section_to_clients:
            self.section_to_clients[client.section].remove(client)
