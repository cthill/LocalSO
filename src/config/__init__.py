import json
from util import ceildiv

# TODO: Move config to json file?

INTERFACE = '0.0.0.0'
INTERFACE_HTTP = '0.0.0.0'
PORT_HTTP = 80
GAME_MOTD = 'Welcome to LocalSO!'
MENU_MOTD = 'Welcome to LocalSO!'

# Change these parameters if you want a different experience from the original game
MOB_SPAWN_RATE_MULTIPLIER = 2.0 # (default = 1.0) change this number to increase or decrease the mob spawn rate
MOB_SPAWN_COUNT_MAX_MULTIPLIER = 2 # (default = 1) change this number to increase the maximum number of mobs in each area
MOB_SPAWN_SPECIAL_RATE_MULTIPLIER = 1.0 # (default = 1.0)
MOB_SPAWN_BUNNY_RATE_MULTIPLIER = 1.0 # (default = 1.0)
PLAYER_DAMAGE_MULTIPLIER = 1.0 # (default = 1.0)

# Do not change these parameters, modifying them may cause bugs or performance issues
PORT_ACCOUNT = 3104
PORT_GAME = 3105
ROOM_SPEED = 30
WORLD_WIDTH = 67966
WORLD_HEIGHT = 2200
WORLD_SECTION_WIDTH = 512
NUM_SECTIONS = ceildiv(WORLD_WIDTH, WORLD_SECTION_WIDTH)
HIT_SOUND_ID = 0x01
HIT_INVINCIBLE_FRAMES = 30

PLAYER_MASK_WIDTH = 28
PLAYER_MASK_HEIGHT = 54
PLAYER_OFFSET_X = 14
PLAYER_OFFSET_Y = 0

WORLD_GRAVITY = 1
WORLD_TERMINAL_VELOCITY = 14

SOLID_BLOCK_DATA = []
MOB_DATA = []
MOB_SPAWN = []

DATA_DIR = '../data/'
# load world data json
block_data_json = open(DATA_DIR + 'world.json').read()
block_data = json.loads(block_data_json)
# add solid blocks
SOLID_BLOCK_DATA += block_data['block_type_1']
SOLID_BLOCK_DATA += block_data['block_type_2']

# load mob json
mob_data_json = open(DATA_DIR + 'mob.json').read()
mob_data = json.loads(mob_data_json)
MOB_DATA += mob_data

# load mob_spawn json
mob_spawn_json = open(DATA_DIR + 'mob_spawn.json').read()
mob_spawn = json.loads(mob_spawn_json)
MOB_SPAWN += mob_spawn
