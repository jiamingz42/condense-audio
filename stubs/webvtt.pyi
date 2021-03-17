from typing import List


class WebVTT(object):
    @property
    def captions(self) -> List[Caption]:
        pass

    def save(self, path: str) -> None:
        pass


class Caption(object):
    def __init__(self, start: str, end: str, text: str):
        pass

    @property
    def start(self) -> str:
        pass

    @property
    def end(self) -> str:
        pass

    @property
    def text(self) -> str:
        pass


def read(file: str) -> List[Caption]:
    pass
