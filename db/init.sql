CREATE TABLE email_and_id ( id INT PRIMARY KEY, email VARCHAR(255) );
CREATE TABLE phonenumber_and_id ( id INT PRIMARY KEY, phonenumber VARCHAR(255) );
INSERT INTO email_and_id (id, email) VALUES (1, 'Violettanik27@yandex.ru'), (2, 'Violettanik27062005@yandex.ru');
INSERT INTO phonenumber_and_id (id, phonenumber) VALUES (1, '89858782912'), (2, '89169329062'); 

CREATE TABLE hba ( lines text );
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf';
INSERT INTO hba (lines) VALUES ('host replication all 0.0.0.0/0 md5');
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf';
SELECT pg_reload_conf();

CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'Qq12345' LOGIN;
SELECT pg_create_physical_replication_slot('replication_slot');
