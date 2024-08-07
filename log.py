import time

Debug = 0
Info = 1
Warning = 2
Error = 3
Critical = 4

level = 0
more = False


def DEBUG(*args, **kwargs):
    global level
    if level > Debug:
        return
    t = time.strftime("%Y-%m-%d %X")
    print(f"*** \033[34m[ {'DEBUG': <9}] {t} | ", *args, **kwargs, end="")
    print("\033[0m")


def INFO(*args, **kwargs):
    global level
    if level > Info:
        return
    t = time.strftime("%Y-%m-%d %X")
    print(f"*** \033[32m[ {'INFO': <9}] {t} | ", *args, **kwargs, end="")
    print("\033[0m")


def INFO_MORE(*args, **kwargs):
    global level, more
    if level > Info or not more:
        return
    t = time.strftime("%Y-%m-%d %X")
    print(f"*** \033[32m[ {'INFO': <9}] {t} | ", *args, **kwargs, end="")
    print("\033[0m")


def WARNING(*args, **kwargs):
    global level
    if level > Warning:
        return
    t = time.strftime("%Y-%m-%d %X")
    print(f"*** \033[33m[ {'WARNING': <9}] {t} | ", *args, **kwargs, end="")
    print("\033[0m")


def ERROR(*args, **kwargs):
    global level
    if level > Error:
        return
    t = time.strftime("%Y-%m-%d %X")
    print(f"*** \033[31m[ {'ERROR': <9}] {t} | ", *args, **kwargs, end="")
    print("\033[0m")


def CRITICAL(*args, **kwargs):
    global level
    if level > Critical:
        return
    t = time.strftime("%Y-%m-%d %X")
    print(f"*** \033[35m[ {'CRITICAL': <9}] {t} | ", *args, **kwargs, end="")
    print("\033[0m")


if __name__ == "__main__":
    DEBUG("This is a debug message")
    INFO("This is an info message")
    WARNING("This is a warning message")
    ERROR("This is an error message")
    CRITICAL("This is a critical message")
