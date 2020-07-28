# apc2mqtt
Post APCUPSD UPS data to MQTT broker with Home Assistant discovery.

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

# Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `HOMEASSISTANT_PREFIX` | `homeassistant` | The prefix for Home Assistant discovery. Must be the same as `discovery_prefix` in your Home Assistant configuration. |
| `MQTT_USER` | `None` | The user to send to the MQTT broker. |
| `MQTT_PASSWORD` | `None` | The password to send to the MQTT broker. |
| `MQTT_HOST` | `localhost` | IP address or hostname of the MQTT broker to connect to. |
| `MQTT_PORT` | `1883` | The port the MQTT broker is bound to. |
| `MQTT_TOPIC_PREFIX` | `apc` | The MQTT topic prefix. |
| `MQTT_TIMEOUT` | `300` | The timeout for the MQTT connection in seconds. |
| `MQTT_QOS` | `1` | The MQTT QoS level. |
| `INTERVAL` | `15` | How often (in seconds) apc2mqtt polls APCUPSD for UPS information.* |
| `UPS_ALIAS` | `apc` | Used to determine the first part of the object ID for each sensor's entity ID (`sensor.XXX_battery` for example). |
| `APCUPSD_HOST` | `127.0.0.1` | IP address or hostname of the host running APCUPSD. |
| `DEBUG` | `1` | Set to `1` to enable debug logging. |

\* By default, APCUPSD polls the UPS every 60 seconds. If you use a value lower than 60 here, you'll need to update your APCUPSD configuration (`/etc/apcupsd/apcupsd.conf`) by setting `POLLTIME X` where `X` is the interval in seconds.

# TODO
* Properly test everything
