from huggingface_hub import hf_hub_download
from ltp_extension.algorithms import Hook
from ltp_extension.perceptron import CWSModel

WORDS = [
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


class PullWords:
    def __init__(self):
        model_file = hf_hub_download("LTP/legacy", "cws_model.bin")
        self.model = CWSModel(model_file)
        self.hook = Hook()
        for work in WORDS:
            self.hook.add_word(work, 2)

    def pull_words(self, text: str) -> list[str]:
        words = self.model(text)
        return self.hook.hook(text, words)

    def __call__(self, text: str) -> list[str]:
        return self.pull_words(text)
