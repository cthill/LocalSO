import logging
import math
import time
import traceback
from datetime import datetime

import config
from mailbox import mail_header
from net import packet
from bounding_box import BoundingBox
from mailbox import Mailbox
from mob import Mob
from spawner import MobSpawner, ClientMobSpawner
from net.buffer import *
from util import ceildiv, LockDict, LockSet, acquire_all

class WorldSection:
    def __init__(self, index):
        self.index = index
        self.x = config.WORLD_SECTION_WIDTH * self.index
        self.solid_blocks = []
        self.jump_through_blocks = []

    def add_solid_block(self, block):
        self.solid_blocks.append(block)

    def add_jump_through_block(self, block):
        self.jump_through_blocks.append(block)


class World(Mailbox):
    def __init__(self, game_server):
        super(World, self).__init__()

        self.logger = logging.getLogger('world')

        self.running = True
        self.game_server = game_server

        # read only data that does not need locks
        self.solid_blocks = []
        self.jump_through_blocks = []
        self.sections = []
        self.mob_spawn = []
        self.events = []

        # mutable data that needs locks
        self.mobs = LockDict()
        self.section_to_clients = LockDict()
        self.section_to_mobs = LockDict()
        self.active_sections = LockSet()
        self.client_mob_spawn = LockDict()

        self.mob_id_gen_counter = 0
        self.world_step_num = 0
        self.world_step_tstamp = time.time()

        # create sections. This makes collision detection faster because we only
        # have to check for collision within the section (and adjacent sections)
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

        for d in config.JUMP_THROUGH_BLOCK_DATA:
            x = d['x']
            y = d['y']
            w = d['box_w'] * d['x_scale']
            h = d['box_h'] * d['y_scale']
            bbox = BoundingBox(x, y, w, h)

            section_range = self._find_section_range(bbox)
            for i in range(*section_range):
                self.sections[i].add_jump_through_block(bbox)

            self.jump_through_blocks.append(bbox)

        # create the mob spawners
        spawner_id = 0
        for spawner_data in config.MOB_SPAWN:
            self.mob_spawn.append(MobSpawner(spawner_id, spawner_data, self.game_server, self))
            spawner_id += 1

        # create the event mob spawners
        for event_data in config.EVENTS:
            event = {
                'name': event_data['name'],
                'start_month': event_data['start_month'],
                'start_day': event_data['start_day'],
                'end_month': event_data['end_month'],
                'end_day': event_data['end_day'],
                'mob_spawn': []
            }
            for spawner_data in event_data['mob_spawn']:
                event['mob_spawn'].append(MobSpawner(spawner_id, spawner_data, self.game_server, self))
                spawner_id += 1
            self.events.append(event)

    def find_section_index(self, x):
        if x < 0:
            return 0
        elif x >= config.WORLD_WIDTH:
            return config.NUM_SECTIONS - 1

        return int(x // config.WORLD_SECTION_WIDTH)

    def _find_section_range(self, bbox):
        origin_section = self.find_section_index(bbox.x)
        end_section = self.find_section_index(bbox.x + bbox.w)
        return (origin_section, end_section + 1)

    # This method modifies the section_to_clients dict and the active_sections
    # set and should not be called without first locking the dict and set.
    def _update_client_section(self, client, old_section, new_section):
        if old_section in self.section_to_clients:
            self.section_to_clients[old_section].remove(client)
            if len(self.section_to_clients[old_section]) == 0:
                self.active_sections.remove(old_section)

        if new_section in self.section_to_clients:
            self.section_to_clients[new_section].add(client)
            self.active_sections.add(new_section)

    # This method modifies the section_to_mobs dict and should not be called
    # without first locking the dict and set.
    def _update_mob_section(self, mob, old_section, new_section):
        if old_section in self.section_to_mobs:
            self.section_to_mobs[old_section].remove(mob)

        if new_section in self.section_to_mobs:
            self.section_to_mobs[new_section].add(mob)

    def get_local_sections(self, section, section_radius=3):
        if section_radius < 0:
            section_radius = 0
        start = max(section - section_radius, 0)
        end = min(section + section_radius + 1, config.NUM_SECTIONS)
        return range(start, end)

    def __call__(self):
        target_frame_interval = 1.0/config.ROOM_SPEED
        consecutive_error_steps = 0
        while self.running:
            try:
                step_start_timestamp = time.time()
                self.world_step_tstamp = step_start_timestamp

                with acquire_all(self.mobs, self.section_to_clients, self.section_to_mobs,
                                 self.active_sections, self.game_server.clients, self.client_mob_spawn):
                    self._step()

                # compute time to next frame
                now = time.time()
                time_to_wait = target_frame_interval - (now - step_start_timestamp)
                if time_to_wait < 0:
                    time_to_wait = 0
                time.sleep(time_to_wait)
                consecutive_error_steps = 0
            except Exception as e:
                self.logger.error('Unhandled exception in world step %s: %s' % (self.world_step_num, e))
                traceback.print_exc()
                consecutive_error_steps += 1
                if consecutive_error_steps > config.WORLD_MAX_ERROR_STEPS:
                    self.logger.error('More than %s consecutive error steps, terminating world thread...' % (config.WORLD_MAX_ERROR_STEPS))
                    self.running = False
                else:
                    self.logger.info('Continuing, consecutive_error_steps=%s', consecutive_error_steps)

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
                mob_id = self._generate_mob_id()
                mob_type, mob_x, mob_y, mob_spawner = payload
                new_mob = Mob(mob_id, mob_type, mob_x, mob_y, mob_spawner, self)
                if mob_spawner:
                    mob_spawner._add_mob(new_mob)
                self._add_mob(new_mob)

            elif header == mail_header.MSG_DELETE_MOB:
                self._remove_mob(payload)

            elif header == mail_header.UPDATE_MOB_SECTION:
                self._update_mob_section(*payload)

            elif header == mail_header.UPDATE_CLIENT_SECTION:
                self._update_client_section(*payload)

            elif header == mail_header.MSG_POISON_PILL:
                raise Exception('Got poison pill')

    def _step(self):
        self._process_mail_messages()

        now = datetime.now()
        current_month = now.month
        current_day = now.day

        # loop through events and run the spawners
        event_is_active = False
        for event in self.events:
            active = False
            if event['start_month'] > event['end_month']:
                # Event crosses a year boundary
                if (current_month >= event['start_month'] and current_day >= event['start_day']) or (current_month <= event['end_month'] and current_day <= event['end_day']):
                    active = True
            else:
                if current_month >= event['start_month'] and current_day >= event['start_day'] and current_month <= event['end_month'] and current_day <= event['end_day']:
                    active = True
            if active:
                event_is_active = True
                for spawner in event['mob_spawn']:
                    spawner.step()

        # run the default spawners if there are no active events
        if not event_is_active:
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
                    self._broadcast_local(buff, mob.section)

            elif mob.section in active_sections_expanded:
                # mob.step() is an expensive call, so we only want to do it in the active world sections (where the players are)
                mob.step()

        # remove dead mobs
        for mob in to_remove:
            self._remove_mob(mob)

        # broadcast mob updates
        # first find each clien
        for client in self.game_server.clients:
            # then get the client's nearby sections
            local_sections = self.get_local_sections(client.section)
            for section in local_sections:
                # find all the mobs in the nearby section
                for mob in self.section_to_mobs.get(section, []):
                    # send that client the mob status
                    if mob.write_packet_this_step:
                        client.send_tcp_message(mob.get_status_packet())

            # interpolate the client's state
            client.interpolate_state()

        for mob_id in self.mobs:
            if mob.write_packet_this_step:
                mob.reset_write_packet_flag()

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

    def get_jump_through_blocks_at(self, bbox):
        touching = []
        section_range = self._find_section_range(bbox)
        for i in range(*section_range):
            for jump_through_block in self.sections[i].jump_through_blocks:
                if jump_through_block.check_collision(bbox):
                    touching.append(jump_through_block)

        return touching

    def _find_player_nearest(self, x, section_radius=3):
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

    def _generate_mob_id(self):
        '''
        Mob ID's in StickOnline are a 16 bit number.
        LocalSO uses the upper 6 bits of the ID designate the spawner ID.
        The lower 10 bits are the mob's unique ID within that spawner.
        This allows a maximum of 1024 mobs per spawner.
        Attempting to spawn more than 1024 mobs per spawner will cause mobs to be overwritten and disappear.
        Spawner ID 0b111111 is reserved for all mobs spawned by players.
        '''
        new_id = (0b111111 << 10) | (self.mob_id_gen_counter % 1024)
        self.mob_id_gen_counter += 1
        return new_id

    # This method modifies the mobs dict and should not be called without first
    # locking the dict.
    def _add_mob(self, mob):
        self.mobs[mob.id] = mob

    # This method modifies the mobs and section_to_mobs dicts and should not be
    # called without first locking the dicts.
    def _remove_mob(self, mob):
        if mob.id in self.mobs:
            del self.mobs[mob.id]
        if mob.section in self.section_to_mobs:
            self.section_to_mobs[mob.section].remove(mob)
        if mob.spawner is not None:
            # we can call this method directly because spawners are run on the world thread
            mob.spawner._mob_death(mob)

    def _broadcast_local(self, data, section, exclude=None):
        for i in self.get_local_sections(section):
            section_clients = self.section_to_clients[i]
            for client in section_clients:
                if client is exclude:
                    continue

                client.send_tcp_message(data)

    def get_client_mob_spawn(self, client):
        with self.client_mob_spawn:
            if not self.client_mob_spawn.get(client.id):
                self.client_mob_spawn[client.id] = ClientMobSpawner()
            return self.client_mob_spawn[client.id]

    def client_disconnect(self, client):
        # lock the dict
        with self.section_to_clients:
            if client.section in self.section_to_clients:
                if client in self.section_to_clients[client.section]:
                    self.section_to_clients[client.section].remove(client)
                else:
                    self.logger.warn('client_disconnect unknown client %s', client)
            else:
                self.logger.warn('client_disconnect unknown section %s', client.section)
