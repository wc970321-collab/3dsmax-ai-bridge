# 3ds Max AI Bridge

让具备本机文件读写能力的 AI 助手，通过本地 MAXScript 文件控制正在运行的 3ds Max。支持建模、分组、材质和渲染参数设置；也可以只完成场景准备，由用户手动渲染。

本项目整理自实际使用的本地桥接脚本。已使用环境：Windows、3ds Max 2020 简体中文、V-Ray 5 Update 2.1（5.20.01）、RTX 4060 Ti。其他版本尚未验证。V-Ray 不是桥接必需依赖，V-Ray 材质或 GPU 渲染命令需要另行安装对应插件。

**GitHub 用于保存和分发工具。3ds Max 在本机运行；下载项目不会自动把普通网页聊天连接到电脑，也不包含 Autodesk / Chaos 软件或许可证。**

## 快速开始

1. 下载本仓库 ZIP 并完整解压到本机可写目录，例如 `G:\Tools\3dsmax-ai-bridge`。
2. 打开 3ds Max，在“脚本 / Scripting → 运行脚本 / Run Script”中运行 `GPT_Max_Bridge.ms`。
3. 保持 **GPT Max Bridge** 小窗口打开。启动会写出 `bridge_scene_info.txt` 和 `bridge_status.txt`，状态为 `READY`。
4. 安装 Python 3.9 或更新版本，在项目目录打开 PowerShell，先执行只读示例：

   ```powershell
   py bridge_client.py examples/scene_info.ms
   ```

   返回 `OK` 表示脚本执行完成，场景信息输出在 Max 的 MAXScript 侦听器中。Python 不在 PATH 时可使用其完整路径。桥接本身无需 Python，Python 只是方便发送命令。

5. 在空白测试场景中查看分阶段出现的三个方块：

   ```powershell
   py bridge_client.py examples/staged_boxes.ms
   ```

   示例会新增三个对象，可用一次撤销移除。尺寸使用当前场景的系统单位。

## 给本机 AI 助手的使用约定

把解压目录告诉助手，并让它读取本 README。例如：

> 通过 G:\Tools\3dsmax-ai-bridge 控制已打开的 3ds Max。先读取场景信息，再把命令写为 UTF-8 BOM 编码的 .ms 文件，用 bridge_client.py 发送。每个阶段等待 OK 后再继续，刷新视口让我看到过程。完成建模、材质和灯光后停止，提醒我手动渲染。

助手必须具备同一台电脑上的文件读写与命令执行权限。项目没有内置大模型、API Key、聊天服务、MCP 服务或网络监听端口。发送自定义脚本：

```powershell
py bridge_client.py "G:\Scripts\my_command.ms" --timeout 300
```

另一目录的客户端可以通过 `--root "G:\Tools\3dsmax-ai-bridge"` 指定桥接目录。文件路径无需修改源码；中文 MAXScript 建议用 UTF-8 BOM 保存，避免 Max 2020 的编码差异。

## 工作机制

- Max 每秒检查同目录下的 `bridge_request.ms`，先归档为 `bridge_request_<timestamp>.ms`，再通过 `fileIn` 执行。
- 客户端先写完整临时文件，然后在 Windows 上通过同目录重命名原子发布，拒绝覆盖已有待执行命令。请使用本地可写目录。
- 每个客户端请求有独立的 `runtime/<id>.txt` 完成回执，避免把上一次 `OK` 当作本次结果。只按顺序发送命令，前一个返回后再发下一个。
- 全局 `bridge_status.txt` 为 `READY / RUNNING / OK / ERROR / STOPPED`。启动时的 `bridge_scene_info.txt` 是快照，不会自动随场景更新。
- `OK` 只代表脚本未抛出异常，不能证明模型尺寸、材质外观或渲染质量正确。需要视口或实际渲染检查。

关闭桥接小窗口即停止接收新命令；不影响已经创建的场景。关闭聊天窗口后能否继续发命令取决于 AI 助手是否仍在运行。此版本没有后台服务和开机自启。

## 分阶段建模与 V-Ray

长任务建议拆成结构、柜体、材质、灯光、相机等独立命令。阶段内可使用 `completeRedraw()` 和 `windows.processPostedMessages()` 刷新视口。不要在命令中等待用户输入；MAXScript 仍在 Max 主线程执行，复杂操作可能让界面暂时忙碌。

V-Ray 5 GPU 通过本机已安装的插件工作，显卡设备、材质属性与灯光设置需要按实际场景检查。本仓库不强制切换渲染器、曝光或灯光，也不自动启动渲染。不会附带工程图、客户模型、材质贴图或本机命令历史。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| 一直等待或超时 | 确认桥接窗口打开、Max 未停在模态对话框、`--root` 与脚本目录一致。超时不取消命令；查看打印出的回执路径，确认未执行后再决定是否重发。 |
| 提示文件已存在 | 上一个请求尚未被 Max 接收。不要覆盖它；先检查 Max 和 `bridge_status.txt`。 |
| `ERROR` | 查看独立回执及 `bridge_status.txt`。异常前已完成的修改可能保留，按需要在 Max 中撤销。 |
| GPU 渲染黑或过曝 | 检查实际灯光、曝光、相机、环境、V-Ray GPU 设备设置；桥接成功不代表渲染参数正确。 |
| 无法写入或发布命令 | 移到本机可写目录；不要使用网络共享或在线同步命令目录。 |

## 本地验证

```powershell
py -m unittest discover -s tests -v
```

这些测试验证文件传输、防覆盖、回执和超时；不启动 Max，不验证 MAXScript 语法或 V-Ray 渲染。Max 中请先在空白场景运行上述两个示例，再用于工程。

## 信任与许可

命令文件会以当前用户权限执行任意 MAXScript。只执行经过检查的本地脚本；不要把桥接目录暴露为公共共享，也不要提交 API Key、运行日志、工程或客户资料。修改工程前先另存备份。

当前未附加开源许可证；公开托管不自动授予复用许可。Autodesk、3ds Max、Chaos、V-Ray 为各自权利人的商标，本项目不隶属于这些公司。
