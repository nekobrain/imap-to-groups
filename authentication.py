#! /usr/bin/python3
# -*- coding: utf-8 -*-
from apiclient import discovery
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import googleapiclient.http
import os
import imaplib
import httplib2

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser])
    flags = flags.parse_args()
except ImportError:
    flags = None

class Connection:
    def __init__(self,client_secret):
        self.SCOPES = ['https://www.googleapis.com/auth/apps.groups.migration']
        self.APPLICATION_NAME = 'Groups Migrator'
        self.CLIENT_SECRET_FILE = client_secret

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'groups-migrator.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials
    def create_service(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        return discovery.build('groupsmigration', 'v1', http=http)

def media_upload(b):
    return googleapiclient.http.MediaIoBaseUpload(b, mimetype='message/rfc822')

class IMAP_connection:
    def __init__(self, server, user, password, port):
        self.IMAP_SERVER = server
        self.EMAIL_ACCOUNT = user
        self.PASSWORD = password
        self.PORT = port
    def connect(self):
        return imaplib.IMAP4_SSL(self.IMAP_SERVER, self.PORT)
    def log_in(self):
        return self.connect().login(self.EMAIL_ACCOUNT, self.PASSWORD)
    def list(self):
        self.log_in().list()
