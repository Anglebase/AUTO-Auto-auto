import time


def DEBUG(*args, **kwargs):
    # t = time.strftime("%Y-%m-%d %X")
    # print(f"*** \033[34m[{'DEBUG': <10}] {t} | ", *args, **kwargs, end="")
    # print("\033[0m")
    pass


def INFO(*args, **kwargs):
    t = time.strftime("%Y-%m-%d %X")
    print(f"*** \033[32m[{'INFO': <10}] {t} | ", *args, **kwargs, end="")
    print("\033[0m")


def WARNING(*args, **kwargs):
    t = time.strftime("%Y-%m-%d %X")
    print(f"*** \033[33m[{'WARNING': <10}] {t} | ", *args, **kwargs, end="")
    print("\033[0m")


def ERROR(*args, **kwargs):
    t = time.strftime("%Y-%m-%d %X")
    print(f"*** \033[31m[{'ERROR': <10}] {t} | ", *args, **kwargs, end="")
    print("\033[0m")


def CRITICAL(*args, **kwargs):
    t = time.strftime("%Y-%m-%d %X")
    print(f"*** \033[35m[{'CRITICAL': <10}] {t} | ", *args, **kwargs, end="")
    print("\033[0m")


if __name__ == "__main__":
    DEBUG("This is a debug message")
    INFO("This is an info message")
    WARNING("This is a warning message")
    ERROR("This is an error message")
    CRITICAL("This is a critical message")
