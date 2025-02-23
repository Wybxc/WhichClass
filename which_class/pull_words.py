from ltp import LTP


def create_ltp():
    ltp = LTP("LTP/legacy")
    words = [
        "本研",
        "研本",
        "一教",
        "二教",
        "三教",
        "四教",
        "理教",
        "文史",
        "地学",
        "理一",
        "理二",
        "医学部",
        "逸夫楼",
        "马池口",
        "邱德拔",
        "单周",
        "双周",
        "每周",
        "周一",
        "周二",
        "周三",
        "周四",
        "周五",
        "周六",
        "周日",
    ]
    ltp.add_words(words)
    return ltp
