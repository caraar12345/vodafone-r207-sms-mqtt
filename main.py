import time

if __name__ == "__main__":
    import constants
    import vodafone_connect

    vodafone = vodafone_connect.VodafoneDevice(
        constants.DEFAULT_ROUTER_IP, constants.DEFAULT_ADMIN_PWD
    )

    print(vodafone.getSmsList())
    while True:
        vodafone.refreshDeviceStatus()
        print(
            vodafone.network,
            vodafone.imei,
            vodafone.battery_level,
            vodafone.signal_strength,
            vodafone.signal_icon,
            vodafone.max_signal,
        )
        time.sleep(5)
