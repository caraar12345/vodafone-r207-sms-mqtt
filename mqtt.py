import paho.mqtt.client as mqtt
import config
import vodafone_connect
import constants


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
        payload = None
        self.mqttClient.publish(topic, payload, retain=True)


if __name__ == "__main__":
    newMqtt = MqttClient(
        client_id="aaroncarsontest",
        vodafone_device=vodafone_connect.VodafoneDevice(
            constants.DEFAULT_ROUTER_IP, constants.DEFAULT_ADMIN_PWD
        ),
    )
    newMqtt.setUpMqttDiscovery()
    newMqtt.mqttClient.publish("TEST/vodafone-r207-sms-mqtt", "TESTING")
