# SK天气推送插件

# 插件简介
这是一个基于 Python nonebot 开发的酷Q机器人插件。因为是基于 CQHTTP 4 接口，所以很遗憾无法打包成cpk文件，需要进行一些相对复杂的配置，因此**不建议不熟悉酷Q或电脑小白用户使用**。

# 环境要求
* Python 3.6.1+
* nonebot 库
* nonebot scheduler 库
* 酷Q Air/Pro
* CoolQ HTTP API 插件 v4.7+
* ~~一颗肯折腾的心~~

# 配置教程

## 安装 Python
从 <a href="https://www.python.org/" target="_blank">Python 官网</a> 下载 Python 安装包并安装，**安装时注意勾选“Add to PATH”**，如果不知道在哪里可以参考 [网上的教程](https://www.liaoxuefeng.com/wiki/1016959663602400/1016959856222624)

## 安装nonebot 与 scheduler 额外库（必须安装，本插件依赖其的计划任务功能）
打开命令提示符工具，逐行输入以下命令
```
pip install nonebot
pip install "nonebot[scheduler]"
```

## 下载插件源码
从[release页面](https://github.com/songrk415/Weather-Pusher/releases)下载插件的最新源码压缩包（在“Assests”下的“Souce code(zip)”），记住文件的位置

## 运行插件
1. 到解压文件夹的根目录，按住 SHIFT 并对空白处单击右键，选择 “在此处打开 Powershell 窗口”
2. 在 Poweshell 里输入 `python bot.py`，如果看到类似以下的字段则代表运行成功。**如果出现报错，请从头检查之前步骤是否有遗漏**
```
ujson module not found, using json
msgpack not installed, MsgPackSerializer unavailable
[2020-01-04 17:11:06,938 nonebot] INFO: Succeeded to import "plugins.weather"
[2020-01-04 17:11:06,940 nonebot] INFO: Running on 0.0.0.0:8080
Running on https://0.0.0.0:8080 (CTRL + C to quit)
[2020-01-04 17:11:06,944] ASGI Framework Lifespan error, continuing without Lifespan support
[2020-01-04 17:11:06,952 nonebot] INFO: Scheduler started
```

## 更新插件
如果需要更新机器人至更高版本，只需将压缩包中 Plugins 目录下的 weather.py 覆盖至您正在使用的版本中即可，如果出现错误可以尝试删除 settings.json 或 weather_data.json 重新尝试录入

## 安装CoolQ HTTP API 插件
这里直接引用 nonebot 文档原文：
>前往 [CoolQ HTTP API 插件官方文档](https://cqhttp.cc/docs/)，按照其教程的「使用方法」安装插件。安装后，请先使用默认配置运行，并查看 酷Q 日志窗口的输出，以确定插件的加载、配置的生成和读取、插件版本等符合预期。
>>注意  
请确保你安装的插件版本 >= 4.7，通常建议插件在大版本内尽量及时升级至最新版本。

如果不知道怎么设置配置文件，请直接复制以下设置至 "<user_id>.json" 文件：
```
{
    "host": "",
    "port": 5700,
    "use_http": true,
    "ws_host": "[::]",
    "ws_port": 6700,
    "use_ws": false,
    "ws_reverse_url": "",
    "ws_reverse_api_url": "ws://127.0.0.1:8080/ws/api/",
    "ws_reverse_event_url": "ws://127.0.0.1:8080/ws/event/",
    "ws_reverse_reconnect_interval": 3000,
    "ws_reverse_reconnect_on_code_1000": true,
    "use_ws_reverse": true,
    "post_url": "",
    "access_token": "",
    "secret": "",
    "post_message_format": "string",
    "serve_data_files": false,
    "update_source": "china",
    "update_channel": "stable",
    "auto_check_update": false,
    "auto_perform_update": false,
    "show_log_console": true,
    "log_level": "info"
}
```

# 安装完成！
如果不出意外，此时私聊机器人 “天气” 即可开始设置推送地区了。如果报错或未响应，请重新阅读步骤是否有遗漏。**有问题或意见欢迎加QQ群交流：153409375**
>感谢您对本插件的支持，这是我自学 Python 制作的第一个实战项目。本来觉得这么无聊又麻烦的玩意儿谁会用啊，说明也只随便留了只言片语。但是这几天我确实看到有人下来了，还有人在评论去表达了对本插件的支持。这对菜鸟的我来说着实是莫大的鼓励。因此我又花了几天重新写了这份说明手册，并把代码上传到了 Github。介于本人能力有限，这个插件依然有诸多的不足，我今后会持续对它进行维护，直到能达到一个我比较满意的程度。  
谢谢你，读到了最后。你们的支持就是我最大的动力。

# 更新日志
- 2020.1.24（v1.1.1）
  - 搜索结果为空会提示重新搜索，同时提示正确格式
  - 选择结果会检测是否为数字
- 2020.1.23（v1.1.0）
  - 彻底重写所有api，修复国内无法使用的问题
  - 天气信息增加：日落日出，体感温度
  - 发送“天气”返回实时天气
- 2020.1.18（v1.0.0）
  - 去除爬取次数限制，直接从网页爬取数据，不再依赖api接口
- 2020.1.4（v0.1.1）
  - 重写说明手册

# 已知问题与更新计划
- 地区设定可以中途退出
- 限制用户查询频率
- 可以修改已经设定的地区
- 使用 C++ 重写应用，可以直接打包为cpk插件，不再需要配置环境（刚开始看C++，希望有生之年能做到……）
- ~~重写说明手册~~
- ~~搜索城市名返回结果为空没有任何提示~~
- ~~选择搜索结果时如果输入不为数字会直接退出，需添加提示~~
- ~~搜索城市处提示用户正确格式（只能中文城市，且不包括省份国家等）~~
- ~~已经设定天气的情况下，发送“天气”返回为实时天气~~
- ~~直接从网页端爬取数据，不在需要APIKey，不再有调用次数限制~~
