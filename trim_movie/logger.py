from termcolor import cprint

def log(message: str) -> None:
    cprint(message, 'red')