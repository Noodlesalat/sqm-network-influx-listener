#!/usr/bin/env python

import socketserver, subprocess, sys
import json
import configparser
import io
import logging
from threading import Thread
from datetime import datetime
from influxdb import InfluxDBClient

# set logging options
logging.basicConfig(level=logging.INFO)

# load config file
config = configparser.ConfigParser()
config.read("../config.ini")

# connect to influx database
client = InfluxDBClient(host=config['influx']['host'], port=config['influx']['port'])
client.switch_database(config['influx']['database'])

class SingleTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # self.request is the client connection
        data = self.request.recv(1024)
        payload = data.decode('utf-8').split(",")

        # check if transmission is interesting
        if (len(data) != 66 and len(payload) != 6):
            logging.info("Got bogus data from: %s", self.client_address[0])
            self.request.send('Thanks for playing!'.encode('utf-8'))
            self.request.close()
        else:
            # get interesting values from report
            current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            serial = payload[6].replace('\r', '').replace('\n', '')
            brightness = payload[1]
            temperature = payload[5]

            # log received report
            logging.info("%s: Got report from: %s - %s mpsas; %s °C", current_time, serial, brightness, temperature)

            # prepare data for influx
            influxdata = [{
                "measurement": "reading",
                "tags": {
                    "serial": serial,
                },
                "time": current_time,
                "fields": {
                    "brightness": float(brightness[:-1]),
                    "temperature": float(temperature[:-1])
                }
            }]

            # write to database and close connection
            client.write_points(influxdata)
            self.request.close()

class SimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)

if __name__ == "__main__":
    server = SimpleServer((config['general']['host'], int(config['general']['port'])), SingleTCPHandler)
    # terminate with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)