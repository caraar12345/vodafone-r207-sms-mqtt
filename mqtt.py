import json
import paho.mqtt.client as mqtt
import config
import vodafone_connect
import constants
import ssl


class MqttClient:
    def __init__(
        self,
        client_id,
        vodafone_device,
        host=config.MQTT_SERVER,
        port=config.MQTT_PORT,
        username=config.MQTT_USERNAME,
        password=config.MQTT_PASSWORD,
        tls_enabled=config.MQTT_TLS_ENABLED,
    ):
        self.mqtt_discovery_prefix = config.MQTT_DISCOVERY_PREFIX
        self.client_id = client_id
        self.vodafone_device = vodafone_device
        self.mqttClient = mqtt.Client(client_id=client_id)
        self.mqttClient.enable_logger()
        self.mqttClient.username_pw_set(username, password)

        if tls_enabled:
            self.mqttClient.tls_set_context()

        self.mqttClient.connect(host, port)
        self.setUpMqttDiscovery()

    def setUpMqttDiscovery(self):
        topic = (
            self.mqtt_discovery_prefix
            + "/sensor/"
            + self.client_id
            + "/"
            + self.vodafone_device.serial_number
            + "/config"
        )
        state_topic = (
            self.mqtt_discovery_prefix
            + "/sensor/"
            + self.client_id
            + "/"
            + self.vodafone_device.serial_number
        )
        device = {
            "identifiers": [self.vodafone_device.serial_number],
            "name": self.vodafone_device.name,
            "model": "R207",
            "manufacturer": "Vodafone",
        }
        payload = {
            "latest_sms": {
                "name": f"{self.vodafone_device.name} Latest SMS",
                "state_topic": state_topic + "/received_sms",
                "value_template": "{{ value_json['content'] }}",
                "json_attributes_topic": state_topic + "/received_sms",
                "device": device,
                "unique_id": self.vodafone_device.serial_number + "_received_sms",
            },
            "battery": {
                "name": f"{self.vodafone_device.name} Battery",
                "state_topic": state_topic + "/device_status",
                "value_template": "{{ value_json['battery'] }}",
                "unit_of_measurement": "%",
                "device": device,
                "unique_id": self.vodafone_device.serial_number + "_battery",
            },
            "imei": {
                "name": f"{self.vodafone_device.name} IMEI",
                "state_topic": state_topic + "/device_status",
                "value_template": "{{ value_json['imei'] }}",
                "device": device,
                "unique_id": self.vodafone_device.serial_number + "_imei",
            },
            "serial": {
                "name": f"{self.vodafone_device.name} Serial",
                "state_topic": state_topic + "/device_status",
                "value_template": "{{ value_json['serial'] }}",
                "device": device,
                "unique_id": self.vodafone_device.serial_number + "_serial",
            },
            "signal": {
                "name": f"{self.vodafone_device.name} Signal Strength",
                "state_topic": state_topic + "/device_status",
                "value_template": "{{ value_json['signal'] }}",
                "unit_of_measurement": "%",
                "device": device,
                "unique_id": self.vodafone_device.serial_number + "_signal",
            },
            "network": {
                "name": f"{self.vodafone_device.name} Network",
                "state_topic": state_topic + "/device_status",
                "value_template": "{{ value_json['network'] }}",
                "device": device,
                "unique_id": self.vodafone_device.serial_number + "_network",
            },
            "wifi_enabled": {
                "name": f"{self.vodafone_device.name} Wi-Fi Enabled",
                "state_topic": state_topic + "/device_status",
                "value_template": "{{ value_json['wifi'] }}",
                "device": device,
                "unique_id": self.vodafone_device.serial_number + "_wifi_enabled",
            },
        }

        if config.WIFI_SETTINGS_TO_MQTT:
            payload["ssid"] = {
                "name": f"{self.vodafone_device.name} SSID",
                "state_topic": state_topic + "/device_status",
                "value_template": "{{ value_json['ssid'] }}",
                "device": device,
                "unique_id": self.vodafone_device.serial_number + "_ssid",
            }

            payload["wpa_psk"] = {
                "name": f"{self.vodafone_device.name} WPA2 PSK",
                "state_topic": state_topic + "/device_status",
                "value_template": "{{ value_json['wpa_psk'] }}",
                "device": device,
                "unique_id": self.vodafone_device.serial_number + "_wpa_psk",
            }

            payload["ssid_broadcast"] = {
                "name": f"{self.vodafone_device.name} SSID Broadcast",
                "state_topic": state_topic + "/device_status",
                "value_template": "{{ value_json['ssid_broadcast'] }}",
                "device": device,
                "unique_id": self.vodafone_device.serial_number + "_ssid_broadcast",
            }

        for entity in payload.keys():
            topic = (
                self.mqtt_discovery_prefix
                + "/sensor/"
                + "vodafone_"
                + self.vodafone_device.serial_number
                + "/"
                + entity
                + "/config"
            )

            self.mqttClient.publish(topic, json.dumps(payload[entity]), retain=True)

    def publishNewSms(self, smsParsedDict):
        smsParsedDict["timestamp"] = smsParsedDict["timestamp"].strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        try:
            self.mqttClient.publish(
                self.mqtt_discovery_prefix
                + "/sensor/"
                + self.client_id
                + "/"
                + self.vodafone_device.getInformation()["SerialNumber"]
                + "/received_sms",
                json.dumps(smsParsedDict),
            )
        except ssl.SSLEOFError as e:
            pass

    def publishDeviceStatus(self):
        device_status = self.vodafone_device.mqtt_description
        try:
            self.mqttClient.publish(
                self.mqtt_discovery_prefix
                + "/sensor/"
                + self.client_id
                + "/"
                + self.vodafone_device.getInformation()["SerialNumber"]
                + "/device_status",
                json.dumps(device_status),
            )
        except ssl.SSLEOFError as e:
            pass


if __name__ == "__main__":
    vodafone_device = vodafone_connect.VodafoneDevice(
        constants.DEFAULT_ROUTER_IP, constants.DEFAULT_ADMIN_PWD
    )
    newMqtt = MqttClient(client_id="aaroncarsontest", vodafone_device=vodafone_device)
    newMqtt.setUpMqttDiscovery()
    newMqtt.mqttClient.publish("TEST/vodafone-r207-sms-mqtt", "TESTING")
