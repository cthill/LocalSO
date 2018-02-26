from datetime import datetime
import logging
import os.path
import sqlite3
from threading import Lock

import config

class SQLiteDB:
    def __init__(self, db_file):
        self.db_file = db_file
        self.db_lock = Lock()

        should_init_db = not os.path.isfile(self.db_file)

        self.db = sqlite3.connect(self.db_file, check_same_thread=False)
        logging.info('Connected to database %s' % (self.db_file))
        self.db.row_factory = sqlite3.Row

        if should_init_db:
            self._init_db()

    def _init_db(self):
        logging.info('creating database tables...')
        init_statements = open(config.SQLITE_DB_SQL_INIT_FILE).read()
        c = self.db.cursor()
        c.executescript(init_statements)
        self.db.commit()
        logging.info('done.')

    def get_client(self, name):
        with self.db_lock:
            c = self.db.cursor()
            c.execute('SELECT * FROM clients WHERE name=?', (name,))
            db_client = c.fetchone()
            return db_client

    def create_client(self, name, passhash, admin_level=0):
        with self.db_lock:
            c = self.db.cursor()
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
            ''', (name, passhash, now, now, admin_level, config.PLAYER_START_GOLD))
            self.db.commit()

    def get_items(self, client_id):
        with self.db_lock:
            c = self.db.cursor()
            item_rows = c.execute('SELECT * FROM inventory WHERE client_id=?', (client_id,))
            return [x['item_id'] for x in item_rows]

    def get_unknown_list_1(self, client_id):
        with self.db_lock:
            c = self.db.cursor()
            item_rows = c.execute('SELECT * FROM unknown_list_1 WHERE client_id=?', (client_id,))
            return [x['list_element_id'] for x in item_rows]

    def get_unknown_list_2(self, client_id):
        with self.db_lock:
            c = self.db.cursor()
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

            c = self.db.cursor()
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

            self.db.commit()
