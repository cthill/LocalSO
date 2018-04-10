import math
from random import randint

import config
from mailbox import mail_header
from mob import Mob

class MobSpawner:
    def __init__(self, mob_spawn_id, spawner_data, game_server, world):
        self.mob_spawn_id = mob_spawn_id
        self.spawner_data = spawner_data
        self.game_server = game_server
        self.world = world

        self.mob_type = self.spawner_data['mob_type']
        self.mobs = set()
        self.mob_id_counter = 0
        self.time_till_next_spawn = 0

    def step(self):
        if self.time_till_next_spawn > 0:
            self.time_till_next_spawn -= 1

        else:
            if (len(self.mobs) < self.spawner_data['max_of_type'] * config.MOB_SPAWN_COUNT_MAX_MULTIPLIER):
                self._do_spawn()

            normalized_instance_count = 0.9 + (len(self.game_server.clients) * 7.0) / 100.0
            self.time_till_next_spawn = round(((self.spawner_data['base_interval'] + randint(0, self.spawner_data['random_interval']))  / normalized_instance_count) / config.MOB_SPAWN_RATE_MULTIPLIER)
            if self.time_till_next_spawn < 0:
                self.time_till_next_spawn = 0

    def _do_spawn(self):
        if randint(0, int(round(self.spawner_data['special_spawn_chance'] / config.MOB_SPAWN_CHANCE_BOSS_MULTIPLIER))) != 0 or self.spawner_data['special_spawn_type'] == -1:
            mob_type_to_spawn = self.spawner_data['mob_type']
        else:
            mob_type_to_spawn = self.spawner_data['special_spawn_type']

        if mob_type_to_spawn == 0 and randint(0, int(round(110.0 / config.MOB_SPAWN_CHANCE_BOSS_MULTIPLIER))) == 0:
            mob_type_to_spawn = 2 # big blob boss

        if mob_type_to_spawn == 0 or mob_type_to_spawn == 3:
            if randint(0, int(round(150.0 / config.MOB_SPAWN_CHANCE_BUNNY_MULTIPLIER))) == 0:
                if randint(0, 5) == 0:
                    mob_type_to_spawn = 11 # black bunny
                else:
                    mob_type_to_spawn = 5 # bunny

        if mob_type_to_spawn == 7 or mob_type_to_spawn == 9:
            if randint(0, int(round(50.0 / config.MOB_SPAWN_CHANCE_BOSS_MULTIPLIER))) == 0:
                mob_type_to_spawn = 10 # dark sage

        if mob_type_to_spawn == 9:
            # the 250.0 here is just a guess. All of the other spawn chances were extracted from the client.
            if randint(0, int(round(250.0 / config.MOB_SPAWN_CHANCE_BOSS_MULTIPLIER))) == 0:
                mob_type_to_spawn = 16 # sand fiend

        new_mob_id = self._generate_mob_id()
        new_mob_x = self.spawner_data['x_min'] + randint(0, self.spawner_data['x_max'] - self.spawner_data['x_min'])
        new_mob_y = self.spawner_data['y'] - config.MOB_DATA[mob_type_to_spawn]['spawner_neg_y_offset']
        new_mob = Mob(new_mob_id, mob_type_to_spawn, new_mob_x, new_mob_y, self, self.world)

        # we can call this method directly because the spawners are run on the world thread
        self.world._add_mob(new_mob)
        self.mobs.add(new_mob)
        self.mob_id_counter += 1

    def _generate_mob_id(self):
        new_mob_id = -1
        while True:
            new_mob_id = (self.mob_spawn_id << 10) | (self.mob_id_counter % 1024)
            self.mob_id_counter += 1
            if new_mob_id not in self.mobs:
                break
        return new_mob_id

    def _mob_death(self, mob):
        self.mobs.remove(mob)
