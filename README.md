# AUTO Auto auto

auto 是一个跨平台的命令行工具，它可以帮助开发者在不写任何Make文件的情况下，自动编译 C/C++ 项目，编译时会自动分析项目依赖关系，生成编译链接命令，并自动调用编译器进行编译。也会分析项目的文件是否发生更改，仅重新编译必要的文件，提高编译效率。同时 auto 通过识别 main 文件标记，自动生成相应的可执行文件。

## 配置

### 通过已编译文件安装
+ Windows 系统：
    + 前置条件：
        - 请确保你的系统中已经安装了 GCC 编译器或 Clang 编译器之一
    + 安装：
        - 下载 auto.exe 文件并放到任意目录
        - 将 auto.exe 所在目录添加到环境变量中
+ Linux 系统下与 Windows 系统相同，但文件为 auto(暂未提供) 而不是 auto.exe

### 通过此项目构建
+ 前置条件：
    - 请确保你的系统中已经安装了 Python 3.x 环境
    - 请确保你的系统中已经安装了 PyInstaller 工具
+ 构建步骤：
    - 克隆项目到本地：`git clone https://github.com/Anglebase/AUTO-Auto-auto.git`
    - 进入项目目录：`cd MinGW_Compiler_Package_Manager`
    - 运行构建命令：`pyinstaller --onefile --name=auto main.py`
+ 安装：
    - 构建完成后，在 dist 目录下找到 auto.exe(Windows)/auto(Linux) 文件，将其放到任意目录
    - 将 auto.exe(Windows)/auto(Linux) 所在目录添加到环境变量中

## 更新日志

### -v0.2
- 提供并发编译支持
- 提供并发链接支持
- 支持多条命令合并为一条命令执行
- 利用多线程加速文件差异分析
- 添加 `-I:` 选项，支持头文件多级父目录搜索
- 添加 `/out=` 选项，支持自定义输出路径
- 更改默认输出路径为项目根目录下的 out 目录

### -v0.1
- 跨平台支持(Windows/Linux)
- 支持 C/C++ 项目自动编译
- 支持头文件依赖自动分析
- 支持链接库依赖自动分析
- 支持生成静态链接库
- 支持生成动态链接库

## 使用

auto 的命令行参数分两种，一种是以 `-` 开头的命令参数，一种是以 `/` 开头的次级命令参数。一段有效命令以命令参数开头，到下一个命令参数之前结束。以 JsonCpp 的编译链接为例，命令如下：
```
auto -c .\jsoncpp -l /static jsoncpp /path+=.\jsoncpp\src\lib_json /at=.\jsoncpp
```
它与如下方式等价：
```
auto -c .\jsoncpp
auto -l /static jsoncpp /path+=.\jsoncpp\src\lib_json /at=.\jsoncpp
```
auto 每个主命令的执行都是独立的，次级命令参数除了特别标注之外，对顺序没有特别要求

### 依赖
auto 是一个跨平台编译工具，它依赖于开发者**已安装的编译器**，并通过分析项目依赖关系，自动生成编译链接命令并执行。

### 功能
+ 项目自动编译
    - 支持头文件依赖自动分析
    - 支持链接库依赖自动分析
    - 内容变更自动分析
    - 支持多线程编译
    - 支持多线程链接

+ 生成链接库
    - 支持生成静态链接库
    - 支持生成动态链接库

+ 命令行
    - 可以将多个命令合并为一条执行

### 示例
[auto 使用示例](./doc/test.md)

## 开发者

- [Anglebase](https://github.com/Anglebase)