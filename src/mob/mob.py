from random import randint

import config
from gmk.bounding_box import BoundingBox
from config import ROOM_SPEED, WORLD_WIDTH, WORLD_HEIGHT, packet
from net.buffer import *
from util.util import ceildiv

gravity = 1
terminal_velocity = 14
xspeed_knockback_decay = 1



SPRITE_INDEX_WALK = 0
SPRITE_INDEX_STAND = 1
SPRITE_INDEX_ATTACK = 2
SPRITE_INDEX_JUMP = 3

class Mob():
    def __init__(self, id, mob_type, x, y, spawner, world):
        self.id = id
        self.mob_type = mob_type
        self.x = x
        self.y = y
        self.spawner = spawner
        self.world = world

        self.section = None
        self.update_world_position(x, y)

        self.mob_dat = config.MOB_DATA[mob_type]
        self.sprite_index = SPRITE_INDEX_WALK
        self.image_index = 0.0
        self.sprite = self.mob_dat['sprites'][self.sprite_index]

        self.w = self.mob_dat['width'] * self.mob_dat['scale']
        self.h = self.mob_dat['height'] * self.mob_dat['scale']

        self.x_offset = self.mob_dat['x_offset'] * self.mob_dat['scale']
        self.y_offset = self.mob_dat['y_offset'] * self.mob_dat['scale']

        self.base_speed = self.mob_dat['speed']
        self.direction = -1 if randint(0, 1) == 0 else 1
        self.xspeed = 0
        self.image_index = 0
        self.yspeed = 0
        self.xspeed_knockback = 0

        self.hp = self.mob_dat['hp']
        self.defense = self.mob_dat['defense']
        self.dead = False

        self.state_time = 0

        self.timers = {}
        self.set_reset_timer('atk')
        self.set_reset_timer('jump')

        self.broadcast_death = True

    def state_machine(self):
        if self.state_time > 0:
            self.state_time -= 1
        else:
            if self.sprite_index == SPRITE_INDEX_WALK:
                self._set_sprite(SPRITE_INDEX_STAND)
                self.state_time = randint(config.ROOM_SPEED * 1, config.ROOM_SPEED * 3)
            elif self.sprite_index == SPRITE_INDEX_STAND:
                self._set_sprite(SPRITE_INDEX_WALK)
                self.state_time = randint(config.ROOM_SPEED * 3, config.ROOM_SPEED * 6)
                self.direction = -1 if randint(0, 1) == 0 else 1

    def set_reset_timer(self, timer):
        self.timers[timer] = self.mob_dat['timer_%s_base' % timer] + randint(0, self.mob_dat['timer_%s_rand' % timer])

    def _set_sprite(self, sprite_index):
        self.sprite_index = sprite_index
        self.image_index = 0.0
        self.sprite = self.mob_dat['sprites'][self.sprite_index]

    def step(self):
        if self.dead:
            return

        self.state_machine()

        x_plus_speed_as_int = int(round(self.x + self.xspeed))
        x_as_int = int(round(self.x))
        y_as_int = int(round(self.y))

        bbox_side = BoundingBox(x_plus_speed_as_int - self.x_offset, y_as_int - self.y_offset, self.w, self.h)
        side_collide = len(self.world.solid_block_at(bbox_side)) > 0

        bbox_below = BoundingBox(x_as_int - self.x_offset, y_as_int - self.y_offset + 1, self.w, self.h)
        ground_below = len(self.world.solid_block_at(bbox_below)) > 0

        # atk
        self.timers['atk'] -= 1
        if self.timers['atk'] == 0:
            self.set_reset_timer('atk')
            if ground_below:
                search_radius = ceildiv(int(round(self.mob_dat['follow_radius'] / 2.0)), config.WORLD_SECTION_WIDTH)
                to_atk = self.world.find_player_nearest(x_as_int, section_radius=search_radius)
                if to_atk is not None and abs(to_atk.x - self.x) < self.mob_dat['follow_radius'] / 2.0:
                    self._set_sprite(SPRITE_INDEX_ATTACK)
                    self.timers['atk'] += ceildiv(float(self.sprite['frames']), self.mob_dat['image_speed_atk'])



        if self.sprite_index == SPRITE_INDEX_ATTACK and self.image_index >= self.sprite['frames']:
            self.sprite_index = SPRITE_INDEX_STAND


        # jump
        self.timers['jump'] -= 1
        if self.timers['jump'] == 0:
            self.set_reset_timer('jump')

            if side_collide and ground_below and self.sprite_index != SPRITE_INDEX_ATTACK:
                self.yspeed = -self.mob_dat['jump_speed']
                # self._set_sprite(SPRITE_INDEX_JUMP)


        # gravity
        self.yspeed += gravity
        if self.yspeed > terminal_velocity:
            self.yspeed = terminal_velocity

        # reduce xspeed
        if self.xspeed_knockback > 0:
            self.xspeed_knockback -= xspeed_knockback_decay
            if self.xspeed_knockback < 0:
                self.xspeed_knockback = 0
        elif self.xspeed_knockback < 0:
            self.xspeed_knockback += xspeed_knockback_decay
            if self.xspeed_knockback > 0:
                self.xspeed_knockback = 0

        # xspeed
        if self.sprite_index == SPRITE_INDEX_WALK:
            if self.direction > 0:
                self.xspeed = self.base_speed
            else:
                self.xspeed = -self.base_speed
        elif self.sprite_index == SPRITE_INDEX_STAND or self.sprite_index == SPRITE_INDEX_ATTACK:
            self.xspeed = 0

        x_plus_speed_as_int = int(round(self.x + self.xspeed + self.xspeed_knockback))
        y_as_int = int(round(self.y))

        bbox_side = BoundingBox(x_plus_speed_as_int - self.x_offset, y_as_int - self.y_offset, self.w, self.h)
        side_collide = len(self.world.solid_block_at(bbox_side)) > 0

        # move x
        if not side_collide:
            self.x += self.xspeed + self.xspeed_knockback
        if self.x < 0:
            self.x = 0
        elif self.x > WORLD_WIDTH:
            self.x = WORLD_WIDTH

        # move y
        self.y += self.yspeed
        if self.y - self.y_offset > WORLD_HEIGHT + 300:
            self._die(broadcast_death=False)
            return
        elif self.y < 0:
            self.y = 0

        self.update_world_position(self.x, self.y)

        x_as_int = int(round(self.x))
        y_as_int = int(round(self.y))
        bbox = BoundingBox(x_as_int - self.x_offset, y_as_int - self.y_offset, self.w, self.h)
        touching = self.world.solid_block_at(bbox)

        if len(touching) > 0:
            min_touching_y = WORLD_HEIGHT

            for solid_block in touching:
                if solid_block.y < min_touching_y:
                    min_touching_y = solid_block.y

            self.y = min_touching_y - self.h + self.y_offset

        # sprite animation code
        if self.sprite_index == SPRITE_INDEX_ATTACK:
            self.image_index += self.mob_dat['image_speed_atk']
        else:
            self.image_index += self.mob_dat['image_speed']

    def hit(self, damage, knockback_x, knockback_y):
        if self.dead:
            return

        dmg = (damage - self.defense)
        if dmg < 3:
            dmg = 3
        self.hp -= dmg
        if self.hp <= 0:
            self._die()

        self.yspeed += knockback_y
        self.xspeed_knockback = knockback_x

    def update_world_position(self, x, y):
        self.x = x
        self.y = y

        old_section = self.section
        new_section = self.world.find_section_index(int(round(x)))

        if old_section != new_section:
            self.section = new_section
            self.world.update_mob_section(self, old_section, new_section)

    def get_status_packet(self):
        # send mob info
        # print 'writing mob info %s %s %s' % (self.id, self.x, self.y)
        buff = [packet.RESP_MOB_STATUS]
        write_ushort(buff, self.id) # mob unique id
        write_uint(buff, int(round(self.x * 10))) # x
        write_short(buff, int(round(self.y * 10))) # y

        write_byte(buff, self.mob_type) # mob type
        write_byte(buff, 1 if self.direction == 1 else 0) # direction facing
        write_short(buff, int(round(self.xspeed * 10))) # x speed
        write_short(buff, 0x00 if self.sprite_index == SPRITE_INDEX_ATTACK else int(round(self.yspeed * 10))) # y speed

        write_ushort(buff, self.sprite['id']) # sprite
        write_short(buff, (int(self.image_index) % self.sprite['frames']) * 100) # image_index
        write_short(buff, int(self.mob_dat['image_speed'] * 100)) # image speed

        if self.xspeed_knockback != 0:
            write_short(buff, int(round(self.xspeed_knockback * 10)))

        return buff

    def _die(self, broadcast_death=True):
        self.broadcast_death = broadcast_death
        self.hp = 0
        self.dead = True

    def __str__(self):
        return 'Mob(%s)' % self.id
