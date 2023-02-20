from dicttoxml import dicttoxml
from datetime import datetime


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
    return {
        "timestamp": datetime.strptime(messageDict["Date"], "%Y-%m-%d %H:%M:%S"),
        "msg_id": messageDict["Index"],
        "sender": messageDict["Phone"],
        "message": messageDict["Content"],
    }
