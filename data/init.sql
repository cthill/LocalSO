CREATE TABLE IF NOT EXISTS clients (
  id integer PRIMARY KEY,
  name text NOT NULL,
  passhash text,
  register_date text,
  last_login_date text,
  last_save_date text,
  last_login_ip text,
  banned boolean,
  spawn_x integer,
  spawn_y integer,
  hp integer,
  mp integer,
  stat_str integer,
  stat_agi integer,
  stat_int integer,
  stat_vit integer,
  int_unknown_1 integer,
  experience float,
  level integer,
  admin_level integer,
  stat_points integer,
  int_unknown_2 integer,
  weapon_equipped integer,
  hat_equipped integer,
  int_unknown_3 integer,
  int_unknown_4 integer,
  int_unknown_5 integer,
  gold float,
  clan text
);

CREATE TABLE IF NOT EXISTS inventory (
  id integer PRIMARY KEY,
  client_id integer,
  item_id integer,
  FOREIGN KEY(client_id) REFERENCES client(id)
);

CREATE TABLE IF NOT EXISTS unknown_list_1 (
  id integer PRIMARY KEY,
  client_id integer,
  list_element_id integer,
  FOREIGN KEY(client_id) REFERENCES client(id)
);

CREATE TABLE IF NOT EXISTS unknown_list_2 (
  id integer PRIMARY KEY,
  client_id integer,
  list_element_id integer,
  FOREIGN KEY(client_id) REFERENCES client(id)
);
