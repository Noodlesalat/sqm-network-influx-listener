#!/usr/bin/env python

import configparser
import io
from influxdb import InfluxDBClient

# load config file
config = configparser.ConfigParser()
config.read("../config.ini")

# connect to influx database
client = InfluxDBClient(host=config['influx']['host'], port=config['influx']['port'])

print("Create database")
client.create_database('sqm-network')