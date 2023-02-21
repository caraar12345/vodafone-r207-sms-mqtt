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

    def setUpMqttDiscovery(self):
        topic = (
            self.mqtt_discovery_prefix
            + "/sensor/"
            + self.client_id
            + "/"
            + self.vodafone_device.getInformation()["SerialNumber"]
            + "/config"
        )
        payload = json.dumps(
            {
                "name": f"R207 Latest SMS",
                "state_topic": self.mqtt_discovery_prefix
                + "/sensor/"
                + self.client_id
                + "/"
                + self.vodafone_device.getInformation()["SerialNumber"]
                + "/received_sms",
            }
        )

        self.mqttClient.publish(topic, payload, retain=True)

        # name: SMS2MQTT Latest Message
        # state_topic: sms2mqtt/received
        # value_template: "{{ value_json['text'] }}"
        # unique_id: sms2mqtt_received_sms_1
        # json_attributes_topic: sms2mqtt/received
        # availability_topic: sms2mqtt/connected
        # payload_available: "1"
        # payload_not_available: "0"
        # state_class: measurement

    def publishNewSms(self, smsParsedDict):
        smsParsedDict["timestamp"] = smsParsedDict["timestamp"].strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        self.setUpMqttDiscovery()

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


if __name__ == "__main__":
    vodafone_device = vodafone_connect.VodafoneDevice(
        constants.DEFAULT_ROUTER_IP, constants.DEFAULT_ADMIN_PWD
    )
    newMqtt = MqttClient(client_id="aaroncarsontest", vodafone_device=vodafone_device)
    newMqtt.setUpMqttDiscovery()
    newMqtt.mqttClient.publish("TEST/vodafone-r207-sms-mqtt", "TESTING")
