import json
import logging
from util import ceildiv

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%d-%m-%y %H:%M:%S')

with open('config.json') as f:
    config_json = json.loads(f.read())

INTERFACE = config_json['interface']
INTERFACE_HTTP = config_json['interface_http']
PORT_HTTP = config_json['port_http']

# Change these parameters (in config.json) if you want a different experience from the original game
MOB_SPAWN_RATE_MULTIPLIER = config_json['mob_spawn_rate_multiplier']
MOB_SPAWN_COUNT_MAX_MULTIPLIER = config_json['mob_spawn_count_max_multiplier']
MOB_SPAWN_CHANCE_BOSS_MULTIPLIER = config_json['mob_spawn_chance_boss_multiplier']
MOB_SPAWN_CHANCE_BUNNY_MULTIPLIER = config_json['mob_spawn_chance_bunny_multiplier']
PLAYER_DAMAGE_MULTIPLIER = config_json['player_damage_multiplier']
PLAYER_START_GOLD = config_json['player_start_gold']

# message of the day
INGAME_MOTD = config_json['ingame_motd']
MENU_MOTD = config_json['menu_motd']

# registration parameters
REGISTER_ILLEGAL_CHARACTERS = ' #/\\:*?<>|"'
REGISTER_ILLEGAL_USERNAMES = ['meiun', 'danimal', 'seifer']
REGISTER_CLOSED = config_json['register_closed']

# db file
SQLITE_DB_FILE = config_json['sqlite_db_file']
SQLITE_DB_INIT_FILE = config_json['sqlite_db_init_file']

# dirs
GAME_BIN_DIR = config_json['game_bin_dir']
DATA_DIR = config_json['data_dir']

# load block data json
SOLID_BLOCK_DATA = []
JUMP_THROUGH_BLOCK_DATA = []
with open(DATA_DIR + '/world.json') as f:
    block_data = json.loads(f.read())
    SOLID_BLOCK_DATA += block_data['block_type_1']
    SOLID_BLOCK_DATA += block_data['block_type_2']
    JUMP_THROUGH_BLOCK_DATA += block_data['block_type_3']

# load mob json
MOB_DATA = []
with open(DATA_DIR + '/mob.json') as f:
    MOB_DATA += json.loads(f.read())

# load mob_spawn json
MOB_SPAWN = []
with open(DATA_DIR + '/mob_spawn.json') as f:
    MOB_SPAWN += json.loads(f.read())

# load item data
ITEM_DATA = {}
with open(DATA_DIR + '/item.json') as f:
    for item in json.loads(f.read()):
        ITEM_DATA[item['id']] = item

# load player spawn data
PLAYER_SPAWN = {}
with open(DATA_DIR + '/player_spawn.json') as f:
    for spawn_point in json.loads(f.read()):
        PLAYER_SPAWN[spawn_point['id']] = spawn_point

# set default spawn for new accounts
PLAYER_SPAWN_DEFAULT = PLAYER_SPAWN[1]


# Do not change these parameters, modifying them may cause bugs or performance issues
COMPATIBLE_GAME_VERSION = 439.0
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
PLAYER_STATUS_BROADCAST_RADIUS = 1430
PLAYER_TIMEOUT = 10 # in seconds
LOGIN_PENDING_TIMEOUT = 5 # in seconds
WORLD_GRAVITY = 1
WORLD_TERMINAL_VELOCITY = 14
WORLD_MAX_ERROR_STEPS = 30
