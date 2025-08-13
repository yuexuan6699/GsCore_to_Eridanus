# 为Eridanus框架开发的早柚核心Docs适配器

GsCore_to_Eridanus V0.0.1

这是一个为Eridanus框架开发的早柚核心Docs适配器插件。

> [!IMPORTANT]  
> 请注意！该插件并不能开箱即用，你还需要完成Core的安装和配置！！
>
> 如果使用Docker安装Core，请务必确保HOST和PORT填写正确，该插件可以修改链接Core的HOST和PORT！！
>
> 类似ISSUES [#12] [#10] 

[早柚核心](https://docs.sayu-bot.com/)
**💖一套业务逻辑，多个平台支持！**

**🎉 [详细文档](https://docs.sayu-bot.com)** ( [快速开始(安装)](https://docs.sayu-bot.com/Started/InstallCore.html) | [链接Bot](https://docs.sayu-bot.com/LinkBots/AdapterList.html) | [插件市场](https://docs.sayu-bot.com/InstallPlugins/PluginsList.html) )

[Eridanus](https://eridanus.netlify.app/)
 基于 [OneBot](https://github.com/howmanybots/onebot/blob/master/README.md) 协议的多功能bot兼python开发框架

**[详细文档](https://eridanus.netlify.app)** ( [快速开始](https://eridanus.netlify.app/getting-started/) | [下载](https://github.com/AOrbitron/Eridanus/releases)

## 注意事项！！！！！！

- 项目作者即本人使用的是AI开发，有部分功能无法使用，我也不能保证这个项目的安全性
- 本项目你可以自由使用、修改和分发本项目的代码，但需要接受主项目Eridanus和早柚核心的开源要求
- 本项目的作者不对本项目的代码或使用本项目的结果负责。
- 本项目的作者不提供任何形式的技术支持或担保。
- 本项目的作者不负责任何因使用本项目而导致的损失或损害。
- 本项目的作者不承担任何因使用本项目而导致的法律责任。

## 功能

- 连接早柚核心服务器
- 在Eridanus和早柚核心之间转发消息
- 支持部分文本、图片、文件等多种消息类型
- 支持部分群聊和私聊消息

## 安装

将整个`GsCore_to_Eridanus`目录复制到Eridanu/run的目录中。

## 配置

在目录下的`gs_core.yaml`文件中配置以下参数：

- `BOT_ID`: Bot的唯一标识符，默认为"Eridanus"。如果需要自定义Bot的唯一标识符，请在`gs_core.yaml`文件中配置。
- `IP`: 早柚核心服务器的IP地址，默认为"127.0.0.1"
- `PORT`: 早柚核心服务器的端口号，默认为8765。如果早柚核心服务器部署在其他IP地址，请在`gs_core.yaml`文件中配置。

## 使用

启动Eridanus框架后，插件会自动连接到早柚核心服务器。确保早柚核心服务器已启动并监听指定的IP和端口。


