import time
from utils import *
import db
import mqtt

if __name__ == "__main__":
    import constants
    import vodafone_connect

    vodafone = vodafone_connect.VodafoneDevice(
        constants.DEFAULT_ROUTER_IP, constants.DEFAULT_ADMIN_PWD
    )

    mqttCli = mqtt.MqttClient("vodafone-r207-sms-mqtt", vodafone_device=vodafone)

    mariaDb = db.DatabaseInstance()
    mariaDb.dbConnect()
    mariaDb.dbTablePrep()

    while True:
        sms_list = vodafone.getSmsList()
        print("+1", sms_list)
        if sms_list == None:
            pass
        elif len(sms_list) == 1:
            for msg in sms_list:
                print("+4", sms_list["Message"])
                msgData = msgParser(sms_list["Message"])
                mariaDb.storeSms(msgData)
                mqttCli.publishNewSms(msgData)
                vodafone.deleteSms(msgData["sms_index"])

        elif sms_list != None:
            for msg in sms_list:
                print("+3", msg)
                msgData = msgParser(msg)
                mariaDb.storeSms(msgData)
                mqttCli.publishNewSms(msgData)
                vodafone.deleteSms(msgData["sms_index"])

        vodafone.refreshDeviceStatus()
        print(vodafone.description)
        time.sleep(5)
