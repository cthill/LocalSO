from datetime import datetime
import logging
import md5
import os.path
import sqlite3
from threading import Lock

import config

logger = logging.getLogger('db')

class SQLiteDB:
    def __init__(self, db_file, stick_online_server):
        self.db_file = db_file
        self.db_lock = Lock()
        self.stick_online_server = stick_online_server

        should_create_db = not os.path.isfile(self.db_file)

        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        logger.info('Connected to database %s' % (self.db_file))
        self.conn.row_factory = sqlite3.Row

        try:
            if should_create_db:
                self._create_db()
                self._create_admin_account()
        except Exception as e:
            logger.error('Error initializing the datbase. Please delete %s and try again.', db_file)
            raise e

    def _create_db(self):
        logger.info('Performing first time setup.')
        logger.info('Creating database tables...')

        with open(config.SQLITE_DB_INIT_FILE) as f:
            init_statements = f.read()

        c = self.conn.cursor()
        c.executescript(init_statements)
        self.conn.commit()
        logger.info('Done.')

    def _create_admin_account(self):
        print 'You must register an admin account.'
        admin_username = raw_input("  username: ")
        admin_password = raw_input("  password: ")

        m = md5.new()
        m.update(admin_password)
        admin_passhash = m.hexdigest()

        c = self.conn.cursor()
        now = datetime.now().isoformat()

        # create account
        c.execute('''
        INSERT INTO clients
        (
            id, name, passhash, register_date, last_login_date, last_save_date,
            last_login_ip, banned, spawn_x, spawn_y, hp, mp, stat_str, stat_agi,
            stat_int, stat_vit, int_unknown_1, level, experience, admin_level,
            stat_points, int_unknown_2, weapon_equipped, hat_equipped, int_unknown_3,
            int_unknown_4, int_unknown_5, gold, clan
        )
        VALUES
        (?, ?, ?, ?, ?, null, null, 0, 1080, 300, 739, 1200, 150, 150, 150, 150, 1, 255, 0.0, 250, 0, 0, 10, 17, 0, 0, 0, 9999999, '')
        ''', (0, admin_username.lower(), admin_passhash, now, now))

        # add items
        items = [
            17, # gm helm
            31, # dragoon helm
            10, # wood hammer
            39, # stone hammer
            49, # Okry
            50, # Scotty's Axe
            52, # Gunblade
            53, # Princess Jenny's Crown
            54, # Bella's Magical Death Weapon Extraordinaire
            70, # Hyperion
            71, # Dark Gauntlet
            72  # Lingus Gauntlet
        ]
        for item_id in items:
            c.execute('INSERT INTO inventory (client_id, item_id) VALUES (?, ?)', (0, item_id))

        # commit
        self.conn.commit()
        print 'Created admin account %s' % admin_username
        print 'To grant admin access to other users, use the in game commands.'

    def get_client(self, name):
        with self.db_lock:
            c = self.conn.cursor()
            c.execute('SELECT * FROM clients WHERE name=?', (name.lower(),))
            db_client = c.fetchone()
            return db_client

    def create_client(self, name, passhash, admin_level=0):
        with self.db_lock:
            c = self.conn.cursor()
            now = datetime.now().isoformat()
            c.execute('''
            INSERT INTO clients
            (
                name, passhash, register_date, last_login_date, last_save_date,
                last_login_ip, banned, spawn_x, spawn_y, hp, mp, stat_str, stat_agi,
                stat_int, stat_vit, int_unknown_1, level, experience, admin_level,
                stat_points, int_unknown_2, weapon_equipped, hat_equipped, int_unknown_3,
                int_unknown_4, int_unknown_5, gold, clan
            )
            VALUES
            (?, ?, ?, ?, null, null, 0, 1080, 300, 104, 67, 1, 1, 1, 1, 1, 1, 0.0, ?, 0, 0, 0, 0, 0, 0, 0, ?, '')
            ''', (name.lower(), passhash, now, now, admin_level, config.PLAYER_START_GOLD))
            self.conn.commit()

    def get_items(self, client_id):
        with self.db_lock:
            c = self.conn.cursor()
            item_rows = c.execute('SELECT * FROM inventory WHERE client_id=?', (client_id,))
            return [x['item_id'] for x in item_rows]

    def get_unknown_list_1(self, client_id):
        with self.db_lock:
            c = self.conn.cursor()
            item_rows = c.execute('SELECT * FROM unknown_list_1 WHERE client_id=?', (client_id,))
            return [x['list_element_id'] for x in item_rows]

    def get_unknown_list_2(self, client_id):
        with self.db_lock:
            c = self.conn.cursor()
            item_rows = c.execute('SELECT * FROM unknown_list_2 WHERE client_id=?', (client_id,))
            return [x['list_element_id'] for x in item_rows]

    def save_client(self, d):
        with self.db_lock:
            client_id = d['id']
            save_values = (
                datetime.now().isoformat(), d['spawn_x'], d['spawn_y'], d['hp'],
                d['mp'], d['stat_str'], d['stat_agi'], d['stat_int'], d['stat_vit'],
                d['int_unknown_1'], d['level'], d['experience'], d['stat_points'],
                d['int_unknown_2'], d['weapon_equipped'], d['hat_equipped'], d['int_unknown_3'],
                d['int_unknown_4'], d['int_unknown_5'], d['gold'], client_id
            )

            c = self.conn.cursor()
            c.execute('''
            UPDATE clients SET
                last_save_date = ?,
                spawn_x = ?,
                spawn_y = ?,
                hp = ?,
                mp = ?,
                stat_str = ?,
                stat_agi = ?,
                stat_int = ?,
                stat_vit = ?,
                int_unknown_1 = ?,
                level = ?,
                experience = ?,
                stat_points = ?,
                int_unknown_2 = ?,
                weapon_equipped = ?,
                hat_equipped = ?,
                int_unknown_3 = ?,
                int_unknown_4 = ?,
                int_unknown_5 = ?,
                gold = ?
            WHERE id=?
            ''', save_values)

            c.execute('DELETE FROM inventory WHERE client_id=?', (client_id,))
            for item_id in d['inventory']:
                c.execute('INSERT INTO inventory (client_id, item_id) VALUES (?, ?)', (client_id, item_id))

            c.execute('DELETE FROM unknown_list_1 WHERE client_id=?', (client_id,))
            for list_element_id in d['unknown_list_1']:
                c.execute('INSERT INTO unknown_list_1 (client_id, list_element_id) VALUES (?, ?)', (client_id, list_element_id))

            c.execute('DELETE FROM unknown_list_2 WHERE client_id=?', (client_id,))
            for list_element_id in d['unknown_list_2']:
                c.execute('INSERT INTO unknown_list_2 (client_id, list_element_id) VALUES (?, ?)', (client_id, list_element_id))

            self.conn.commit()

    def ban_unban_client(self, client_id, banned):
        with self.db_lock:
            c = self.conn.cursor()
            c.execute('UPDATE clients SET banned=? WHERE id=?', (1 if banned else 0, client_id))
            self.conn.commit()

    def set_admin_client(self, client_id, admin):
        with self.db_lock:
            c = self.conn.cursor()
            c.execute('UPDATE clients SET admin_level=? WHERE id=?', (250 if admin else 0, client_id))
            self.conn.commit()

    def set_stats(self, client_id, stats):
        '''
        Update player stats in db. Does not check for valid values.
        '''

        with self.db_lock:
            c = self.conn.cursor()

            vals = (stats['level'], stats['stat_str'], stats['stat_agi'], stats['stat_int'],
                    stats['stat_vit'], stats['stat_points'], client_id)

            c.execute('''
            UPDATE clients SET
                level=?,
                stat_str=?,
                stat_agi=?,
                stat_int=?,
                stat_vit=?,
                stat_points=?,
                experience=0.0
            WHERE id=?
            ''', vals)
            self.conn.commit()

    def add_items(self, client_id, items):
        with self.db_lock:
            c = self.conn.cursor()
            item_rows = c.execute('SELECT * FROM inventory WHERE client_id=?', (client_id,))
            num_items = len([x for x in item_rows])
            num_to_insert = min(20 - num_items, len(items))
            for i in range(num_to_insert):
                item_id = items[i]
                c.execute('INSERT INTO inventory (client_id, item_id) VALUES (?, ?)', (client_id, item_id))

            if num_to_insert > 0:
                self.conn.commit()


    def get_top_clients(self, include_admin=False):
        with self.db_lock:
            c = self.conn.cursor()

            if include_admin:
                clients = c.execute('SELECT name, level, hat_equipped, weapon_equipped FROM clients WHERE banned=0 ORDER BY level DESC LIMIT 10')
            else:
                clients = c.execute('SELECT name, level, hat_equipped, weapon_equipped FROM clients WHERE banned=0 AND admin_level=0 ORDER BY level DESC LIMIT 10')

            return [dict(x) for x in clients]
