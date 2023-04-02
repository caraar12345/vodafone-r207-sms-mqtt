import time
from utils import *
import db
import mqtt
import config


if __name__ == "__main__":
    voda_logger.warning("Starting...")
    import constants
    import vodafone_connect

    router_ip = (
        config.ROUTER_ADDRESS if config.ROUTER_ADDRESS else constants.DEFAULT_ROUTER_IP
    )
    admin_pwd = (
        config.ADMIN_PASSWORD if config.ADMIN_PASSWORD else constants.DEFAULT_ADMIN_PWD
    )
    ssl = config.ROUTER_SSL if config.ROUTER_SSL else False
    ssl_root = config.ROUTER_SSL_ROOT if config.ROUTER_SSL_ROOT else None

    vodafone = vodafone_connect.VodafoneDevice(
        router_ip, admin_pwd, ssl, ssl_root, config.WIFI_SETTINGS_TO_MQTT
    )

    mqttCli = mqtt.MqttClient("vodafone-r207-sms-mqtt", vodafone_device=vodafone)

    mariaDb = db.DatabaseInstance()
    mariaDb.dbConnect()
    mariaDb.dbTablePrep()

    while True:
        sms_list = vodafone.getSmsList()
        if sms_list == None:
            pass

        elif type(sms_list["Message"]) == dict:
            msgHandler(sms_list["Message"], mariaDb, mqttCli, vodafone, single=True)

        else:
            for msg in sms_list["Message"]:
                msgHandler(msg, mariaDb, mqttCli, vodafone, single=False)

        vodafone.refreshDeviceStatus()
        mqttCli.publishDeviceStatus()
        time.sleep(5)
