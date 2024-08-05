import os, hashlib, pickle, copy, log

has_build = False

# 忽略的文件夹
ignore_floders = ["build", "dist", "venv", "docs", "out", "bin"]
# 同时忽略所有以.或_开头的文件和文件夹

"""
参数选项             说明                          默认值
/help           显示帮助信息                         /
/gun=           指定编译器                          g++
/std=           指定编译标准                        c++17
/include_dirs=  指定额外的头文件搜索路径(不在项目内)      /
/lib_dirs=      指定额外的库文件搜索路径(不在项目内)      /
/link=          指定链接库链接参数                     /
/options=       指定其它编译选项                       /
"""

gnu = "g++"
std = "c++17"
include_dirs = []
lib_dirs = []
link = []
c_options = ""
defines = []


def set_options(option: list):
    global gnu, std, include_dirs, lib_dirs, link, c_options, defines
    for item in option:
        if item.startswith("/gun="):
            gnu = item[5:]
            if not gnu:
                gnu = "g++"
            if not os.path.exists(gnu) and gnu not in ["g++", "gcc"]:
                log.ERROR("未找到编译器：", gnu)
                exit(1)
        elif item.startswith("/std="):
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
            include_dirs = item[3:].split(";")
        elif item.startswith("/L="):
            lib_dirs = item[3:].split(";")
        elif item.startswith("/l="):
            link = item[3:].split(";")
        elif item.startswith("/opt="):
            c_options = item[5:].split(";")
        elif item.startswith("/D="):
            defines = item[3:].split(";")
        else:
            log.WARNING("被忽略的未知选项：", item)

    log.DEBUG("设置选项：", " ".join(option))


def del_ignore_files(file_dict: dict):
    ls = []
    for name in file_dict:
        if name.startswith(".") or name.startswith("_"):
            ls.append(name)
            log.INFO("已忽略文件：", name)
            continue
        if type(file_dict[name]) == dict:
            if name in ignore_floders or name.startswith(".") or name.startswith("_"):
                ls.append(name)
                log.INFO("已忽略文件夹：", name)
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
        if state:
            expand_headers(header_dict_ls)

    expand_headers(header_dict)
    log.DEBUG(*header_dict.items(), sep="\n")

    # 去重
    log.DEBUG("正在去重...")
    for name in header_dict:
        header_dict[name] = list(set(header_dict[name]))

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
    link_task = {source: [] for source in main_source}
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
        out_file = os.path.join(
            out_file_at,
            ".".join(os.path.basename(output_file).split(".")[:-1]) + ".exe",
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
    path = options[0]
    set_options(options[1:])
    build_path = os.path.join(path, ".build")
    # 获取整个项目目录
    log.INFO("正在获取项目目录信息...")
    dict_files = get_floders_dict(path)
    log.DEBUG(dict_files)
    old_dict_files = copy.deepcopy(dict_files)
    # 计算每个文件的哈希值
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
    log.INFO("正在分析差异...")
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

    # 执行编译命令
    log.INFO("正在执行编译任务...")
    Faild = False
    count = 0
    with open(os.path.join(build_path, ".complier.log"), "w") as f:
        pass
    for cmd in complier_cmd:
        count += 1
        res = os.system(f"{cmd} >>{os.path.join(build_path, '.complier.log')} 2>&1")
        print(
            f"\r正在执行编译: [{'#'*int(count/len(complier_cmd)*40):.<40}] {count/len(complier_cmd)*100:.2f}%",
            end="",
        )
        if res != 0:
            log.ERROR("\n编译失败！:", cmd)
            Faild = True
    if complier_cmd:
        with open(os.path.join(build_path, ".complier.log"), "r") as f:
            print("\n编译器输出：")
            print(f.read())
    if Faild:
        return

    print("正在执行链接任务...")
    count = 0
    with open(os.path.join(build_path, ".link.log"), "w") as f:
        pass
    for cmd in link_cmd:
        count += 1
        res = os.system(f"{cmd} >>{os.path.join(build_path, '.link.log')} 2>&1")
        print(
            f"\r正在执行链接: [{'#'*int(count/len(link_cmd)*40):.<40}] {count/len(link_cmd)*100:.2f}%",
            end="",
        )
        if res != 0:
            log.ERROR("\n链接失败！:", cmd)
            Faild = True
    if link_cmd:
        print("\n链接器输出：")
        with open(os.path.join(build_path, ".link.log"), "r") as f:
            print(f.read())
    if Faild:
        return

    log.INFO("编译完成！")
    # 保存哈希值
    with open(os.path.join(build_path, ".hash.pkl"), "wb") as f:
        pickle.dump(new_dict_files, f)
