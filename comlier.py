import os, hashlib, pickle, copy, log
import shutil, sys

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


def isLinux():
    return os.name == "posix"


def isWindows():
    return os.name == "nt"


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
    )


def islibirary(name: str):
    return name.endswith(".lib") or name.endswith(".a") or name.endswith(".so")


def set_options(option: list):
    """
    命令格式：-c {项目路径} [选项1 [选项2 [...]]]
    选项可以是以下之一：
        /help               显示此帮助信息
        /run                在编译完成后运行编译结果(不建议使用)
        /rebuild            强制重新编译
        /ign=               指定忽略的文件夹名，默认为build,dist,venv,docs,out,bin
        /ign+=              额外指定忽略的文件夹名
        /gun=               指定编译器，默认为g++
        /std=               指定编译标准，默认为c++17
        /I=                 指定额外的头文件搜索路径(不在项目内)
        /L=                 指定额外的库文件搜索路径(不在项目内)
        /l=                 指定链接库链接参数
        /D=                 指定预定义宏
        /opt=               指定其它编译选项
        /res=               指定资源文件路径
        对于可赋值的参数，多个值之间用分号分隔，如：/I=path1;path2;path3，/opt=-O2;-Wall
    """
    for item in option:
        if item.startswith("/gun="):
            global gnu
            gnu = item[5:]
            if not gnu:
                gnu = "g++"
            if not os.path.exists(gnu) and gnu not in ["g++", "gcc"]:
                log.ERROR("未找到编译器：", gnu)
                return False
        elif item.startswith("/std="):
            global std
            std = item[5:]
            if not std:
                std = "c++17"
            if gnu == "g++" or os.path.basename(gnu).startswith("g++"):
                if std not in ["c++11", "c++14", "c++17", "c++20"]:
                    log.WARNING("无效的语言标准：", std)
                    log.WARNING("已使用默认语言标准：", "c++17")
                    std = "c++17"
            elif gnu == "gcc" or os.path.basename(gnu).startswith("gcc"):
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
        else:
            log.WARNING("被忽略的未知选项：", item)

    log.DEBUG("设置选项：", " ".join(option))
    return True


def del_ignore_files(file_dict: dict):
    ls = []
    for name in file_dict:
        if name.startswith(".") or name.startswith("_"):
            ls.append(name)
            log.INFO("已忽略文件:\t", name)
            continue
        if type(file_dict[name]) == dict:
            if name in ignore_floders or name.startswith(".") or name.startswith("_"):
                ls.append(name)
                log.INFO("已忽略文件夹:\t", name)
                continue
            else:
                del_ignore_files(file_dict[name])
    for name in ls:
        del file_dict[name]
    return file_dict


# 以递归的方式读取目录并存储为字典格式
def get_floders_dict(path: str):
    files_dict = {}

    def get_files(path: str, files_dict: dict):
        # print(path, files_dict)
        for root, dirs, files in os.walk(path):
            # print(root, dirs, files)
            if dirs:  # 递归读取子目录
                for dir in dirs:
                    if dir not in files_dict:
                        files_dict[dir] = {}
                    log.DEBUG("读取到文件夹：", os.path.join(root, dir))
                    get_files(os.path.join(root, dir), files_dict[dir])
            for file in files:
                log.DEBUG("读取到文件：", os.path.join(root, file))
                files_dict[file] = "new"
            break

    get_files(path, files_dict)
    return del_ignore_files(files_dict)


def hash_file(hash_func: callable, project_dict: dict, file_path: str):
    for name in project_dict:
        if type(project_dict[name]) == str:
            log.DEBUG("计算文件哈希值：", os.path.join(file_path, name))
            with open(os.path.join(file_path, name), "rb") as f:
                project_dict[name] = hash_func(f.read()).hexdigest()
            # 若是链接库自动追加搜索路径和链接参数
            if islibirary(name):
                global link
                link.append(file_path)
                if name.endswith(".a"):
                    link.append(name[3:-2])
                elif name.endswith(".so"):
                    link.append(name[3:-3])
                elif name.endswith(".lib"):
                    link.append(name[:-4])
        else:
            hash_file(hash_func, project_dict[name], os.path.join(file_path, name))


def diff_files(project_dict: dict, old_project_dict: dict):
    for name in project_dict:
        if type(project_dict[name]) == str:
            log.DEBUG("比较先后文件差异：", name)
            if project_dict[name] == old_project_dict.get(name, ""):
                project_dict[name] = ""
            else:
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

    # 展开头文件依赖
    def expand_headers(header_dict_ls: dict):
        state = False
        for name in header_dict_ls:
            del_ele = []
            for item in header_dict_ls[name]:
                if item in header_dict:
                    del_ele.append(item)
                    state = True
            for item in del_ele:
                header_dict_ls[name].remove(item)
                header_dict_ls[name].extend(header_dict[item])
            header_dict_ls[name] = list(set(header_dict_ls[name]))  # 去重
        if state:
            expand_headers(header_dict_ls)

    expand_headers(header_dict)
    log.DEBUG(*header_dict.items(), sep="\n")

    # 去重
    # log.DEBUG("正在去重...")
    # for name in header_dict:
    #     header_dict[name] = list(set(header_dict[name]))

    return header_dict


def get_main_source_files(relpath: str, project_dict: dict):
    res = []

    # 检查是否存在main函数
    def append_main_source(path: str):
        with open(os.path.join(relpath, path), "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("int main(") or line.startswith("// main"):
                    res.append(path)
                    break

    def get_sources(path: str, project_dict: dict):
        for name in project_dict:
            if type(project_dict[name]) == str:
                if issource(name):
                    append_main_source(os.path.join(path, name))
            else:
                get_sources(os.path.join(path, name), project_dict[name])

    get_sources(".", project_dict)
    return res


def generate_task(path: str, dict_files: dict, header_dict: dict, main_source: list):
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
    log.DEBUG("头文件列表：", header_list)
    for item in header_list:
        if item in header_dict:
            task_list.remove(item)
            task_list.extend(header_dict[item])
        else:
            raise ValueError("头文件依赖错误：", item)
    # 编译任务
    complier_task = list(set(task_list))

    # 生成链接任务
    link_task = {source: [source] for source in main_source}
    for source in main_source:
        for header in header_dict:
            if source in header_dict[header]:
                link_task[source].extend(header_dict[header])
        link_task[source] = list(set(link_task[source]))  # 去重

    # 去除重复main函数
    log.DEBUG("主函数文件列表：", main_source)
    log.DEBUG("链接任务：", link_task)
    for source in link_task:
        del_ls = []
        for item in link_task[source]:
            if item in main_source and item != source:
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
    output_list = [
        ".".join(
            os.path.normpath(os.path.join(os.path.abspath(build_path), file)).split(
                "."
            )[:-1]
        )
        + ".o"
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

    # 生成链接命令
    for output_file, source_files in link_task.items():
        binaray_file = [
            os.path.normpath(
                os.path.abspath(
                    os.path.join(
                        build_path,
                        ".".join(source_file.split(".")[:-1]) + ".o",
                    )
                )
            )
            for source_file in source_files
        ]
        output_path = os.path.normpath(os.path.join(build_path, ".out"))
        out_file_at = os.path.abspath(
            os.path.join(output_path, os.path.dirname(output_file))
        )
        if isWindows():
            extention_name = ".exe"
        elif isLinux():
            extention_name = ".out"
        else:
            raise ValueError("不支持的系统类型！")

        out_file = os.path.join(
            out_file_at,
            ".".join(os.path.basename(output_file).split(".")[:-1]) + extention_name,
        )
        try:
            os.makedirs(out_file_at)
        except FileExistsError:
            pass
        link_list.append(
            f"{gnu} -o {os.path.normpath(out_file)} {' '.join(binaray_file)}"
        )

    # 添加链接库参数
    for i in range(len(link_list)):
        link_list[i] += " ".join([f" -l{lib}" for lib in link])
        link_list[i] += " ".join([f" -L{lib_dir}" for lib_dir in lib_dirs])

    return complier_list, link_list


def complier(options: list):
    if not options:
        log.ERROR("未指定项目路径！")
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
    # 计算每个文件的哈希值
    log.INFO("正在分析差异...")
    hash_file(hashlib.md5, dict_files, path)
    new_dict_files = copy.deepcopy(dict_files)
    # 载入哈希值
    try:
        with open(os.path.join(build_path, ".hash.pkl"), "rb") as f:
            old_dict_files = pickle.load(f)
    except FileNotFoundError:
        try:
            os.mkdir(build_path)
        except FileExistsError:
            pass
    create_build_dir(build_path, dict_files)
    try:
        os.mkdir(os.path.join(build_path, ".out"))
    except FileExistsError:
        pass
    # 比较哈希值
    diff_files(dict_files, old_dict_files)
    log.DEBUG(dict_files)
    # 构造头文件依赖表
    log.INFO("正在分析头文件依赖...")
    header_dict = tree_headers(relpath=path, project_dict=dict_files)
    log.DEBUG(*header_dict.items(), sep="\n")
    # 构造主函数文件表
    log.INFO("正在分析链接依赖...")
    main_source = get_main_source_files(relpath=path, project_dict=dict_files)
    log.DEBUG(main_source)

    # 添加头文件搜索路径
    global include_dirs
    for item in header_dict:
        include_dirs.append(os.path.abspath(os.path.join(path, os.path.dirname(item))))
    include_dirs = list(set(include_dirs))

    log.INFO("正在生成任务...")
    complier_task, link_task = generate_task(path, dict_files, header_dict, main_source)

    log.DEBUG("编译任务：", complier_task)
    log.DEBUG("链接任务：", link_task)

    log.DEBUG("GNU：", gnu)
    log.DEBUG("标准：", std)
    log.DEBUG("头文件搜索路径：", include_dirs)
    log.DEBUG("库文件搜索路径：", lib_dirs)
    log.DEBUG("链接库参数：", link)
    log.DEBUG("其它编译选项：", c_options)

    # 生成编译命令
    log.INFO("正在生成编译命令...")
    complier_cmd, link_cmd = generate_build_cmd(build_path, complier_task, link_task)

    log.DEBUG("编译命令：", *complier_cmd, sep="\n")
    log.DEBUG("编译命令：", *link_cmd, sep="\n")

    Faild = False
    LEN = 50
    # 执行编译命令
    if complier_cmd:
        log.INFO("正在执行编译任务...")
        count = 0
        with open(
            os.path.join(build_path, ".complier.log"), "w", encoding="utf-8"
        ) as f:
            pass
        for cmd in complier_cmd:
            count += 1
            res = os.system(
                f"{cmd} 1>>{os.path.join(build_path, '.complier.log')} 2>&1"
            )
            print(
                f"\r正在执行编译: [{'#'*int(count/len(complier_cmd)*LEN):.<50}] {count/len(complier_cmd)*100:.2f}%",
                end="",
            )
            if res != 0:
                print()
                log.ERROR("编译失败！")
                Faild = True
                break
        with open(
            os.path.join(build_path, ".complier.log"), "r", encoding="utf-8"
        ) as f:
            print("\n编译器输出：")
            for line in f:
                if "note" in line:
                    print("\033[36m" + line.strip() + "\033[0m")
                elif "warning" in line:
                    print("\033[33m" + line.strip() + "\033[0m")
                elif "error" in line:
                    print("\033[31m" + line.strip() + "\033[0m")
                else:
                    print(line, end="")
    else:
        log.INFO("没有需要编译的文件")

    if Faild:
        return

    # 保存哈希值
    with open(os.path.join(build_path, ".hash.pkl"), "wb") as f:
        pickle.dump(new_dict_files, f)

    if link_cmd:
        print("正在执行链接任务...")
        count = 0
        f_count = 0
        with open(os.path.join(build_path, ".link.log"), "w", encoding="utf-8") as f:
            pass
        for cmd in link_cmd:
            count += 1
            res = os.system(f"{cmd} 1>>{os.path.join(build_path, '.link.log')} 2>&1")
            print(
                f"\r正在执行链接: [{'#'*int(count/len(link_cmd)*LEN):.<50}] {count/len(link_cmd)*100:.2f}%",
                end="",
            )
            if res != 0:
                f_count += 1
                Faild = True
        print()
        log.INFO(f"链接成功！{len(link_cmd)-f_count}/{len(link_cmd)}")
        if f_count != 0:
            log.ERROR(f"链接失败！{f_count}/{len(link_cmd)}")
            print("链接器输出：")
            with open(
                os.path.join(build_path, ".link.log"), "r", encoding="utf-8"
            ) as f:
                for line in f:
                    for item in line.split():
                        if item in ["undefined", "reference"]:
                            print("\033[31m" + item + "\033[0m", end=" ")
                        elif item in ["multiple", "definition"]:
                            print("\033[33m" + item + "\033[0m", end=" ")
                        else:
                            print(item, end=" ")
                    print()
    else:
        log.INFO("没有需要链接的文件")

    if Faild:
        return

    log.INFO("编译完成！")

    if run:
        log.INFO("正在启用运行...")
        for root, dirs, pragrams in os.walk(os.path.join(build_path, ".out")):
            for pragram in pragrams:
                if pragram.endswith(".exe" if isWindows() else ".out"):
                    log.INFO(f"正在运行{pragram}...")
                    log.DEBUG(os.path.join(os.path.abspath(root), pragram))
                    ret = os.system(os.path.join(os.path.abspath(root), pragram))
                    log.INFO(f"程序{pragram}运行结束，返回值：{ret}")
