#!/usr/bin/python
import os
import time
import json
from prettytable import PrettyTable
import paho.mqtt.client as paho
from apcaccess import status as apc
import logging

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

DEBUG = os.getenv('DEBUG') == '1'
HOMEASSISTANT_PREFIX = os.getenv('HOMEASSISTANT_PREFIX', 'homeassistant')
MQTT_USER = os.getenv('MQTT_USER')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
MQTT_TOPIC_PREFIX = os.getenv('MQTT_TOPIC_PREFIX', 'apc').lower()
MQTT_TIMEOUT = int(os.getenv('MQTT_TIMEOUT', '300'))
INTERVAL = float(os.getenv('INTERVAL', 15))
UPS_ALIAS = os.getenv('UPS_ALIAS','apc').lower().replace(" ", "_").replace('.', '_')
APCUPSD_HOST = os.getenv('APCUPSD_HOST','127.0.0.1')
MQTT_QOS = int(os.getenv('MQTT_QOS', 1))
DISCOVERY_TOPIC = HOMEASSISTANT_PREFIX + '/sensor/apc/{}/config'

mqtt = paho.Client()
mqtt.username_pw_set(username=MQTT_USER,password=MQTT_PASSWORD)
mqtt.will_set(MQTT_TOPIC_PREFIX + '/status', 'offline', qos=MQTT_QOS, retain=True)
mqtt.connect(MQTT_HOST, MQTT_PORT, MQTT_TIMEOUT)
mqtt.publish(MQTT_TOPIC_PREFIX + '/status', 'online', qos=MQTT_QOS, retain=True)

t = PrettyTable(['Key','Value'])
t.add_row(['MQTT_USER', MQTT_USER])
t.add_row(['MQTT_PASSWORD', MQTT_PASSWORD])
t.add_row(['MQTT_HOST', MQTT_HOST])
t.add_row(['INTERVAL', INTERVAL])
t.add_row(['UPS_ALIAS', UPS_ALIAS])
t.add_row(['ACPUPSD_HOST', APCUPSD_HOST])
# print the table
logger.info(t)

def mqtt_send(topic, payload, retain=False):
    try:
        if DEBUG:
            logger.info(f'Sending to MQTT: {topic}: {payload}')
        mqtt.publish(topic, payload=payload, qos=MQTT_QOS, retain=retain)

    except Exception as e:
        logger.info(f'MQTT Publish Failed: {e}')

def send_homeassistant_registration(sensorname):
    """Register an MQTT sensor for a each data topic."""
    discovery_sensorname = sensorname.lower().replace(" ", "_").replace('.', '_')
    registration_topic = DISCOVERY_TOPIC.format(discovery_sensorname)
    registration_packet = {
        'name': f"{MQTT_TOPIC_PREFIX.title()} {sensorname}",
        'unique_id': f'{MQTT_TOPIC_PREFIX}_{registration_topic}',
        'availability_topic': MQTT_TOPIC_PREFIX + '/status',
        'payload_available': 'online',
        'payload_not_available': 'offline',
        'state_topic': f'{MQTT_TOPIC_PREFIX}/{UPS_ALIAS}_{sensorname}'
    }
    logger.info(f'Registering {sensorname} with Home Assistant: {registration_topic}: {registration_packet}')
    mqtt_send(registration_topic, json.dumps(registration_packet), retain=True)

def main():
    mqtt.loop_start()
    ups = apc.parse(apc.get(host=APCUPSD_HOST))
    HOSTNAME = ups.get('HOSTNAME', 'apcupsd-mqtt')
    MQTT_TOPIC_PREFIX_UPS = MQTT_TOPIC_PREFIX + "/" + UPS_ALIAS + "_"
    alias = UPS_ALIAS.lower().replace(" ", "_").replace('.', '_')
    ups_data = apc.parse(apc.get(host=APCUPSD_HOST), strip_units=True)
    for data_topic in ups_data:
        send_homeassistant_registration(str(data_topic).lower().replace(" ", "_").replace('.', '_'))
    while True:
        ups_data = apc.parse(apc.get(host=APCUPSD_HOST), strip_units=True)
        for data_topic in ups_data:
            topic_id = MQTT_TOPIC_PREFIX_UPS + str(data_topic).lower().replace(" ", "_").replace('.', '_')
            mqtt_send( topic_id, str(ups_data[data_topic]) )
        time.sleep(INTERVAL)
        
if __name__ == '__main__':
    main()
