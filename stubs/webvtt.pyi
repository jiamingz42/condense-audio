from typing import List

class WebVTT(object):
    @property
    def captions(self) -> List[Caption]:
        pass

    def save(self, path: str) -> None:
        pass

class Caption(object):
    @property
    def start(self) -> str:
        pass

    @property
    def end(self) -> str:
        pass

    @property
    def text(self) -> str:
        pass

def read(file : str) -> List[Caption]:
    pass
