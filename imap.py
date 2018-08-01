#! /usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import imaplib
import httplib2
import os
import getpass
import sys
import datetime
import sqlconnection
import sqlqueries
from io import BytesIO
import googleapiclient.http
from authentication import Connection
from authentication import media_upload

# EXAMPLE IMAP SERVER
IMAP_SERVER = 'source.server.com'
# EMAIL ACCOUNT
EMAIL_ACCOUNT = 'source@user.com'
# PORT
PORT = 993
# ACCOUNT PASSWORD
PASSWORD = getpass.getpass()

#def process_mailbox(M, OUTPUT_DIRECTORY):
def sanitize_group(string):
    string = string.split('@')
    string = string[0]
    return string

def sanitize_sender(header):
    invalid_characters = ["\""]
    for char in invalid_characters:
        if char in header:
            header = header.replace(char,'')
    return header

def sanitize_rcpt(header):
    invalid_characters = ["\"", "<", ">"]
    for char in invalid_characters:
        if char in header:
            header = header.replace(char,'')
    return header


def process_mailbox(M, service, group_name, db, migrated_messages):
    """
    Dump all emails in the folder to files in output directory.
    """
    try:
        status, folders = M.list()
        folders_array = []
    except Exception as e:
        print(e)

    for folder in folders:
        folder = folder.split('\"/\"')
        folders_array.append(folder[-1].strip())
    for folder_name in folders_array:
        print(folder_name)
        rv, data = M.select(folder_name)
        total_msg = data[0]
        if rv == 'OK':
            print("Processing mailbox: ", folder_name)
            print("Folder has " + total_msg + " messages. Starting...")
            rv, data = M.search(None, "ALL")
            if rv != 'OK':
                print("No messages found!")
                return

            for num in data[0].split():
                b = BytesIO()
                timestamp = datetime.datetime.now()
                while True:
                    try:
                        try:
                            rv, msg_id = M.fetch(num, '(BODY.PEEK[HEADER.FIELDS (Message-ID)])')
                            msg_id = msg_id[0][1].strip().split(" ")[1]
                            if msg_id in migrated_messages:
                                print("Message", num, "already migrated, skipping...")
                                b = "skip"
                                break
                        except Exception:
                            print("Could not peek headers.")
                        rv, headers = M.fetch(num, '(BODY.PEEK[HEADER.FIELDS (To From Subject Message-ID)])')
                        headers = headers[0][1].split("\r\n")
                        try:
                            rcpt = sanitize_rcpt([header for header in headers if "To: " in header][0].split("To: ")[1])
                        except Exception:
                            try:
                                rcpt = sanitize_rcpt([header for header in headers if "to: " in header][0].split("to: ")[1])
                            except Exception:
                                rcpt = "Unknown recipient"
                        try:
                            sender = sanitize_sender([header for header in headers if "From: " in header][0].split("From: ")[1])
                        except Exception:
                            try:
                                sender = sanitize_sender([header for header in headers if "from: " in header][0].split("from: ")[1])
                            except Exception:
                                sender = "Unknown sender"
                        try:
                            subject = [header for header in headers if "Subject: " in header][0].split("Subject: ")[1]
                        except Exception:
                            try:
                                subject = [header for header in headers if "subject: " in header][0].split("subject: ")[1]
                            except Exception:
                                subject = "No subject"
                        rv, data = M.fetch(num, '(RFC822)')
                        b.write(data[0][1])
                        try:
                            msg_id = [header for header in headers if "Message" in header][0].split(" ")[1]
                        except Exception:
                            msg_id = "No Message-Id could be parsed."
                        break
                    except Exception as e:
                        print("Errore!")
                        print(e.message)
                        M = imap_connection(IMAP_SERVER,EMAIL_ACCOUNT,PASSWORD, PORT)
                        M.select(folder_name)
                if rv != 'OK':
                    print("ERROR getting message", num)
                    return
                if b == "skip":
                    continue
                print("Writing message", num, "of", total_msg)
                to_upload = googleapiclient.http.MediaIoBaseUpload(b, mimetype='message/rfc822')
                to_upload = media_upload(b)

                try:
                    request = service.archive().insert(groupId=group_name,media_body=to_upload).execute()
                    db.insert_record(sender, rcpt, subject, msg_id, 1, timestamp)
                    if request['responseCode'] == "SUCCESS":
                        print("Message migrated successfully.")
                except Exception as e:
                    print("Could not migrate message.")
                    print(e) 
                    try:
                        print(sender, rcpt, subject, msg_id)
                        print(type(sender), type(rcpt), type(subject), type(msg_id))
                    except Exception:
                        continue
                    db.insert_record(sender, rcpt, subject, msg_id, 0, timestamp)
        else:
            print("ERROR: Unable to open mailbox ", rv)

def imap_connection(server, user, password, port):
    if port == 993:
        M = imaplib.IMAP4_SSL(server, port)
    else:
        M = imaplib.IMAP4(server, port)
    M.login(EMAIL_ACCOUNT, PASSWORD)
    return M

def main():
    conn_parameters = sqlconnection.parameters
    CLIENT_SECRET_FILE = '/PATH/TO/CLIENT_SECRET_FILE'
    service = Connection(CLIENT_SECRET_FILE).create_service()
    group = 'destination@group.com'
    table_name = sanitize_group(group)
    db = sqlqueries.DB(conn_parameters,table_name)
    db.connect()
    print("Creating table...")
    create_table = db.create_table()
    print("Table created.")
    migrated_messages = []
    if create_table[1] == 'Table \'' + table_name + '\' already exists':
        print("Table exists, skipping creation...")
        migrated_messages = db.select_all()
    print("Starting migration...")
    M = imap_connection(IMAP_SERVER, EMAIL_ACCOUNT, PASSWORD, PORT)
    process_mailbox(M, service, group, db, migrated_messages)
    try:
        M.close()
        M.logout()
    except Exception as e:
        print(e.message)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user.")
