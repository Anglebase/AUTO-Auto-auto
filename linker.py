import log, os
from comlier import issource


def help():
    """
    命令格式: -l [库类别] {库名} {链接源} [链接源 [...]] [选项 [...]]
        库类别可以是以下值之一：
            /help      显示此帮助信息
            /dll       指定输出目标为 Windows 动态链接库(<库名>.dll)
            /lib       指定输出目标为 Windows 静态链接库(<库名>.lib)
            /a         指定输出目标为 Linux 静态链接库(lib<库名>.a)
            /so        指定输出目标为 Linux 动态链接库(lib<库名>.so)
        链接源可以是以下值之一：
            /at=<项目路径>          指定链接文件的源项目路径(默认为当前执行目录)
            /file+=<文件路径>       指定链接源为指定文件
            /path+=<目录路径>       指定链接源为指定目录下的所有文件
        选项可以是以下值之一：
            若要为该选项指定多个值，请用逗号分隔，例如：-L=path1,path2,path3、-l=lib1,lib2
            /L=         指定链接库搜索路径(仅当库类别为/dll或/so时有效)
            /l=         指定链接库(仅当库类别为/dll或/so时有效)
    """
    print(help.__doc__)


link_file = []
link_path = []
output_type = ""
output_name = ""
root_path = os.getcwd()

L_dirs = []
l_libs = []


def set_optioins(options: list):
    if len(options) < 3:
        log.ERROR("缺少必要参数")
        return

    global output_type
    if options[0] in ["/dll", "/lib", "/a", "/so"]:
        output_type = options[0][1:]
    else:
        log.ERROR(f"无效的输出目标'{options[0]}'")
        return

    global output_name
    output_name = options[1]
    for ch in output_name:
        if not ch.isalnum() and ch not in ["_", "."]:
            log.ERROR(f"输出文件名'{output_name}'不合法")
            return

    for i in range(2, len(options)):
        if options[i].startswith("/file+="):
            file_path = options[i][7:]
            if output_type in ["dll", "lib"]:
                if not file_path.endswith(".obj"):
                    if issource(file_path):
                        file_path = ".".join(file_path.split(".")[:-1]) + ".obj"
                    else:
                        file_path += ".obj"
            elif output_type in ["a", "so"]:
                if not file_path.endswith(".o"):
                    if issource(file_path):
                        file_path = ".".join(file_path.split(".")[:-1]) + ".o"
                    else:
                        file_path += ".o"
            link_file.append(file_path)
        elif options[i].startswith("/path+="):
            link_path.append(options[i][7:])
        elif options[i].startswith("/at="):
            global root_path
            root_path = os.path.abspath(options[i][4:])
        elif options[i].startswith("/L="):
            L_dirs.extend(options[i][3:].split(","))
        elif options[i].startswith("/l="):
            l_libs.extend(options[i][3:].split(","))
        else:
            log.WARNING(f"被忽略的无效参数'{options[i]}'")
            return


def linker(options: list):
    if not options or options[0] == "/help":
        help()
        return
    set_optioins(options)

    log.DEBUG(f"输出目标: {output_type}")
    log.DEBUG(f"输出文件名: {output_name}")
    log.DEBUG(f"链接源文件: {link_file}")
    log.DEBUG(f"链接源目录: {link_path}")
    log.DEBUG(f"执行目录: {root_path}")

    build_dir = os.path.join(root_path, ".build")
    os.chdir(root_path)
    if not os.path.exists(build_dir):
        log.ERROR("没有找到 '.build' 目录，请先运行 '-c' 命令编译项目")

    files_list = []
    files_list.extend(link_file)

    log.DEBUG(f"链接源文件: {files_list}")

    for path in link_path:
        for root, dirs, files in os.walk(path):
            log.DEBUG(f"搜索目录: {root}")
            log.DEBUG(f"搜索文件: {files}")
            log.DEBUG(f"包含目录: {dirs}")
            for file in files:
                log.DEBUG(f"搜索文件: {file}")
                if output_type in ["dll", "lib"]:
                    if file.endswith(".obj"):
                        files_list.append(os.path.join(root, file))
                    elif issource(file):
                        files_list.append(
                            os.path.join(root, ".".join(file.split(".")[:-1]) + ".obj")
                        )
                    else:
                        log.WARNING(f"忽略非源文件非目标文件'{file}'")
                elif output_type in ["a", "so"]:
                    if file.endswith(".o"):
                        files_list.append(os.path.join(root, file))
                    elif issource(file):
                        files_list.append(
                            os.path.join(root, ".".join(file.split(".")[:-1]) + ".o")
                        )
                    else:
                        log.WARNING(f"忽略非源文件非目标文件'{file}'")

    log.DEBUG(f"链接源文件: {files_list}")
    if not files_list:
        log.ERROR("没有找到用于链接的目标文件")
        return

    # 转换为绝对路径
    for i in range(len(files_list)):
        if not os.path.isabs(files_list[i]):
            if ".build" in files_list[i]:
                files_list[i] = os.path.join(root_path, files_list[i])
            else:
                files_list[i] = os.path.join(build_dir, files_list[i])
        else:
            files_list[i] = os.path.abspath(files_list[i])
        files_list[i] = os.path.normpath(files_list[i])

    log.DEBUG(f"链接源文件: {files_list}")
    output_path = os.path.join(build_dir, os.path.join(".out", output_name))
    output_path_unix = os.path.join(
        build_dir, os.path.join(".out", "lib" + output_name)
    )

    L_args = " ".join(["-L" + d for d in L_dirs]) if L_dirs else ""
    l_args = " ".join(["-l" + l for l in l_libs]) if l_libs else ""
    log.DEBUG(f"链接库搜索路径: {L_args}")
    log.DEBUG(f"链接库: {l_args}")

    if output_type == "lib":
        linker_cmd = f"ar rcs {output_path}.lib {' '.join(files_list)}"
    elif output_type == "dll":
        linker_cmd = (
            f"g++ -shared -o {output_path}.dll {' '.join(files_list)} {L_args} {l_args}"
        )
    elif output_type == "a":
        linker_cmd = f"ar rcs {output_path_unix}.a {' '.join(files_list)}"
    elif output_type == "so":
        linker_cmd = f"g++ -shared -o {output_path_unix}.so {' '.join(files_list)} {L_args} {l_args}"

    log.DEBUG(f"链接命令: {linker_cmd}")

    ret = os.system(f"{linker_cmd} 1>> {os.path.join(build_dir, '.linker.log')} 2>&1")
    if ret != 0:
        log.ERROR(f"链接失败，错误码: {ret}")
        with open(os.path.join(build_dir, ".linker.log"), "r") as f:
            for line in f:
                for word in line.split():
                    if word in ["undefined", "reference"]:
                        print(f"\033[31m{word}\033[0m", end=" ")
                    elif word in ["multiple", "definition"]:
                        print("\033[33m" + word + "\033[0m", end=" ")
                    else:
                        print(word, end=" ")
                print()
    else:
        log.INFO(f"链接成功")


if __name__ == "__main__":
    pass
