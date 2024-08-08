import os, hashlib, pickle, copy, log
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Lock

has_build = False

# 忽略的文件夹
ignore_floders = ["build", "dist", "venv", "docs", "out", "bin"]
# 同时忽略所有以.或_开头的文件和文件夹

gnu = "g++"
std = "c++17"
include_dirs = []
lib_dirs = []
link = []
c_options = []
defines = []
rebuild = False
run = False

file_count = 0
source_file_count = 0

build_path = ""
max_thread_every_cpu = 5

include_parent_depth = 2

diff_file_count = 0
hadcompare_file_count = 0
hased_file_count = 0
output_path = "out"


def init():
    global has_build
    has_build = False
    # 忽略的文件夹
    global ignore_floders
    ignore_floders = ["build", "dist", "venv", "docs", "out", "bin"]
    # 同时忽略所有以.或_开头的文件和文件夹
    global gnu
    gnu = "g++"
    global std
    std = "c++17"
    global include_dirs
    include_dirs = []
    global lib_dirs
    lib_dirs = []
    global link
    link = []
    global c_options
    c_options = []
    global defines
    defines = []
    global rebuild
    rebuild = False
    global run
    run = False
    global file_count
    file_count = 0
    global source_file_count
    source_file_count = 0
    global build_path
    build_path = ""
    global include_parent_depth
    include_parent_depth = 2
    global diff_file_count
    diff_file_count = 0
    global hadcompare_file_count
    hadcompare_file_count = 0

    global hased_file_count
    hased_file_count = 0
    global output_path
    output_path = "out"
    global max_thread_every_cpu
    max_thread_every_cpu = 5


def isLinux():
    return os.name == "posix"


def isWindows():
    return os.name == "nt"


if isWindows():
    sys_type = "windows"
elif isLinux():
    sys_type = "linux"
else:
    raise Exception("不支持的系统类型")


def isheader(name: str):
    return (
        name.endswith(".h")
        or name.endswith(".hpp")
        or name.endswith(".hxx")
        or name.endswith(".hh")
    )


def issource(name: str):
    return (
        name.endswith(".c")
        or name.endswith(".cpp")
        or name.endswith(".cxx")
        or name.endswith(".cc")
        or name.endswith(".C")
        or name.endswith(".c++")
    )


def islibirary(name: str):
    return name.endswith(".lib") or name.endswith(".a") or name.endswith(".so")


def set_options(option: list):
    """
    命令格式：-c {项目路径} [选项1 [选项2 [...]]]
    选项可以是以下之一：
        /help               显示此帮助信息
        /run                在编译完成后运行编译结果
        /rebuild            强制重新编译
        /win                强制采用Windows命名风格编译(.obj)
        /unix               强制采用Linux命名风格编译(.o)
        /all                显示更加详细的输出信息
        /th=                指定单核最大并发编译线程数，默认为5
        /out=               指定结果输出目录，默认为out
        /ign=               指定忽略的文件夹名，默认为build,dist,venv,docs,out,bin
        /ign+=              额外指定忽略的文件夹名
        /cpr=               指定编译器，默认为g++
        /std=               指定编译标准，默认为c++17
        /I:                 指定头文件父目录深度，默认为2，即头文件所在目录和该目录的父目录
        /I=                 指定额外的头文件搜索路径(项目目录外)
        /L=                 指定额外的库文件搜索路径(项目目录外)
        /l=                 指定额外的链接库链接参数(项目目录外)
        /D=                 指定预定义宏
        /opt=               指定其它编译选项
        /res=               指定资源文件路径
        对于可赋值的参数，多个值之间用逗号分隔，如：/I=path1,path2,path3、/opt=-O2,-Wall
    """
    for item in option:
        if item.startswith("/cpr="):
            global gnu
            gnu = item[5:]
            if not gnu:
                gnu = "g++"
        elif item.startswith("/std="):
            global std
            std = item[5:]
            if not std:
                std = "c++17"
            if (
                gnu == "g++"
                or os.path.basename(gnu).startswith("g++")
                or gnu == "clang++"
                or os.path.basename(gnu).startswith("clang++")
            ):
                if std not in ["c++11", "c++14", "c++17", "c++20"]:
                    log.WARNING("无效的语言标准：", std)
                    log.WARNING("已使用默认语言标准：", "c++17")
                    std = "c++17"
            elif (
                gnu == "gcc"
                or os.path.basename(gnu).startswith("gcc")
                or gnu == "clang"
                or os.path.basename(gnu).startswith("clang")
            ):
                if std not in ["c99", "c11"]:
                    log.WARNING("无效的语言标准：", std)
                    log.WARNING("已使用默认语言标准：", "c11")
                    std = "c11"
        elif item.startswith("/I="):
            global include_dirs
            include_dirs.extend(item[3:].split(","))
        elif item.startswith("/L="):
            global lib_dirs
            lib_dirs.extend(item[3:].split(","))
        elif item.startswith("/l="):
            global link
            link.extend(item[3:].split(","))
        elif item.startswith("/opt="):
            global c_options
            c_options.extend(item[5:].split(","))
        elif item.startswith("/D="):
            global defines
            defines.extend(item[3:].split(","))
        elif item.startswith("/ign="):
            global ignore_floders
            ignore_floders = item[5:].split(",")
            for item in ignore_floders:
                for ch in item:
                    if ch in '/\\<>*:?"':
                        log.ERROR(f"'{item}'不是文件夹名")
                        return False
        elif item.startswith("/ign+="):
            ignore_floders.extend(item[6:].split(","))
            for item in ignore_floders:
                for ch in item:
                    if ch in '/\\<>*:?"':
                        log.ERROR(f"'{item}'不是文件夹名")
                        return False
        elif item == "/help":
            log.INFO("cpm -c 命令文档:")
            print(set_options.__doc__)
            return False
        elif item == "/rebuild":
            global rebuild
            rebuild = True
        elif item == "/run":
            global run
            run = True
        elif item == "/win":
            global sys_type
            sys_type = "windows"
        elif item == "/unix":
            sys_type = "linux"
        elif item == "/all":
            log.more = True
        elif item.startswith("/I:"):
            global include_parent_depth
            if item[3:].isdigit():
                include_parent_depth = int(item[3:])
            else:
                log.ERROR("选项参数必须为数字：", item)
                return False
        elif item.startswith("/out="):
            global output_path
            output_path = item[5:]
        elif item.startswith("/th="):
            global max_thread_every_cpu
            if item[4:].isdigit():
                max_thread_every_cpu = int(item[4:])
            else:
                log.ERROR("选项参数必须为数字：", item)
                return False
        else:
            log.WARNING("被忽略的未知选项：", item)

    log.DEBUG("设置选项：", " ".join(option))
    return True


# 以递归的方式读取目录并存储为字典格式
def get_floders_dict(path: str):
    files_dict = {}

    def get_files(path: str, files_dict: dict):
        global file_count
        # print(path, files_dict)
        for root, dirs, files in os.walk(path):
            # print(root, dirs, files)
            if dirs:  # 递归读取子目录
                for dir in dirs:
                    if dir not in files_dict:
                        files_dict[dir] = {}
                    log.DEBUG("读取到文件夹：", os.path.join(root, dir))
                    if (
                        dir not in ignore_floders
                        and not dir.startswith(".")
                        and not dir.startswith("_")
                    ):
                        get_files(os.path.join(root, dir), files_dict[dir])
                    else:
                        log.INFO("已忽略文件夹:\t", os.path.join(root, dir))
            for file in files:
                log.DEBUG("读取到文件：", os.path.join(root, file))
                if file.startswith(".") or file.startswith("_"):
                    log.INFO("已忽略文件:\t", os.path.join(root, file))
                    continue
                files_dict[file] = "new"
                file_count += 1
                global source_file_count
                if issource(file) or isheader(file):
                    source_file_count += 1
            break

    get_files(path, files_dict)
    log.INFO("搜索到文件数：", file_count)
    log.DEBUG("检索到源/头文件数：", source_file_count)
    return files_dict


def hash_file(hash_func: callable, project_dict: dict, file_path: str):
    global hased_file_count
    for name in project_dict:
        if type(project_dict[name]) == str:
            with open(os.path.join(file_path, name), "rb") as f:
                project_dict[name] = hash_func(f.read()).hexdigest()
            scount = int(hased_file_count / file_count * 50)
            whitespaces = len(str(file_count)) - len(str(hased_file_count))
            print(
                f"\r正在计算哈希: [{'#'*scount:.<50}] {whitespaces*' '}{hased_file_count}/{file_count}",
                end="",
            )
            hased_file_count += 1
            # 若是链接库自动追加搜索路径和链接参数
            if islibirary(name):
                global link, lib_dirs
                lib_dirs.append(file_path)
                if name.endswith(".a"):
                    link.append(name[3:-2])
                elif name.endswith(".so"):
                    link.append(name[3:-3])
                elif name.endswith(".lib"):
                    link.append(name[:-4])
        else:
            hash_file(hash_func, project_dict[name], os.path.join(file_path, name))


def diff_files(project_dict: dict, old_project_dict: dict):
    global diff_file_count
    for name in project_dict:
        if type(project_dict[name]) == str:
            log.DEBUG("比较先后文件差异：", name)
            global hadcompare_file_count
            hadcompare_file_count += 1
            if not rebuild and os.path.exists(build_path):
                print(
                    f"\r正在比较差异: [{'#'*int(diff_file_count/file_count*50):.<50}] {diff_file_count}/{file_count}",
                    end="",
                )
            if project_dict[name] == old_project_dict.get(name, ""):
                project_dict[name] = ""
            else:
                diff_file_count += 1
                project_dict[name] = "changed"
        else:
            diff_files(project_dict[name], old_project_dict.get(name, {}))


def tree_headers(relpath: str, project_dict: dict):
    header_dict = {}

    def get_headers(path: str, header_dict_ls: dict):
        for name in header_dict_ls:
            if type(header_dict_ls[name]) == str:
                if isheader(name) and os.path.join(path, name) not in header_dict:
                    header_dict[os.path.join(path, name)] = []
            else:
                get_headers(os.path.join(path, name), header_dict_ls[name])

    # 递归遍历目录，获取头文件
    get_headers(".", project_dict)
    log.DEBUG(*header_dict.items(), sep="\n")

    log.INFO("检索到头文件数：", len(header_dict))

    def append_headers(path: str):
        with open(os.path.join(relpath, path), "r", encoding="utf-8") as f:
            for line in f:
                if "#include" in line:
                    for item in header_dict:
                        filename = os.path.basename(item)
                        if filename.lower() in line.lower():
                            header_dict[item].append(path)

    def get_sources(path: str, project_dict: dict):
        for name in project_dict:
            if type(project_dict[name]) == str:
                if issource(name) or isheader(name):
                    append_headers(os.path.join(path, name))
            else:
                get_sources(os.path.join(path, name), project_dict[name])

    # 递归遍历目录，构建头文件依赖表
    get_sources(".", project_dict)
    log.DEBUG(*header_dict.items(), sep="\n")

    for item in header_dict:
        if len(header_dict[item]) >= 1:
            log.DEBUG(f"头文件 {item} 包含 {len(header_dict[item])} 个直接引用")
        else:
            log.DEBUG(f"头文件 {item} 未被引用")

    # 展开头文件依赖
    state = True
    while state:
        state = False
        for header in header_dict:
            del_ls = []
            for reffile in header_dict[header]:
                if reffile == header:
                    log.ERROR(f"头文件 {header} 包含自身引用！")
                    return None
                if reffile in header_dict:
                    del_ls.append(reffile)
                    state = True
            for reffile in del_ls:
                header_dict[header].remove(reffile)
                header_dict[header].extend(header_dict[reffile])
            header_dict[header] = list(set(header_dict[header]))

    log.DEBUG(*header_dict.items(), sep="\n")

    nouse_headers = []
    for item in header_dict:
        header_path = os.path.normpath(os.path.join(relpath, item))
        if len(header_dict[item]) >= 1:
            maxlen = max([len(str(len(header_dict[item]))) for item in header_dict])
            lenth = len(header_dict[item])
            whitespaces = maxlen - len(str(lenth))
            log.INFO_MORE(
                f"具有 {whitespaces*' '}{lenth} 个有效引用的头文件： {header_path}"
            )
        else:
            log.WARNING(f"未被引用的头文件 {header_path} 将被忽略")
            nouse_headers.append(item)
    for item in nouse_headers:
        del header_dict[item]

    # 去重
    # log.DEBUG("正在去重...")
    # for name in header_dict:
    #     header_dict[name] = list(set(header_dict[name]))

    return header_dict


def get_main_source_files(relpath: str, project_dict: dict):
    res = []
    name_list = {}
    rename_list = {}
    count_id = 0

    # 检查是否存在main函数
    def append_main_source(path: str):
        trupath = os.path.normpath(os.path.join(relpath, path))
        with open(trupath, "r", encoding="utf-8") as f:
            line_num = 0
            if isWindows():
                ext_name = ".exe"
            elif isLinux():
                ext_name = ""
            else:
                raise Exception("不支持的系统类型")
            for line in f:
                line_num += 1
                if (
                    line.startswith("int main(")
                    or line.startswith("// main")
                    or line.startswith("void main(")
                ):
                    its_name = ".".join(os.path.basename(path).split(".")[:-1])
                    if its_name in name_list:
                        nonlocal count_id
                        log.WARNING(f"文件 {trupath} 与 {name_list[its_name]} 重名")
                        rename = (
                            ".".join(path.split(".")[:-1])
                            + f"_{count_id}.{path.split('.')[-1]}"
                        )
                        out_name = (
                            ".".join(os.path.basename(rename).split(".")[:-1])
                            + ext_name
                        )
                        log.WARNING(f"文件 {trupath} 将生成为 {out_name}")
                        res.append(rename)
                        rename_list[rename] = path
                        count_id += 1
                    else:
                        res.append(path)
                    name_list[its_name] = trupath
                    log.INFO_MORE(f"检索到具有主函数文件: {trupath}:{line_num}:0")
                    break

    def get_sources(path: str, project_dict: dict):
        for name in project_dict:
            if type(project_dict[name]) == str:
                if issource(name) and os.path.join(path, name) not in res:
                    append_main_source(os.path.join(path, name))
            else:
                get_sources(os.path.join(path, name), project_dict[name])

    get_sources(".", project_dict)
    return res, rename_list


def generate_task(
    path: str, dict_files: dict, header_dict: dict, main_source: list, rename_list: dict
):
    # 生成编译任务
    changed_list = []

    def get_changed_files(path: str, dict_files: dict):
        for name in dict_files:
            if type(dict_files[name]) == str:
                if dict_files[name] != "":
                    changed_list.append(os.path.join(path, name))
            else:
                get_changed_files(os.path.join(path, name), dict_files[name])

    get_changed_files(".", dict_files)
    log.DEBUG("发生变化的文件：", changed_list)
    # 构造编译任务
    task_list = []
    for file in changed_list:
        if isheader(os.path.basename(file)) or issource(os.path.basename(file)):
            task_list.append(file)

    header_list = []
    for file in task_list:
        if isheader(os.path.basename(file)):
            header_list.append(file)
    log.DEBUG("发生变化的头文件：", *header_list, sep="\n")
    for item in header_list:
        task_list.remove(item)
        if item in header_dict:
            task_list.extend(header_dict[item])
    # 编译任务
    complier_task = list(set(task_list))
    log.DEBUG("编译任务：", *complier_task, sep="\n")

    # 生成链接任务
    link_task = {
        source: [source if source not in rename_list else rename_list[source]]
        for source in main_source
    }
    for source in main_source:
        for header in header_dict:
            if (
                source
                if source not in rename_list
                else rename_list[source] in header_dict[header]
            ):
                link_task[source].extend(header_dict[header])
        link_task[source] = list(set(link_task[source]))  # 去重

    # 去除重复main函数
    log.DEBUG("主函数文件列表：", main_source)
    log.DEBUG("链接任务：", link_task)
    for source in link_task:
        del_ls = []
        for item in link_task[source]:
            if (item in main_source or item in rename_list.values()) and item != (
                source if source not in rename_list else rename_list[source]
            ):
                del_ls.append(item)
        for item in del_ls:
            link_task[source].remove(item)

    return complier_task, link_task


def create_build_dir(path: str, project_dict: dict):
    log.DEBUG("构建目录：", project_dict)
    for name in project_dict:
        if type(project_dict[name]) == dict:
            try:
                os.mkdir(os.path.join(path, name))
            except FileExistsError:
                pass
            create_build_dir(os.path.join(path, name), project_dict[name])


def generate_build_cmd(build_path: str, complier_task: list, link_task: dict):
    log.DEBUG("编译", *complier_task, sep="\n")
    log.DEBUG("链接", *link_task.items(), sep="\n")
    source_list = [
        os.path.normpath(
            os.path.abspath(os.path.join(os.path.join(build_path, ".."), file))
        )
        for file in complier_task
    ]
    if sys_type == "windows":
        object_exname = ".obj"
    elif sys_type == "linux":
        object_exname = ".o"
    else:
        raise Exception("不支持的系统类型！")
    output_list = [
        ".".join(
            os.path.normpath(os.path.join(os.path.abspath(build_path), file)).split(
                "."
            )[:-1]
        )
        + object_exname
        for file in complier_task
    ]
    log.DEBUG("源文件：", *source_list, sep="\n")
    complier_list = [
        f"{gnu} -std={std} -c {srcfile} -o {output_file}"
        for srcfile, output_file in zip(source_list, output_list)
    ]
    for i in range(len(complier_list)):
        complier_list[i] += " ".join(
            [f" -I {include_dir}" for include_dir in include_dirs]
        )
        complier_list[i] += " ".join([f" -D{define}" for define in defines])
        complier_list[i] += " ".join([f" {opt}" for opt in c_options])

    link_list = []
    # log.DEBUG("链接文件：", *link_task.items(), sep="\n")

    name_list = []
    # 生成链接命令
    for output_file, source_files in link_task.items():
        binaray_file = [
            os.path.normpath(
                os.path.abspath(
                    os.path.join(
                        build_path,
                        ".".join(source_file.split(".")[:-1]) + object_exname,
                    )
                )
            )
            for source_file in source_files
        ]
        global output_path
        if os.path.isabs(output_path):
            out_file_at = os.path.normpath(output_path)
        else:
            out_file_at = os.path.normpath(
                os.path.join(os.path.dirname(build_path), output_path)
            )

        if isWindows():
            extention_name = ".exe"
        elif isLinux():
            extention_name = ""
        else:
            raise Exception("不支持的系统类型！")

        out_file = os.path.join(
            out_file_at,
            ".".join(os.path.basename(output_file).split(".")[:-1]) + extention_name,
        )
        if not os.path.exists(out_file_at):
            os.makedirs(out_file_at)
        link_list.append(
            f"{gnu} -o {os.path.normpath(out_file)} {' '.join(binaray_file)}"
        )

    # 添加链接库参数
    for i in range(len(link_list)):
        link_list[i] += " ".join([f" -l{lib}" for lib in link])
        link_list[i] += " ".join([f" -L{lib_dir}" for lib_dir in lib_dirs])

    return complier_list, link_list


def include_extend(include_dirs: list) -> list:
    res = []
    for item in include_dirs:
        dir = item
        if dir not in res:
            res.append(dir)
        for _ in range(include_parent_depth - 1):
            dir = os.path.dirname(dir)
            if dir not in res:
                res.append(dir)
    return res


def exeute_complier_task(complier_cmd: list):
    if not complier_cmd:
        log.INFO("没有需要编译的文件")
        return True
    count = 0
    pid = 0
    mutex = Lock()
    log.INFO("正在执行编译...")
    pool = ThreadPoolExecutor(max_workers=os.cpu_count() * max_thread_every_cpu)

    def complier_progress(cmd: str, pid: int):
        nonlocal count, mutex
        log.DEBUG(f"编译进程 {pid} 开始执行：{cmd}")
        with open(
            os.path.join(build_path, f".complier_{pid}.log"), "a", encoding="utf-8"
        ) as f:
            pass
        res = os.system(
            f"{cmd} 1>>{os.path.join(build_path, f'.complier_{pid}.log')} 2>&1"
        )
        mutex.acquire()
        count += 1
        mutex.release()
        return res

    res_ls: list[Future] = []

    log.INFO("正在提交编译任务...")
    for cmd in complier_cmd:
        res_ls.append(pool.submit(complier_progress, cmd, pid))
        pid += 1

    while True:
        print(
            f"\r正在执行编译: [{'#'*int(count/len(complier_cmd)*50):.<50}] {count}/{len(complier_cmd)}",
            end="",
        )

        for i in range(len(res_ls)):
            if not res_ls[i].done():
                continue
            res = res_ls[i].result()
            if res != 0:
                print()
                log.ERROR(f"任务 {i} 编译失败！")
                with open(
                    os.path.join(build_path, f".complier_{i}.log"),
                    "r",
                    encoding="utf-8",
                ) as f:
                    log.INFO("编译器输出：")
                    for line in f:
                        if "note:" in line:
                            print("\033[36m" + line.strip() + "\033[0m")
                        elif "warning:" in line:
                            print("\033[33m" + line.strip() + "\033[0m")
                        elif "error:" in line:
                            print("\033[31m" + line.strip() + "\033[0m")
                        else:
                            print(line, end="")
                return False

        time.sleep(0.1)
        if count == len(complier_cmd):
            print(f"\r正在执行编译: [{'#'*50:.<50}] {count}/{len(complier_cmd)}")
            break

    return True


def exeute_link_task(link_cmd: list):
    if not link_cmd:
        log.INFO("没有需要链接的文件")
        return True
    count = 0
    pid = 0
    mutex = Lock()
    log.INFO("正在执行链接...")
    pool = ThreadPoolExecutor(max_workers=os.cpu_count() * max_thread_every_cpu)

    def link_progress(cmd: str, pid: int):
        nonlocal count, mutex
        log.DEBUG(f"链接进程 {pid} 开始执行：{cmd}")
        with open(
            os.path.join(build_path, f".link_{pid}.log"), "a", encoding="utf-8"
        ) as f:
            pass
        res = os.system(f"{cmd} 1>>{os.path.join(build_path, f'.link_{pid}.log')} 2>&1")
        mutex.acquire()
        count += 1
        mutex.release()
        return res

    res_ls: list[Future] = []

    log.INFO("正在提交链接任务...")
    for cmd in link_cmd:
        res_ls.append(pool.submit(link_progress, cmd, pid))
        pid += 1

    faild_count = 0

    while True:
        print(
            f"\r正在执行链接: [{'#'*int(count/len(link_cmd)*50):.<50}] {count}/{len(link_cmd)}",
            end="",
        )

        for i in range(len(res_ls)):
            if not res_ls[i].done():
                continue
            res = res_ls[i].result()
            if res != 0:
                print()
                log.ERROR(f"任务 {i} 链接失败！")
                with open(
                    os.path.join(build_path, f".link_{i}.log"),
                    "r",
                    encoding="utf-8",
                ) as f:
                    log.INFO(f"任务 {i} 的链接器输出：")
                    for line in f:
                        for item in line.split():
                            if item in ["undefined", "reference"]:
                                print("\033[31m" + item + "\033[0m", end=" ")
                            elif item in ["multiple", "definition"]:
                                print("\033[33m" + item + "\033[0m", end=" ")
                            else:
                                print(item, end=" ")
                        print()
                faild_count += 1

        time.sleep(0.1)
        if count == len(link_cmd):
            print(f"\r正在执行链接: [{'#'*50:.<50}] {count}/{len(link_cmd)}")
            break
    
    log.INFO(f"链接完成: {len(link_cmd) - faild_count}/{len(link_cmd)}")
    if faild_count:
        log.ERROR(f"链接失败: {faild_count}/{len(link_cmd)}")

    return not faild_count


def complier(options: list):
    if not options:
        log.INFO("cpm -c 命令文档:")
        print(set_options.__doc__)
        return
    path = options[0]
    if path == "/help":
        log.INFO("cpm -c 命令文档:")
        print(set_options.__doc__)
        return
    if not os.path.isdir(path):
        log.ERROR(f"'{path}'不是文件夹！")
        return
    if not os.path.exists(path):
        log.ERROR(f"路径'{path}'不存在")
        return
    if not set_options(options[1:]):
        return
    global build_path
    build_path = os.path.join(path, ".build")
    # 清理构建目录
    if rebuild and os.path.exists(build_path):
        log.INFO("正在清理构建目录...")
        shutil.rmtree(build_path)
    # 获取整个项目目录
    log.INFO("正在获取项目目录信息...")
    dict_files = get_floders_dict(path)
    log.DEBUG(dict_files)
    old_dict_files = copy.deepcopy(dict_files)
    # 创建构建目录
    if not os.path.exists(build_path):
        os.mkdir(build_path)
    create_build_dir(build_path, dict_files)
    # 确认编译器
    log.INFO("正在确认编译器...")
    res1 = os.system(
        f"{gnu} --version 1>>{os.path.join(build_path, '.cprinfo.log')} 2>&1"
    )
    res2 = os.system(f"{gnu} -v 1>>{os.path.join(build_path, '.cprinfo.log')} 2>&1")
    if res1 != 0 and res2 != 0:
        log.ERROR(f"找不到编译器: {gnu}")
        return
    # 计算每个文件的哈希值
    type_name_str = "哈希值" if rebuild or not os.path.exists(build_path) else "差异"
    log.INFO(f"正在计算{type_name_str}...")
    hash_file(hashlib.md5, dict_files, path)
    print(f"\r正在计算哈希: [{'#'*50}] {file_count}/{file_count}")
    new_dict_files = copy.deepcopy(dict_files)
    # 载入哈希值
    if os.path.exists(os.path.join(build_path, ".hash.pkl")):
        with open(os.path.join(build_path, ".hash.pkl"), "rb") as f:
            old_dict_files = pickle.load(f)
    if not os.path.exists(os.path.join(build_path, ".out")):
        os.mkdir(os.path.join(build_path, ".out"))
    # 比较哈希值
    diff_files(dict_files, old_dict_files)
    if not rebuild:
        print(
            f"\r正在比较差异: [{'#'*50:.<50}] {file_count}/{file_count}",
        )
    if not rebuild or not os.path.exists(build_path):
        global diff_file_count
        log.INFO(f"{diff_file_count} 个文件被更改")
    log.DEBUG(dict_files)
    # 构造头文件依赖表
    log.INFO("正在分析头文件依赖...")
    header_dict = tree_headers(relpath=path, project_dict=dict_files)
    if header_dict is None:
        return
    log.DEBUG(*header_dict.items(), sep="\n")
    log.INFO(f"检索到 {len(header_dict)} 个具有有效引用的头文件")
    # 构造主函数文件表
    log.INFO("正在分析链接依赖...")
    main_source, rename_list = get_main_source_files(
        relpath=path, project_dict=dict_files
    )
    log.DEBUG(main_source)
    log.INFO(f"检索到 {len(main_source)} 个具有主函数的文件")

    # 添加头文件搜索路径
    global include_dirs
    for item in header_dict:
        include_dirs.append(os.path.abspath(os.path.join(path, os.path.dirname(item))))
    include_dirs = list(set(include_dirs))

    log.INFO("正在生成任务...")
    complier_task, link_task = generate_task(
        path, dict_files, header_dict, main_source, rename_list
    )

    log.DEBUG("编译任务：", complier_task)
    log.DEBUG("链接任务：", link_task)

    include_dirs = include_extend(include_dirs)

    log.DEBUG("编译器：", gnu)
    log.DEBUG("标准：", std)
    log.DEBUG("头文件搜索路径：", include_dirs)
    log.DEBUG("库文件搜索路径：", lib_dirs)
    log.DEBUG("链接库参数：", link)
    log.DEBUG("其它编译选项：", c_options)

    # 生成编译命令
    log.INFO("正在生成编译和链接命令...")
    complier_cmd, link_cmd = generate_build_cmd(build_path, complier_task, link_task)

    log.DEBUG("编译命令：", *complier_cmd, sep="\n")
    log.DEBUG("编译命令：", *link_cmd, sep="\n")

    Faild = False
    LEN = 50
    # 执行编译命令
    if not exeute_complier_task(complier_cmd):
        return

    # 保存哈希值
    with open(os.path.join(build_path, ".hash.pkl"), "wb") as f:
        pickle.dump(new_dict_files, f)

    # 执行链接命令
    link_res = exeute_link_task(link_cmd)

    log.INFO("编译完成！")

    if run and link_res:
        log.INFO("正在启用运行...")
        for root, dirs, pragrams in os.walk(os.path.join(path, output_path)):
            for pragram in pragrams:
                if pragram.endswith(".exe" if isWindows() else ""):
                    log.INFO(f"正在运行{pragram}...")
                    log.DEBUG(os.path.join(os.path.abspath(root), pragram))
                    ret = os.system(os.path.join(os.path.abspath(root), pragram))
                    if ret != 0:
                        log.WARNING(f"程序{pragram}运行结束，返回值：{ret}")
                    else:
                        log.INFO(f"程序{pragram}运行结束，返回值：{ret}")
