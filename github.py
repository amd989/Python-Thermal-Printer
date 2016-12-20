#!/usr/bin/python

# A simple script to poll Github for interesting events and
# print them on the Adafruit IoT Printer.

# It turns out that etags are helpful but not sufficient for
# "bookmarking" github requests. Due to the way Github implements
# etags, you can get redundant data if some portion of an object
# you've already seen changes in some way. So we use etags as the
# "first line of defense" to keep us from getting in rate limiting
# trouble, and other mechanisms to detect redundant info.

from __future__ import print_function
import sqlite3
import github3
from Adafruit_Thermal import *

# Grab Github config from the config file as globals
config = ConfigParser.SafeConfigParser({'skip-org-events': 'true', 'filename': 'printerdata.db'})
config.read('options.cfg')
github_username = config.get('github', 'username')
github_token = config.get('github', 'token')
skip_org_events = config.getboolean('github', 'skip-org-events')
database_filename = config.get('database', 'filename')

# Other globals
printer = Adafruit_Thermal("/dev/ttyAMA0", 9600, timeout=5)


def setup_database(conn):
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS github_etags (request_name text primary key, etag text)')
    c.execute('CREATE TABLE IF NOT EXISTS github_ids (request_name text primary key, id integer)')
    conn.commit()
    c.close()


def connect_database():
    try:
        conn = sqlite3.connect(database_filename)
        setup_database(conn)
        return conn
    except Exception, e:
        print("connect_database encountered exception: %s %s" % (str(type(e)), str(e)))
        return None

def get_etag(conn, request_name):
    try:
        etag = None
        c = conn.cursor()
        c.execute('SELECT etag FROM github_etags WHERE request_name = ?', (request_name,))
        row = c.fetchone()
        if row:
            etag = row[0]
        c.close()
        return etag
    except Exception, e:
        print("get_etag encountered exception: %s %s" % (str(type(e)), str(e)))
        return None

def save_etag(conn, request_name, etag):
    try:
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO github_etags (request_name, etag) VALUES (?, ?)', (request_name, etag))
        conn.commit()
        c.close()
    except Exception, e:
        print("save_etag encountered exception: %s %s" % (str(type(e)), str(e)))


def get_id(conn, request_name):
    try:
        id = 0
        c = conn.cursor()
        c.execute('SELECT id FROM github_ids WHERE request_name = ?', (request_name,))
        row = c.fetchone()
        if row:
            id = long(row[0])
        c.close()
        return id
    except Exception, e:
        print("get_id encountered exception: %s %s" % (str(type(e)), str(e)))
        return 0

def save_id(conn, request_name, id):
    try:
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO github_ids (request_name, id) VALUES (?, ?)', (request_name, id))
        conn.commit()
        c.close()
    except Exception, e:
        print("save_id encountered exception: %s %s" % (str(type(e)), str(e)))


def connect_github():
    try:
        return github3.login(github_username, token=github_token)
    except Exception, e:
        print("connect_github encountered exception: %s %s" % (str(type(e)), str(e)))
        return None


def print_message_header(timestamp=None):
    """
    Print message headers that look like the twitter.py message headers.
    """
    printer.inverseOn()
    printer.print(' ' + '{:<31}'.format('Github Event'))
    printer.inverseOff()
    if timestamp is not None:
        printer.underlineOn()
        printer.print('{:<32}'.format(timestamp))
        printer.underlineOff()


def main():
    conn = connect_database()
    if conn is None:
        printer.print('github.py: could not connect to database!')
        printer.feed(3)
        exit(1)
    ghclient = connect_github()
    if ghclient is None:
        printer.print('github.py: could not authenticate with Github')
        printer.feed(3)
        exit(1)

    my_events_etag = get_etag(conn, 'my_events')
    my_events_last_id = get_id(conn, 'my_events')
    my_events_highest_id = -1
    my_events = ghclient.me().received_events(etag=my_events_etag)
    for e in my_events:
        event = e.as_dict()
        # We keep track of event IDs here in case the etag doesn't prevent
        # us from getting events we've already seen (although ids being
        # sequential is based on anecdotal evidence).
        event_id = long(event['id'])
        if my_events_highest_id == -1 or event_id > my_events_highest_id:
            my_events_highest_id = event_id
        if event_id <= my_events_last_id:
            continue
        if skip_org_events and 'org' in event:
            continue
        if event['type'] == 'WatchEvent':
            print_message_header(event['created_at'])
            printer.print(event['actor']['login'] + ' starred repo ' + event['repo']['name'])
            printer.feed(3)
        elif event['type'] == 'ForkEvent':
            print_message_header(event['created_at'])
            printer.print(event['actor']['login'] + ' forked repo ' + event['repo']['name'])
            printer.feed(3)
    save_etag(conn, 'my_events', my_events.etag)
    if my_events_highest_id > my_events_last_id:
        save_id(conn, 'my_events', my_events_highest_id)

    my_followers_etag = get_etag(conn, 'my_followers')
    my_followers = ghclient.me().followers(etag=my_followers_etag)
    for f in my_followers:
        follower = f.as_dict()
        print_message_header()
        printer.print('You were followed by ' + follower['login'])
        printer.feed(3)
    save_etag(conn, 'my_followers', my_followers.etag)

    conn.close()
    exit(0)

if __name__ == '__main__':
    main()
