# MinGW Compiler&Package Manager(cpm)

cpm的设计目的是为了简化MinGW下C++项目的包管理和项目编译流程

## 功能

### 项目自动编译
```
cpm -c {project_dir} [compiler_options]
```
project_dir: 项目目录
compiler_options: 编译选项，可以是以下选项的组合：
- `/gnu=[path]`                          : 指定MinGW安装目录
- `/std=[c++11|c++14|c++17|c++20]`       : 指定编译的C++标准
- `/I=[include_path];[include_path];...` : 指定头文件搜索路径(不在项目目录下)
- `/D=[macro_name];[macro_name];...`     : 指定宏定义
- `/L=[library_path];[library_path];...` : 指定链接库搜索路径(不在项目目录下)
- `/l=[library_name];[library_name];...` : 指定链接库
- `/opt=[optimization_level]`            : 指定其它编译选项，如-O2、-Wall等

**注**：库搜索路径自动识别暂未实现
