from sys import argv
from comlier import complier
from linker import linker
import log, traceback


VERSION = "0.1"


def help():
    """
    命令选项：
        -v 显示版本信息
        -h 显示此帮助信息
        -c {ProjectPath} [...]      自动编译项目，运行 cpm -c /help 查看更多内容
        -l {libName} [...]          编译库文件，运行 cpm -l /help 查看更多内容
    """
    log.INFO("cpm 帮助文档:")
    print(help.__doc__)


def main():
    if len(argv) <= 1:
        help()

    commends = []
    sign = False
    # 解析命令行参数
    for word in argv:
        if not sign:
            sign = True
            continue

        if word[0] == "-":
            commends.append([word])
        elif commends:
            commends[-1].append(word)
        else:
            log.ERROR("无效的命令选项: " + word)
            return

    # 执行命令
    for option in commends:
        if option[0] == "-c":
            complier(option[1:])
        elif option[0] == "-v":
            log.INFO(f"MinGW Compiler&Package Manager 版本: -v{VERSION}")
        elif option[0] == "-h":
            help()
        elif option[0] == "-l":
            linker(option[1:])
        else:
            log.ERROR("无效的命令选项: " + option[0])
            return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.WARNING("cmp 已被终止")
    except Exception as e:
        log.CRITICAL(f"发生错误: {e}")
        log.CRITICAL(f"错误信息:")
        traceback.print_exc()
        log.CRITICAL("请将错误信息反馈给作者")
    finally:
        log.INFO("cmp 已退出")
