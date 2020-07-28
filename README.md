# apc2mqtt
Post APCUPSD ups data to MQTT Broker with Home Assistant discovery.

 # Instructions

clone repo:
`git clone `

enter directory:
`cd apc2mqtt`

build image:
`docker build -t apc2mqtt -f Dockerfile .`

docker-compose:
`docker-compose up -d`

Example compose file with all possible environmental variables listed:
```yaml
version: '3'
services:
  apc2mqtt:
    container_name: apc2mqtt
    image: apc2mqtt:latest
    environment:
    - HOMEASSISTANT_PREFIX=homeassistant
    - MQTT_USER=user
    - MQTT_PASSWORD=password
    - MQTT_HOST=10.1.1.4
    - MQTT_PORT=1883
    - MQTT_TOPIC_PREFIX=apc
    - MQTT_TIMEOUT=15
    - MQTT_QOS=1
    - INTERVAL=15
    - UPS_ALIAS=ups
    - APCUPSD_HOST=10.1.1.4
    - DEBUG=1
    restart: unless-stopped
```

# TODO
* Properly test everything

* Make sensor names more friendly