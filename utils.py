from dicttoxml import dicttoxml
from datetime import datetime
import hashlib
import logging


def dictToReqXml(reqDict):
    return dicttoxml(custom_root="request", obj=reqDict, attr_type=False)


def genSmsListXml(
    pageIndex: int = 1,
    readCount: int = 10,
    boxType: int = 1,
    sortType: int = 1,
    ascending: int = 0,
    unreadPreferred: int = 0,
) -> bytes:
    return dictToReqXml(
        {
            "PageIndex": pageIndex,
            "ReadCount": readCount,
            "BoxType": boxType,
            "SortType": sortType,
            "Ascending": ascending,
            "UnreadPreferred": unreadPreferred,
        }
    )


def msgParser(messageDict):
    if messageDict["Content"] == None:
        messageDict["Content"] = "blank msg or unsupported characters"

    return {
        "sms_hash": hashlib.sha256(str(messageDict).encode()).hexdigest(),
        "timestamp": datetime.strptime(messageDict["Date"], "%Y-%m-%d %H:%M:%S"),
        "sender": messageDict["Phone"],
        "content": bytes(messageDict["Content"], "iso-8859-1").decode("utf-8"),
        "sms_index": messageDict["Index"],
    }


def msgHandler(msg, mariaDb, mqttCli, vodafone, single):
    msgData = msgParser(msg)
    newToDb = mariaDb.storeSms(msgData)
    if newToDb:
        mqttCli.publishNewSms(msgData)
    voda_logger.warning(
        f"Message received from {msgData['sender']}: {msgData['content']}"
    )
    voda_logger.warning(f"Deleting SMS with index {msgData['sms_index']}")
    del_status = vodafone.deleteSms(msgData["sms_index"])
    try:
        if del_status == "OK" or del_status == {"response": "OK"}:
            voda_logger.warning(f"Successfully deleted SMS {msgData['sms_index']}")
        else:
            voda_logger.error(
                f"Failed to delete SMS {msgData['sms_index']}: {del_status}"
            )
    except KeyError:
        voda_logger.error(f"Failed to delete SMS {msgData['sms_index']}: {del_status}")


## Using WARNING as dicttoxml spits a lot into logging.INFO
global voda_logger
voda_logger = logging
voda_logger.basicConfig(format="%(asctime)s - %(message)s", level=logging.WARNING)
