import math
from random import randint

import config
from bounding_box import BoundingBox
from mailbox import mail_header
from net import packet
from net.buffer import *
from util import ceildiv, dist

# xspeed_knockback_decay = 1
xspeed_knockback_div = 3
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

        if self.mob_type == 4 or self.mob_type == 6 or self.mob_type == 15:
            self.image_index = randint(0, self.sprite['frames'] - 1)
            self.direction = 1

        self.client_aggrov = None
        self.dmg_bbox = None
        self.players_hit = set()
        self.atk_length_steps = 0
        self.atk_delay_steps = 0

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

    def get_bbox(self):
        return BoundingBox(int(round(self.x)) - self.x_offset, int(round(self.y)) - self.y_offset, self.w, self.h)

    def step(self):
        if self.dead:
            return

        # presents and easter eggs
        if self.mob_type == 4 or self.mob_type == 6 or self.mob_type == 15:
            self._step_passive()
        else:
            self._step_active()


    def _step_active(self):
        self.state_machine()

        x_plus_speed_as_int = int(round(self.x + self.xspeed))
        x_as_int = int(round(self.x))
        y_as_int = int(round(self.y))

        bbox_side = BoundingBox(x_plus_speed_as_int - self.x_offset, y_as_int - self.y_offset, self.w, self.h)
        side_collide = len(self.world.solid_block_at(bbox_side)) > 0

        bbox_below = BoundingBox(x_as_int - self.x_offset, y_as_int - self.y_offset + 1, self.w, self.h)
        ground_below = len(self.world.solid_block_at(bbox_below)) > 0

        # atk
        self._atk_step(ground_below, x_as_int)

        # jump
        self.timers['jump'] -= 1
        if self.timers['jump'] == 0:
            self.set_reset_timer('jump')

            if side_collide and ground_below and self.sprite_index != SPRITE_INDEX_ATTACK:
                self.yspeed = -self.mob_dat['jump_speed']
                if self.direction > 0:
                    self.xspeed = self.base_speed
                else:
                    self.xspeed = -self.base_speed


        # xspeed
        if self.sprite_index == SPRITE_INDEX_WALK: #or self.sprite_index == SPRITE_INDEX_JUMP:
            if self.direction > 0:
                self.xspeed = self.base_speed
            else:
                self.xspeed = -self.base_speed
        elif self.sprite_index == SPRITE_INDEX_STAND or self.sprite_index == SPRITE_INDEX_ATTACK:
            self.xspeed = 0


        # move in x and y
        # if self.sprite_index != SPRITE_INDEX_ATTACK:
        if self.xspeed_knockback != 0:
            self._move_xspeed_check_side_collide(self.xspeed_knockback)
        else:
            self._move_xspeed_check_side_collide(self.xspeed)

        self._move_yspeed_check_ground_collide()

        self.update_world_position(self.x, self.y)

        self._do_animation()

    def _step_passive(self):
        self._move_yspeed_check_ground_collide()
        self.update_world_position(self.x, self.y)


    def _do_animation(self):
        if self.sprite_index == SPRITE_INDEX_ATTACK and self.image_index >= self.sprite['frames']:
            self._set_sprite(SPRITE_INDEX_STAND)

        if self.sprite_index == SPRITE_INDEX_ATTACK:
            self.image_index += self.mob_dat['image_speed_atk']
        else:
            self.image_index += self.mob_dat['image_speed']

    def _hit_player(self, client):
        if not client.god_mode:
            buff = [packet.RESP_DMG_PLAYER]
            write_ushort(buff, client.id)
            write_ushort(buff, self.mob_dat['atk_stat'])
            write_byte(buff, 30)
            write_ushort(buff, config.HIT_SOUND_ID)
            write_short(buff, self.mob_dat['knockback_x'] * self.direction * 10)
            write_short(buff, self.mob_dat['knockback_y'] * 10)
            self.world.game_server.broadcast(buff)

    def _atk_step(self, ground_below, x_as_int):
        if self.mob_dat['avoid_player']:
            return

        self.timers['atk'] -= 1
        if self.timers['atk'] > 0:
            if self.dmg_bbox is not None:
                if self.atk_delay_steps > 0:
                    self.atk_delay_steps -= 1
                else:
                    if self.atk_length_steps > 0:
                        self.atk_length_steps -= 1
                        if len(self.players_hit) < self.mob_dat['players_hit_per_atk']:
                            search_radius = ceildiv(int(round(self.mob_dat['follow_radius'])), config.WORLD_SECTION_WIDTH)
                            facing_right = self.direction == 1
                            if facing_right:
                                x_search = self.get_bbox().right()
                            else:
                                x_search = self.get_bbox().left()
                            section = self.world.find_section_index(x_search)
                            sections_to_search = self.world.get_local_sections(section, section_radius=search_radius)

                            clients_to_test = []
                            for section in sections_to_search:
                                clients_to_test.extend(self.world.get_clients_in_section(section))

                            for client in clients_to_test:
                                if client not in self.players_hit and self.dmg_bbox.check_collision(client.get_bbox()):
                                    self._hit_player(client)
                                    self.players_hit.add(client)
                        else:
                            self.dmg_bbox = None
                    else:
                        self.dmg_bbox = None

        else:
            if ground_below and self.xspeed_knockback == 0:
                search_radius = ceildiv(int(round(self.mob_dat['follow_radius'])), config.WORLD_SECTION_WIDTH)
                facing_right = self.direction == 1
                if facing_right:
                    x_search = self.get_bbox().right()
                else:
                    x_search = self.get_bbox().left()

                self.client_aggrov = self.world.find_player_nearest(x_search, section_radius=search_radius)
                if self.client_aggrov is not None and dist(self.x, self.y, self.client_aggrov.x, self.client_aggrov.y) < self.mob_dat['follow_radius'] / 2.0:
                    ca_bbox = self.client_aggrov.get_bbox()
                    if facing_right:
                        if ca_bbox.hcenter() >= self.get_bbox().hcenter():
                            if ca_bbox.left() + (ca_bbox.right() - ca_bbox.left()) / 2 >= self.get_bbox().left() + (self.get_bbox().right() - self.get_bbox().left()) / 2 + self.mob_dat['dmg_box_x']:
                                if ca_bbox.left() + (ca_bbox.right() - ca_bbox.left()) / 2 < self.get_bbox().left() + (self.get_bbox().right() - self.get_bbox().left()) / 2 + self.mob_dat['dmg_box_x'] + self.mob_dat['dmg_box_xscale']:
                                    self._init_atk()
                    else:
                        if ca_bbox.hcenter() <= self.get_bbox().hcenter():
                            if ca_bbox.left() + (ca_bbox.right() - ca_bbox.left()) / 2 <= self.get_bbox().left() + (self.get_bbox().right() - self.get_bbox().left()) / 2 - self.mob_dat['dmg_box_x']:
                                if ca_bbox.left() + (ca_bbox.right() - ca_bbox.left()) / 2 > self.get_bbox().left() + (self.get_bbox().right() - self.get_bbox().left()) / 2 - self.mob_dat['dmg_box_x'] - self.mob_dat['dmg_box_xscale']:
                                    self._init_atk()

            self.set_reset_timer('atk')
            if self.sprite_index == SPRITE_INDEX_ATTACK:
                self.timers['atk'] += ceildiv(float(self.sprite['frames']), self.mob_dat['image_speed_atk'])


    def _init_atk(self):
        self._set_sprite(SPRITE_INDEX_ATTACK)

        facing_right = self.direction == 1

        dby = int(math.floor(self.get_bbox().top())) + int(round((self.get_bbox().bottom() - self.get_bbox().top()) / 2.0)) - int(round(self.mob_dat['dmg_box_yscale'] / 2.0)) + self.mob_dat['dmg_box_y']
        if facing_right:
            dbx = int(round((self.get_bbox().left() + self.get_bbox().right()) / 2.0)) + self.mob_dat['dmg_box_x']
            self.dmg_bbox = BoundingBox(dbx, dby, self.mob_dat['dmg_box_xscale'], self.mob_dat['dmg_box_yscale'])
        else:
            dbx = int(round((self.get_bbox().left() + self.get_bbox().right()) / 2.0)) - self.mob_dat['dmg_box_xscale'] - self.mob_dat['dmg_box_x']
            self.dmg_bbox = BoundingBox(dbx, dby, self.mob_dat['dmg_box_xscale'], self.mob_dat['dmg_box_yscale'])

        self.players_hit = set()
        self.atk_delay_steps = ceildiv(self.mob_dat['atk_delay_frames'], self.mob_dat['image_speed_atk'])
        self.atk_length_steps = self.mob_dat['atk_length_steps']

    def _move_xspeed_check_side_collide(self, xspeed):
        for i in reversed(range(1, abs(int(round(xspeed))) + 1)):
            if xspeed > 0:
                x_plus_speed_as_int = int(round(self.x + i))
                y_as_int = int(round(self.y))

                bbox_side = BoundingBox(x_plus_speed_as_int - self.x_offset, y_as_int - self.y_offset, self.w, self.h)
                side_collide = len(self.world.solid_block_at(bbox_side)) > 0

                if not side_collide and x_plus_speed_as_int < config.WORLD_WIDTH:
                    self.x = self.x + i
                    break

            else:
                x_plus_speed_as_int = int(round(self.x - i))
                y_as_int = int(round(self.y))

                bbox_side = BoundingBox(x_plus_speed_as_int - self.x_offset, y_as_int - self.y_offset, self.w, self.h)
                side_collide = len(self.world.solid_block_at(bbox_side)) > 0

                if not side_collide and x_plus_speed_as_int > 0:
                    self.x = self.x - i
                    break

    def _move_yspeed_check_ground_collide(self):
        # gravity
        self.yspeed += config.WORLD_GRAVITY
        if self.yspeed > config.WORLD_TERMINAL_VELOCITY:
            self.yspeed = config.WORLD_TERMINAL_VELOCITY

        # move y
        self.y += self.yspeed
        if self.y - self.y_offset > config.WORLD_HEIGHT + 300:
            self._die(broadcast_death=False)
            return
        elif self.y < 0:
            self.y = 0

        x_as_int = int(round(self.x))
        y_as_int = int(round(self.y))
        bbox = BoundingBox(x_as_int - self.x_offset, y_as_int - self.y_offset, self.w, self.h)
        touching = self.world.solid_block_at(bbox)

        if len(touching) > 0:
            min_touching_y = config.WORLD_HEIGHT

            for solid_block in touching:
                if solid_block.y < min_touching_y:
                    min_touching_y = solid_block.y

            self.y = min_touching_y - self.h + self.y_offset
            self.xspeed_knockback = 0
            self.yspeed = 0
        else:
            pass
            # print 'setsrpint jump'
            # self._set_sprite(SPRITE_INDEX_JUMP)

    def hit(self, damage, knockback_x, knockback_y):
        if self.dead:
            return

        dmg = (damage - self.defense)
        if dmg < 3:
            dmg = 3
        self.hp -= dmg
        if self.hp <= 0:
            self._die()

        self.yspeed += self._normalize_knockback_value(knockback_y)
        self.xspeed_knockback = self._normalize_knockback_value(knockback_x) / xspeed_knockback_div

    def _normalize_knockback_value(self, val):
        if self.mob_dat['immune_knockback_atk']:
            if self.sprite_index == SPRITE_INDEX_ATTACK and self.image_index >= self.mob_dat['immune_knockback_delay']:
                return 0

        val = float(val)
        result = val - math.floor(val * (self.mob_dat['knockback_resist'] / 100.0) * 10.0) / 10.0
        if val >= 0 and result < 3:
            if val >= 3 and result < 3:
                result = 3
            else:
                result = 0
        elif val < 0 and result > -3:
            if val <= -3 and result > -3:
                result = -3
            else:
                result = 0

        return result

    def update_world_position(self, x, y):
        self.x = x
        self.y = y

        old_section = self.section
        new_section = self.world.find_section_index(int(round(x)))

        if old_section != new_section:
            self.section = new_section
            self.world.send_mail_message(mail_header.UPDATE_MOB_SECTION, (self, old_section, new_section))

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
        write_short(buff, int((self.mob_dat['image_speed_atk'] if self.sprite_index == SPRITE_INDEX_ATTACK else self.mob_dat['image_speed']) * 100)) # image speed

        if self.xspeed_knockback != 0:
            write_short(buff, int(round(self.xspeed_knockback * 10)))

        return buff

    def _die(self, broadcast_death=True):
        self.broadcast_death = broadcast_death
        self.hp = 0
        self.dead = True

    def __str__(self):
        return 'Mob(%s)' % self.id
