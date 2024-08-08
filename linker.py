import log, os
from comlier import issource, isWindows, isLinux


def help():
    """
    命令格式: -l [库类别] {库名} {链接源} [链接源 [...]] [选项 [...]]
        库类别可以是以下值之一：
            /help           显示此帮助信息
            /shared         指定输出目标为动态链接库
            /static         指定输出目标为静态链接库
        链接源可以是以下值之一：
            /at=            指定链接文件的源项目路径(默认为当前执行目录[.\])
            /file+=         指定链接源为指定文件，若为相对路径，则相对于当前执行目录[.\]
            /path+=         指定链接源为指定目录下的所有文件，若为相对路径，则相对于当前执行目录[.\]
        选项可以是以下值之一：
            /unix           强制使用Linux命名风格(libxxx.a, libxxx.so)
            /win            强制使用Windows命名风格(xxx.lib, xxx.dll)
            /lnkr=          指定静态链接器路径(仅当库类别为/static时有效)，默认为'ar'
            /L=             指定链接库搜索路径(仅当库类别为/shared时有效)
            /l=             指定链接库(仅当库类别为/shared时有效)
            若要为该选项指定多个值，请用逗号分隔，例如：-L=path1,path2,path3、-l=lib1,lib2
    """
    print(help.__doc__)


g_linker_dir = "ar"
g_link_file = []
g_link_path = []
g_output_type = ""
g_output_name = ""
g_root_path = os.getcwd()

g_L_dirs = []
g_l_libs = []
g_output_path = "lib"

def init():
    global g_linker_dir
    g_linker_dir = "ar"
    global g_link_file
    g_link_file = []
    global g_link_path
    g_link_path = []
    global g_output_type
    g_output_type = ""
    global g_output_name
    g_output_name = ""
    global g_root_path
    g_root_path = os.getcwd()
    global g_L_dirs
    g_L_dirs = []
    global g_l_libs
    g_l_libs = []
    global g_output_path
    g_output_path = "lib"


def set_optioins(options: list):
    if len(options) < 3:
        log.ERROR("缺少必要参数")
        return False

    global g_output_type
    if options[0] in ["/shared", "/static"]:
        if isWindows():
            if options[0] == "/shared":
                g_output_type = "dll"
            else:
                g_output_type = "lib"
        elif isLinux():
            if options[0] == "/shared":
                g_output_type = "so"
            else:
                g_output_type = "a"
        else:
            log.ERROR("不支持当前系统")
            return False
    else:
        log.ERROR(f"无效的输出目标'{options[0]}'")
        return False

    global g_output_name
    g_output_name = options[1]
    for ch in g_output_name:
        if not ch.isalnum() and ch not in ["_", "."]:
            log.ERROR(f"输出文件名'{g_output_name}'不合法")
            return False

    nametype = "windows" if isWindows() else "linux"

    for i in range(2, len(options)):
        if options[i].startswith("/file+="):
            file_path = options[i][7:]
            if g_output_type in ["dll", "lib"]:
                if not file_path.endswith(".obj"):
                    if issource(file_path):
                        file_path = ".".join(file_path.split(".")[:-1]) + ".obj"
                    else:
                        file_path += ".obj"
            elif g_output_type in ["a", "so"]:
                if not file_path.endswith(".o"):
                    if issource(file_path):
                        file_path = ".".join(file_path.split(".")[:-1]) + ".o"
                    else:
                        file_path += ".o"
            g_link_file.append(file_path)
        elif options[i].startswith("/path+="):
            g_link_path.append(options[i][7:])
        elif options[i].startswith("/at="):
            global g_root_path
            g_root_path = os.path.abspath(options[i][4:])
        elif options[i].startswith("/L="):
            g_L_dirs.extend(options[i][3:].split(","))
        elif options[i].startswith("/l="):
            g_l_libs.extend(options[i][3:].split(","))
        elif options[i].startswith("/lnkr="):
            global g_linker_dir
            g_linker_dir = options[i][6:]
        elif options[i] in ["/unix", "/win"]:
            if options[i] == "/unix":
                nametype = "linux"
            else:
                nametype = "windows"
        else:
            log.WARNING(f"被忽略的无效参数'{options[i]}'")
            return False

        if nametype == "windows":
            if g_output_type == "so":
                g_output_type = "dll"
            elif g_output_type == "a":
                g_output_type = "lib"
        elif nametype == "linux":
            if g_output_type == "dll":
                g_output_type = "so"
            elif g_output_type == "lib":
                g_output_type = "a"

    return True


def linker(options: list):
    if not options or options[0] == "/help":
        help()
        return
    if not set_optioins(options):
        return

    for i in range(len(g_link_path)):
        g_link_path[i] = os.path.relpath(g_link_path[i], g_root_path)
    for i in range(len(g_link_file)):
        g_link_file[i] = os.path.relpath(g_link_file[i], g_root_path)

    log.DEBUG(f"输出目标: {g_output_type}")
    log.DEBUG(f"输出文件名: {g_output_name}")
    log.DEBUG(f"链接源文件: {g_link_file}")
    log.DEBUG(f"链接源目录: {g_link_path}")
    log.DEBUG(f"执行目录: {g_root_path}")

    build_dir = os.path.join(g_root_path, ".build")
    os.chdir(g_root_path)
    if not os.path.exists(build_dir):
        log.ERROR(
            "没有找到 '.build' 目录，请先运行 '-c' 命令编译项目或通过 '/at=' 指定源项目路径"
        )
        return

    files_list = []
    files_list.extend(g_link_file)

    log.DEBUG(f"链接源文件: {files_list}")

    for path in g_link_path:
        for root, dirs, files in os.walk(path):
            log.DEBUG(f"搜索目录: {root}")
            log.DEBUG(f"搜索文件: {files}")
            log.DEBUG(f"包含目录: {dirs}")
            for file in files:
                log.DEBUG(f"搜索文件: {file}")
                if file.endswith(".obj") or file.endswith(".o"):
                    files_list.append(os.path.join(root, file))
                elif issource(file):
                    win_obj_path = os.path.join(
                        os.path.join(".build", root),
                        ".".join(file.split(".")[:-1]) + ".obj",
                    )
                    unix_obj_path = os.path.join(
                        os.path.join(".build", root),
                        ".".join(file.split(".")[:-1]) + ".o",
                    )
                    log.DEBUG(win_obj_path)
                    log.DEBUG(unix_obj_path)
                    if os.path.exists(win_obj_path):
                        files_list.append(win_obj_path)
                    elif os.path.exists(unix_obj_path):
                        files_list.append(unix_obj_path)
                    else:
                        log.WARNING(f"未找到源文件'{file}'的目标文件")
                else:
                    log.WARNING(f"忽略非源文件非目标文件'{file}'")

    log.DEBUG(f"链接源文件: {files_list}")
    if not files_list:
        log.ERROR("没有找到用于链接的目标文件(.obj/.o)")
        return

    # 转换为绝对路径
    for i in range(len(files_list)):
        if not os.path.isabs(files_list[i]):
            if ".build" in files_list[i]:
                files_list[i] = os.path.join(g_root_path, files_list[i])
            else:
                files_list[i] = os.path.join(build_dir, files_list[i])
        else:
            files_list[i] = os.path.abspath(files_list[i])
        files_list[i] = os.path.normpath(files_list[i])

    global g_output_path
    log.DEBUG(f"链接源文件: {files_list}")
    if os.path.isabs(g_output_path):
        g_output_path = os.path.join(g_output_path, g_output_name)
        output_path_unix = os.path.join(g_output_path, "lib" + g_output_name)
    else:
        g_output_path = os.path.join(g_root_path, os.path.join(g_output_path, g_output_name))
        output_path_unix = os.path.join(g_root_path, os.path.join(g_output_path, "lib" + g_output_name))
    
    if not os.path.exists(g_output_path):
        os.makedirs(g_output_path)

    L_args = " ".join(["-L" + d for d in g_L_dirs]) if g_L_dirs else ""
    l_args = " ".join(["-l" + l for l in g_l_libs]) if g_l_libs else ""
    log.DEBUG(f"链接库搜索路径: {L_args}")
    log.DEBUG(f"链接库: {l_args}")

    global g_linker_dir
    log.DEBUG(f"静态链接器路径: {g_linker_dir}")
    if g_output_type == "lib":
        linker_cmd = f"{g_linker_dir} rs {g_output_path}.lib {' '.join(files_list)}"
    elif g_output_type == "dll":
        linker_cmd = (
            f"g++ -shared -o {g_output_path}.dll {' '.join(files_list)} {L_args} {l_args}"
        )
    elif g_output_type == "a":
        linker_cmd = f"{g_linker_dir} rs {output_path_unix}.a {' '.join(files_list)}"
    elif g_output_type == "so":
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
        log.INFO(f"链接成功，输出文件位于: {os.path.dirname(g_output_path)}")


if __name__ == "__main__":
    pass
