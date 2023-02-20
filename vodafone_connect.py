import constants
import requests
import xmltodict
from datetime import datetime, timedelta
from base64 import b64encode
from utils import *


class VodafoneDevice:
    def __init__(self, router_ip, admin_password) -> None:
        self.router_ip = router_ip
        self.admin_password = b64encode(bytes(admin_password, "utf-8")).decode()
        self.verification_token_expiry = datetime(9999, 12, 31)
        self.refreshDeviceStatus()

    def getVerificationToken(self):
        if (
            self.verification_token_expiry == datetime(9999, 12, 31)
            or self.verification_token_expiry <= datetime.now()
        ):
            self.verification_token_expiry = datetime.now() + timedelta(minutes=5)
            self.verification_token = self.makeGetRequest(
                constants.API_VERIFICATION_TOKEN, True
            )["response"]["token"]
        return self.verification_token

    def makePostRequest(self, api_endpoint, data):
        if type(data) == dict:
            data = dictToReqXml(data)

        return requests.post(
            "http://" + self.router_ip + "/" + api_endpoint,
            data=data,
            headers={
                "__RequestVerificationToken": self.getVerificationToken(),
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
        ).text

    def makeGetRequest(self, api_endpoint, *calledFromGetVerifToken):
        if calledFromGetVerifToken:
            headers = {}
        else:
            headers = {"__RequestVerificationToken": self.getVerificationToken()}
        return xmltodict.parse(
            requests.get(
                "http://" + self.router_ip + "/" + api_endpoint,
                headers=headers,
            ).text
        )

    def refreshDeviceStatus(self):
        self.network = self.getNetwork()
        self.imei = self.getInformation()["Imei"]
        self.serial_number = self.getInformation()["SerialNumber"]
        self.name = self.getInformation()["DeviceName"]
        self.battery_level = self.getDeviceStatus()["BatteryPercent"]
        self.signal_strength = int(
            int(self.getDeviceStatus()["SignalIcon"])
            / int(self.getDeviceStatus()["maxsignal"])
            * 100
        )
        self.signal_icon = self.getDeviceStatus()["SignalIcon"]
        self.max_signal = self.getDeviceStatus()["maxsignal"]
        self.description = f"""
Name:    {self.name}
Network: {self.network}
IMEI:    {self.imei}
Serial:  {self.serial_number}
Battery: {self.battery_level}%
Signal:  {self.signal_strength}%"""

    def getNetwork(self):
        return self.makeGetRequest(constants.API_CURRENT_MOBILE_NET)["response"][
            "FullName"
        ]

    def getInformation(self):
        return self.makeGetRequest(constants.API_DEVICE_INFORMATION)["response"]

    def getDeviceStatus(self):
        return self.makeGetRequest(constants.API_MONITORING_STATUS)["response"]

    def getLoginStatus(self):
        status = self.makeGetRequest(constants.API_LOGIN_STATUS)
        return (
            True if status["response"]["State"] == "0" else False,
            status["response"]["Username"],
        )

    def login(self):
        return self.makePostRequest(
            constants.API_LOGIN,
            {"Username": "admin", "Password": self.admin_password},
        )

    def loginRequired(self):
        while not self.getLoginStatus()[0]:
            self.login()

        return True

    def getSmsList(self):
        return xmltodict.parse(
            self.makePostRequest(
                constants.API_SMS_LIST,
                genSmsListXml(),
            )
        )["response"]["Messages"]["Message"]

    def deleteSms(self, smsIndex):
        self.loginRequired()

        return self.makePostRequest(
            constants.API_DELETE_SMS, dictToReqXml({"Index": smsIndex})
        )
