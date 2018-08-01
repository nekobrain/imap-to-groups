#! /usr/bin/python3
# -*- coding: utf-8 -*-
import MySQLdb

class DB:
    def __init__(self, parameters, table_name):
        self.table_name = table_name
        self.parameters = parameters
        self.conn = None

    def connect(self):
        self.conn = MySQLdb.connect(self.parameters['MYSQL_HOST'], self.parameters['MYSQL_USER'], self.parameters['MYSQL_PASSWORD'], self.parameters['MYSQL_DB'])
    def create_table(self):
        query = '''CREATE TABLE %s (ID int PRIMARY KEY AUTO_INCREMENT, Sender text NOT NULL, Recipient text NOT NULL, Subject text NOT NULL, MessageId text NOT NULL, Migrated boolean NOT NULL, Timestamp text NOT NULL)''' % self.table_name
        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            return 'Ok!'
        except Exception as e:
            return e

    def select_all(self):
        query = "SELECT MessageId FROM " + self.table_name 
        messages = []
        cursor = self.conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        for msg in results:
            messages.append(msg[0])
        return messages

    def insert_record(self, sender, rcpt, subj, msg_id, migrated, ts):
        query = "INSERT INTO " + self.table_name + " (Sender, Recipient, Subject, MessageId, Migrated, Timestamp) VALUES (%s, %s, %s, %s, %s, %s)"
        try:
            cursor = self.conn.cursor()
            cursor.execute('SET NAMES utf8mb4')
            cursor.execute('SET CHARACTER SET utf8mb4')  
            cursor.execute('SET character_set_connection=utf8mb4')
            cursor.execute(query, (sender, rcpt, subj, msg_id, migrated, ts))
            self.conn.commit()
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute('SET NAMES utf8mb4')
            cursor.execute('SET CHARACTER SET utf8mb4')  
            cursor.execute('SET character_set_connection=utf8mb4')
            cursor.execute(query, (sender, rcpt, subj, msg_id, migrated, ts))
            self.conn.commit()
        return cursor
    def close_connection(self):
        return self.conn.close()
