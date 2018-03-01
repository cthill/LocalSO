import json
from util import ceildiv

config_json = json.loads(open('data/config.json').read())

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

# game binary files directory
GAME_BIN_DIR = config_json['game_bin_dir']

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
WORLD_GRAVITY = 1
WORLD_TERMINAL_VELOCITY = 14


SOLID_BLOCK_DATA = []
MOB_DATA = []
MOB_SPAWN = []

DATA_DIR = 'data/'
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
