#!/usr/bin/env python

import logging
logging.basicConfig(level=logging.DEBUG)
import time

import serial

import tweepy


consumer_key = ""
consumer_secret = ""

access_token = ""
access_token_secret = ""

#port_address = '/dev/ttyUSB1'
port_address = 4  # 4 = COM5
baud = 9600

port_retries = 10
api_retries = 10

port_wait = 10  # seconds between port reads
api_wait_on_error = 10  # seconds to wait if api status update fails
update_wait = 10  # seconds per update
# if the main loop tried to sleep for less than this, than just exit
min_sleep = 5  # seconds
wait_buffer = 0.1  # seconds, additional time to wait every loop

threshold = 400


def parse_line(line):
    try:
        return int(line.strip())
    except:
        return -1


def open_port():
    logging.debug("Attempting to open port: %s, %s" % (port_address, baud))
    p = serial.Serial(port_address, baud)
    p.close()
    p.open()
    return p


def get_twitter_api():
    logging.debug("Attempting to open twitter api")
    auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    return api


def value_to_status(value):
    logging.debug("Value [%s] to status [threshold = %s]" % (value, threshold))
    if value > threshold:
        return 2
    return 1


def main():
    api = None
    port = None
    value = -1

    api_tries = 0
    port_tries = 0

    last_port_read = 0

    states = ['Unknown', 'Empty', 'In Use']
    status = 0
    while True:
        # try to open port
        if port is None:
            try:
                port = open_port()
            except Exception as E:
                port = None
                logging.debug("Port Open Failed: %s" % E)
                # so that this isn't endlessly called
                last_port_read = time.time()

        # try to open twitter api
        if api is None:
            try:
                api = get_twitter_api()
                s = "Sensor online at %s" % time.asctime()
                api.update_status(s)
            except Exception as E:
                api = None
                logging.debug("API Open Failed: %s" % E)

        # try to read port
        port_tries = 0
        pt = time.time()
        while (port is not None) and (pt - last_port_read > port_wait) and\
                (port_tries < port_retries):
            try:
                value = parse_line(port.readline())
            except Exception as E:
                value = -1
                logging.debug("Port Read Failed: %s" % E)
            if value == -1:
                port_tries += 1
            else:
                port_tries = 0
                last_port_read = pt
                break

        # if port read failed, then release port
        if port_tries >= port_retries:
            logging.debug("Port read fails > port_retries, releasing port")
            port = None

        try:
            new_status = value_to_status(value)
        except Exception as E:
            new_status = status
            logging.debug("Value to Status Failed: %s" % E)

        api_tries = 0
        while (new_status != status) and\
                (api is not None) and (api_tries < api_retries):
            try:
                s = "%s at %s" % (states[new_status], time.asctime())
                logging.debug("Updating status to %s" % s)
                api.update_status(s)
                api_tries = 0
                status = new_status
                break
            except Exception as E:
                time.sleep(api_wait_on_error)
                api_tries += 1
                logging.debug("Update Status Failed: %s" % E)

        if (new_status != status) and (api_tries >= api_retries):
            logging.debug("API update fails > api_retries, releasing API")
            api = None

        t = time.time()
        pd = last_port_read + port_wait - t + wait_buffer
        #sleep = max(min(pd, ud), 0)
        sleep = max(pd, 0)
        logging.debug("Now %s" % t)
        logging.debug("Status: %s" % status)
        logging.debug("last_port_read %s" % last_port_read)
        logging.debug("sleeping %s" % sleep)
        if sleep > min_sleep:
            time.sleep(sleep)
        else:
            #time.sleep(min_sleep)
            break
    if api is not None:
        try:
            s = "Sensor offline at %s" % time.asctime()
            api.update_status(s)
        except Exception as E:
            logging.debug("Failed to send offline notification")
    print "Loop exited at %s" % time.time()
    for k, v in locals().iteritems():
        print "%s : %s" % (k, v)

if __name__ == '__main__':
    main()
