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

DEGREE = "°"
CONF_RESOURCES = "resources"
VOLT = "V"
ELECTRICAL_CURRENT_AMPERE = "A"
ELECTRICAL_VOLT_AMPERE = f"{VOLT}{ELECTRICAL_CURRENT_AMPERE}"
FREQUENCY_HERTZ = "Hz"
POWER_WATT = "W"
TEMP_CELSIUS = f"{DEGREE}C"
TIME_MINUTES = "min"
TIME_SECONDS = "s"
UNIT_PERCENTAGE = "%"

SENSOR_TYPES = {
    "alarmdel": ["Alarm Delay", "", "mdi:alarm"],
    "ambtemp": ["Ambient Temperature", "", "mdi:thermometer"],
    "apc": ["Status Data", "", "mdi:information-outline"],
    "apcmodel": ["Model", "", "mdi:information-outline"],
    "badbatts": ["Bad Batteries", "", "mdi:information-outline"],
    "battdate": ["Battery Replaced", "", "mdi:calendar-clock"],
    "battstat": ["Battery Status", "", "mdi:information-outline"],
    "battv": ["Battery Voltage", VOLT, "mdi:flash"],
    "bcharge": ["Battery", UNIT_PERCENTAGE, "mdi:battery"],
    "cable": ["Cable Type", "", "mdi:ethernet-cable"],
    "cumonbatt": ["Total Time on Battery", "", "mdi:timer-outline"],
    "date": ["Status Date", "", "mdi:calendar-clock"],
    "dipsw": ["Dip Switch Settings", "", "mdi:information-outline"],
    "dlowbatt": ["Low Battery Signal", "", "mdi:clock-alert"],
    "driver": ["Driver", "", "mdi:information-outline"],
    "dshutd": ["Shutdown Delay", "", "mdi:timer-outline"],
    "dwake": ["Wake Delay", "", "mdi:timer-outline"],
    "endapc": ["Date and Time", "", "mdi:calendar-clock"],
    "extbatts": ["External Batteries", "", "mdi:information-outline"],
    "firmware": ["Firmware Version", "", "mdi:information-outline"],
    "hitrans": ["Transfer High", VOLT, "mdi:flash"],
    "hostname": ["Hostname", "", "mdi:information-outline"],
    "humidity": ["Ambient Humidity", UNIT_PERCENTAGE, "mdi:water-percent"],
    "itemp": ["Internal Temperature", TEMP_CELSIUS, "mdi:thermometer"],
    "lastxfer": ["Last Transfer", "", "mdi:transfer"],
    "linefail": ["Input Voltage Status", "", "mdi:information-outline"],
    "linefreq": ["Line Frequency", FREQUENCY_HERTZ, "mdi:information-outline"],
    "linev": ["Input Voltage", VOLT, "mdi:flash"],
    "loadpct": ["Load", UNIT_PERCENTAGE, "mdi:gauge"],
    "loadapnt": ["Load Apparent Power", UNIT_PERCENTAGE, "mdi:gauge"],
    "lotrans": ["Transfer Low", VOLT, "mdi:flash"],
    "mandate": ["Manufacture Date", "", "mdi:calendar"],
    "masterupd": ["Master Update", "", "mdi:information-outline"],
    "maxlinev": ["Input Voltage High", VOLT, "mdi:flash"],
    "maxtime": ["Battery Timeout", "", "mdi:timer-off-outline"],
    "mbattchg": ["Battery Shutdown", UNIT_PERCENTAGE, "mdi:battery-alert"],
    "minlinev": ["Input Voltage Low", VOLT, "mdi:flash"],
    "mintimel": ["Shutdown Time", "", "mdi:timer-outline"],
    "model": ["Model", "", "mdi:information-outline"],
    "nombattv": ["Battery Nominal Voltage", VOLT, "mdi:flash"],
    "nominv": ["Nominal Input Voltage", VOLT, "mdi:flash"],
    "nomoutv": ["Nominal Output Voltage", VOLT, "mdi:flash"],
    "nompower": ["Nominal Output Power", POWER_WATT, "mdi:flash"],
    "nomapnt": ["Nominal Apparent Power", ELECTRICAL_VOLT_AMPERE, "mdi:flash"],
    "numxfers": ["Transfer Count", "", "mdi:counter"],
    "outcurnt": ["Output Current", ELECTRICAL_CURRENT_AMPERE, "mdi:flash"],
    "outputv": ["Output Voltage", VOLT, "mdi:flash"],
    "reg1": ["Register 1 Fault", "", "mdi:information-outline"],
    "reg2": ["Register 2 Fault", "", "mdi:information-outline"],
    "reg3": ["Register 3 Fault", "", "mdi:information-outline"],
    "retpct": ["Restore Requirement", UNIT_PERCENTAGE, "mdi:battery-alert"],
    "selftest": ["Last Self Test", "", "mdi:calendar-clock"],
    "sense": ["Sensitivity", "", "mdi:information-outline"],
    "serialno": ["Serial Number", "", "mdi:information-outline"],
    "starttime": ["Startup Time", "", "mdi:calendar-clock"],
    "statflag": ["Status Flag", "", "mdi:information-outline"],
    "status": ["Status", "", "mdi:information-outline"],
    "stesti": ["Self Test Interval", "", "mdi:information-outline"],
    "timeleft": ["Time Left", "", "mdi:clock-alert"],
    "tonbatt": ["Time on Battery", "", "mdi:timer-outline"],
    "upsmode": ["Mode", "", "mdi:information-outline"],
    "upsname": ["Name", "", "mdi:information-outline"],
    "version": ["Daemon Info", "", "mdi:information-outline"],
    "xoffbat": ["Transfer from Battery", "", "mdi:transfer"],
    "xoffbatt": ["Transfer from Battery", "", "mdi:transfer"],
    "xonbatt": ["Transfer to Battery", "", "mdi:transfer"],
}

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
DISCOVERY_TOPIC = HOMEASSISTANT_PREFIX + '/sensor/' + MQTT_TOPIC_PREFIX + '/{}/config'

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

def send_homeassistant_registration(sensordata):
    """Register an MQTT sensor for a each data topic."""
    discovery_sensorname = sensor_name(sensordata)
    registration_topic = DISCOVERY_TOPIC.format(discovery_sensorname)
    registration_packet = {
        'name': f"{MQTT_TOPIC_PREFIX.title()} {discovery_sensorname.title()}",
        'unique_id': f'{MQTT_TOPIC_PREFIX}_{registration_topic}',
        'icon': sensordata[2],
        'availability_topic': MQTT_TOPIC_PREFIX + '/status',
        'unit_of_measurement': sensordata[1],
        'payload_available': 'online',
        'payload_not_available': 'offline',
        'state_topic': f'{MQTT_TOPIC_PREFIX}/{UPS_ALIAS}_{discovery_sensorname}'
    }
    logger.info(f'Registering {discovery_sensorname} with Home Assistant: {registration_topic}: {registration_packet}')
    mqtt_send(registration_topic, json.dumps(registration_packet), retain=True)

def main():
    mqtt.loop_start()
    ups = apc.parse(apc.get(host=APCUPSD_HOST))
    HOSTNAME = ups.get('HOSTNAME', 'apcupsd-mqtt')
    MQTT_TOPIC_PREFIX_UPS = MQTT_TOPIC_PREFIX + "/" + UPS_ALIAS + "_"
    alias = UPS_ALIAS.lower().replace(" ", "_").replace('.', '_')
    ups_data = apc.parse(apc.get(host=APCUPSD_HOST), strip_units=True)
    for data_topic in ups_data:
        data_information = sensor_data(data_topic)
        send_homeassistant_registration(data_information)
    while True:
        ups_data = apc.parse(apc.get(host=APCUPSD_HOST), strip_units=True)
        for data_topic in ups_data:
            data_information = sensor_data(data_topic)
            topic_id = MQTT_TOPIC_PREFIX_UPS + sensor_name(data_information)
            mqtt_send( topic_id, str(ups_data[data_topic]) )
        time.sleep(INTERVAL)
        
def sensor_data(apc_data_name):
    if apc_data_name.lower() not in SENSOR_TYPES:
        SENSOR_TYPES[apc_data_name.lower()] = [
            apc_data_name.title(),
            "",
            "mdi:information-outline",
        ]
    return SENSOR_TYPES[apc_data_name.lower()]

def sensor_name(sensordata):
    return sensordata[0].lower().replace(" ", "_").replace('.', '_')

if __name__ == '__main__':
    main()
