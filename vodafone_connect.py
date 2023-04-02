import constants
import requests
import xmltodict
from datetime import datetime, timedelta
from base64 import b64encode
from utils import *
import mqtt


class VodafoneDevice:
    def __init__(
        self, router_ip, admin_password, ssl, ssl_root, wifi_settings_to_mqtt
    ) -> None:
        self.router_ip = router_ip
        self.admin_password = b64encode(bytes(admin_password, "utf-8")).decode()
        self.verification_token_expiry = datetime(9999, 12, 31)
        self.ssl = ssl
        self.ssl_root = ssl_root
        self.wifi_settings_to_mqtt = wifi_settings_to_mqtt
        self.refreshDeviceStatus()

    def getVerificationToken(self, *expired):
        if (
            self.verification_token_expiry == datetime(9999, 12, 31)
            or self.verification_token_expiry <= datetime.now() - timedelta(minutes=10)
            or expired
        ):
            self.verification_token_expiry = datetime.now() + timedelta(minutes=5)
            self.verification_token = self.makeGetRequest(
                constants.API_VERIFICATION_TOKEN, True
            )["response"]["token"]
        return self.verification_token

    def makePostRequest(self, api_endpoint, data):
        if type(data) == dict:
            data = dictToReqXml(data)

        protocol = "https" if self.ssl else "http"

        response_text = "125001"

        while "125001" in response_text:
            response_text = requests.post(
                protocol + "://" + self.router_ip + "/" + api_endpoint,
                data=data,
                headers={
                    "__RequestVerificationToken": self.getVerificationToken(True),
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                },
                verify=self.ssl_root,
            ).text

        return response_text

    def makeGetRequest(self, api_endpoint, *calledFromGetVerifToken):
        if calledFromGetVerifToken:
            headers = {}
        else:
            headers = {"__RequestVerificationToken": self.getVerificationToken()}

        protocol = "https" if self.ssl else "http"

        return xmltodict.parse(
            requests.get(
                protocol + "://" + self.router_ip + "/" + api_endpoint,
                headers=headers,
                verify=self.ssl_root,
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
        self.ssid = self.getWifiBasicSettings()["WifiSsid"]
        self.wpa_psk = self.getWifiSecuritySettings()["WifiWpapsk"]
        self.wifi_enabled = (
            True if int(self.getWifiBasicSettings()["WifiEnable"]) == 1 else False
        )
        self.ssid_broadcast = (
            False if int(self.getWifiBasicSettings()["WifiHide"]) == 1 else True
        )

        self.printed_description = f"""
Name:    {self.name}
Network: {self.network}
IMEI:    {self.imei}
Serial:  {self.serial_number}
Battery: {self.battery_level}%
Signal:  {self.signal_strength}%
Wi-Fi:   {"Enabled" if self.wifi_enabled else "Disabled"}
SSID:    {self.ssid}
WPA PSK: {self.wpa_psk}
SSID Bc: {self.ssid_broadcast}
"""
        self.mqtt_description = {
            "name": self.name,
            "network": self.network,
            "imei": self.imei,
            "serial": self.serial_number,
            "battery": self.battery_level,
            "signal": self.signal_strength,
            "wifi": self.wifi_enabled,
        }

        if self.wifi_settings_to_mqtt:
            self.mqtt_description |= {
                "ssid": self.ssid,
                "wpa_psk": self.wpa_psk,
                "ssid_broadcast": self.ssid_broadcast,
            }

    def getNetwork(self):
        return self.makeGetRequest(constants.API_CURRENT_MOBILE_NET)["response"][
            "FullName"
        ]

    def getInformation(self):
        return self.makeGetRequest(constants.API_DEVICE_INFORMATION)["response"]

    def getDeviceStatus(self):
        return self.makeGetRequest(constants.API_MONITORING_STATUS)["response"]

    def getWifiBasicSettings(self):
        return self.makeGetRequest(constants.API_WLAN_BASIC_SETTINGS)["response"]

    def getWifiSecuritySettings(self):
        return self.makeGetRequest(constants.API_WLAN_SECURITY_SETTINGS)["response"]

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
        sms_list = self.makePostRequest(
            constants.API_SMS_LIST,
            genSmsListXml(),
        )
        if xmltodict.parse(sms_list)["response"]["Count"] == "0":
            return
        else:
            return xmltodict.parse(sms_list)["response"]["Messages"]

    def deleteSms(self, smsIndex):
        self.loginRequired()

        return xmltodict.parse(
            self.makePostRequest(
                constants.API_DELETE_SMS, dictToReqXml({"Index": smsIndex})
            )
        )
