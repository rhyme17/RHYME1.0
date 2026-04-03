# 本地音乐播放器

## 项目概述

这是一个基于Python和PyQt5开发的纯本地音乐播放器，所有功能都在本地实现，无需后端服务，响应速度快，用户体验流畅。

## 项目结构

```
RHYME/
├── frontend/            # 多端前端聚合目录
│   ├── app.py           # 兼容入口（转发到Windows桌面端）
│   ├── requirements.txt # 依赖包列表
│   ├── apps/
│   │   ├── desktop/
│   │   │   ├── windows/ # Windows桌面端(PyQt5)
│   │   │   │   ├── app.py
│   │   │   │   ├── playlists.json
│   │   │   │   ├── settings.json
│   │   │   │   └── modules/
│   │   │   │       ├── ui_mixin.py
│   │   │   │       ├── playback_mixin.py
│   │   │   │       ├── playlist_mixin.py
│   │   │   │       ├── library_mixin.py
│   │   │   │       ├── lyrics_mixin.py
│   │   │   │       ├── shortcut_mixin.py
│   │   │   │       ├── persistence_mixin.py
│   │   │   │       ├── lifecycle_mixin.py
│   │   │   │       ├── scan_worker.py
│   │   │   │       └── lyrics_worker.py
│   │   │   └── linux/   # Linux桌面端预留
│   │   ├── mobile/      # 手机端预留
│   │   └── web/         # Web端
│   │       ├── index.html
│   │       ├── script.js
│   │       └── style.css
│   ├── core/            # 共享业务核心
│   ├── utils/           # 共享工具
│   ├── tests/           # 回归测试
│   └── tools/           # 基准与报告模板
├── README.md          # 项目说明文档
├── start.bat          # Windows启动脚本
└── start.sh           # Linux/Mac启动脚本
```

## 技术栈

- **桌面端**：Python, PyQt5
- **音频播放**：pydub + sounddevice（需系统可用 `ffmpeg`）
- **元数据解析**：mutagen
- **架构**：当前主实现为 Windows 桌面端本地应用

## 功能特性

### 核心功能
- **本地音乐文件扫描**：支持MP3、FLAC、WAV、AAC、OGG、M4A格式
- **音乐库管理**：按艺术家和专辑分类
- **关键词搜索**：实时搜索音乐
- **播放控制**：播放、暂停、上一首、下一首
- **音量调节**：滑块调节音量，支持静音
- **音量记忆**：自动保存并恢复上次使用的音量
- **播放记忆**：重启程序后恢复上次使用的歌单、上次播放歌曲和进度（不自动播放）
- **进度保护**：播放中按低频自动保存进度，异常退出后可尽量从接近位置恢复
- **播放模式**：顺序播放、随机播放、单曲循环
- **托盘行为**：可在设置中开启“关闭时隐藏到托盘”；首次点击关闭会提示选择“隐藏到托盘”或“关闭程序”
- **多歌单管理**：支持多个歌单、歌单内增删歌曲、清空当前歌单
- **一键生成歌单**：将扫描目录中的歌曲一键保存为歌单，默认名为文件夹名并可自定义
- **进度控制**：显示播放进度，支持拖动调整
- **键盘快捷键**：空格播放/暂停，上下调音量，左右调进度，Ctrl+左右切歌，Delete 移除当前歌单选中歌曲
- **异步扫描**：大目录扫描不阻塞界面
- **歌词A方案**：自动读取本地 `.lrc`（同名、同目录 `lyrics/`、标题-艺术家命名）
- **歌词B方案（在线抓取）**：无本地歌词时自动尝试在线抓取并保存为本地 `.lrc`
- **歌词C方案**：在线抓取失败后，可手动触发离线ASR识别并缓存为 `.lrc`
- **繁简规范化**：离线ASR结果默认转为简体中文（可配置关闭）

### 用户界面
- **响应式设计**：窗口大小可调整
- **标签页切换**：全部音乐、艺术家、专辑
- **分割器**：可调整左右面板大小
- **美观布局**：现代化的界面设计

## 快速开始

### 安装依赖

```bash
cd frontend
pip install -r requirements.txt

# 或在项目根目录安装同版本依赖
# pip install -r requirements.txt
```

> 说明：离线ASR依赖 `faster-whisper` 与 `ctranslate2`，首次识别会加载模型，耗时取决于机器性能。

### 系统工具依赖

- 需要系统已安装 `ffmpeg`，并可在终端直接执行 `ffmpeg -version`
- Windows 建议将 `ffmpeg` 可执行文件目录加入 `PATH`

### Hugging Face 配置（离线歌词识别推荐）

离线ASR会从 Hugging Face 拉取模型。未配置 `HF_TOKEN` 也能使用，但下载速度和频率限制可能更严格。

1. 登录 `https://huggingface.co`
2. 进入 `Settings -> Access Tokens`
3. 创建新 Token（权限选 `Read` 即可）
4. 将 Token 配置到环境变量 `HF_TOKEN`

PowerShell（当前终端）：

```powershell
$env:HF_TOKEN="hf_你的token"
```

PowerShell（永久写入当前用户）：

```powershell
[Environment]::SetEnvironmentVariable("HF_TOKEN","hf_你的token","User")
```

如果你只想关闭 symlink 提示（不影响功能）：

```powershell
[Environment]::SetEnvironmentVariable("HF_HUB_DISABLE_SYMLINKS_WARNING","1","User")
```

### Windows symlink 告警说明

当终端提示 `cache-system uses symlinks ... your machine does not support them` 时，含义是：

- 仍可正常下载与识别歌词
- 但缓存可能更占磁盘空间
- 可通过开启 Windows Developer Mode 或使用管理员权限运行来优化缓存行为

### ASR 设备配置（CPU优先）

当前离线歌词识别默认使用 CPU，避免缺少 CUDA 依赖时出现 `cublas64_12.dll` 错误。

- 默认：`RHYME_ASR_DEVICE=cpu`、`RHYME_ASR_COMPUTE_TYPE=float32`
- 可选 GPU：手动设置 `RHYME_ASR_DEVICE=cuda`（需本机 CUDA 运行库完整）
- 精度调优：`RHYME_ASR_MODEL_SIZE`（如 `small`/`medium`）、`RHYME_ASR_BEAM_SIZE`（建议 `5~8`）、`RHYME_ASR_VAD_FILTER`（歌曲建议 `false`）
- 文本规范：`RHYME_ASR_TO_SIMPLIFIED=true`（默认）将繁体识别结果转为简体；设为 `false` 可保留原文
- 当配置为 `cuda` 但缺少 `cublas64_12.dll` 时，会自动回退到 `cpu+float32` 继续识别

PowerShell（当前终端）：

```powershell
$env:RHYME_ASR_DEVICE="cpu"
$env:RHYME_ASR_COMPUTE_TYPE="float32"
$env:RHYME_ASR_MODEL_SIZE="medium"
$env:RHYME_ASR_BEAM_SIZE="8"
$env:RHYME_ASR_VAD_FILTER="false"
$env:RHYME_ASR_TO_SIMPLIFIED="true"
```

### 启动应用

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```


**或直接运行：**
```bash
cd frontend/apps/desktop/windows
python app.py
```

## Windows 打包（不依赖解释器运行）

推荐将打包产物和构建缓存分离：

- `dist/windows/RHYME/`：可分发应用目录（含 `RHYME.exe`）
- `build/pyinstaller/`：PyInstaller 中间文件（可删除）

### 安装打包依赖

```powershell
cd D:\Projects\PycharmProjects\RHYME
.\.venv\Scripts\activate
pip install -r frontend\requirements-dev.txt
```

### 一键打包

```powershell
cd D:\Projects\PycharmProjects\RHYME
powershell -ExecutionPolicy Bypass -File frontend\tools\build_windows_package.ps1 -Clean
```

打包完成后产物在：

- `dist/windows/RHYME/RHYME.exe`

### 生成安装包（双击安装）

推荐使用 Inno Setup 将打包目录转换为安装程序：

```powershell
cd D:\Projects\PycharmProjects\RHYME
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "build\windows\RHYME.iss"
```

安装包建议输出：

- `dist/installer/RHYME-Setup.exe`

> 可在仓库中配套维护发布说明模板：`.github/release-template.md`

### 打包后的数据目录

- 开发态（直接 `python app.py`）：配置文件仍写入 `frontend/apps/desktop/windows/`
- 打包态（`sys.frozen=True`）：默认写入 `%LOCALAPPDATA%\RHYME`
- 可用 `RHYME_USER_DATA_DIR` 强制覆盖数据目录（便携模式）

### 使用说明

1. **扫描音乐**：
   - 点击"添加音乐"打开扫描弹窗并选择音乐文件夹
   - 点击"开始扫描"后会显示实时进度（已扫描/总计）
   - 扫描过程中可点击"取消扫描"中断任务，取消完成后会自动恢复可操作状态

2. **播放音乐**：
   - 在音乐库列表中双击歌曲直接播放
   - 或在播放列表中双击歌曲播放

3. **管理播放列表**：
   - 扫描完成后，歌单名默认填入扫描文件夹名，可手动修改
   - 点击"保存扫描为歌单"一键创建歌单
   - 单击歌单切换当前歌单，双击歌单从第一首直接播放
   - 选中音乐库中的歌曲点击"添加"加入当前歌单
   - 在歌单歌曲区选中歌曲点击"移除"删除
   - 点击"清空"按钮清空当前歌单

4. **控制播放**：
   - 使用底部控制栏的按钮控制播放（播放/暂停/上一首/下一首）
   - 拖动音量滑块调节音量
   - 点击静音按钮切换静音状态
   - 点击播放模式按钮切换播放模式
   - 拖动进度条调整播放位置
   - 键盘快捷键：
     - 空格：播放/暂停
     - 上/下方向键：音量加/减
     - 左/右方向键：快退/快进 5 秒
     - Ctrl+左/右方向键：上一首/下一首
     - Delete：移除当前歌单选中歌曲

5. **搜索音乐**：
   - 在搜索框中输入关键词，实时过滤音乐列表

6. **分类浏览**：
   - 点击"艺术家"标签查看按艺术家分类的音乐
   - 点击"专辑"标签查看按专辑分类的音乐
   - 点击艺术家或专辑名称查看对应的歌曲

7. **歌词功能（A + B + C）**：
   - 播放歌曲时优先自动匹配本地 `.lrc` 文件
   - 本地无歌词时自动尝试在线抓取（Gequbao），成功后会保存到歌曲同级 `lyrics/` 目录并自动加载
   - 在线抓取失败时，不自动执行ASR；用户可点击“识别歌词”手动触发离线识别（ASR）
   - 识别成功后会将歌词复制到歌曲同级 `lyrics/` 目录，默认优先用歌曲名导出；若标题疑似乱码/哈希名会自动回退为音频文件名
   - “识别歌词”按钮支持重复触发（包括已有歌词时），便于多次尝试参数效果
   - 离线ASR结果默认转简体中文；如需保留繁体可设置 `RHYME_ASR_TO_SIMPLIFIED=false`
   - 识别完成后当前播放界面自动刷新歌词；后续播放直接复用缓存

8. **歌词排障（A + B + C）**：
   - 有 `.lrc` 但未显示：检查是否与音频同名，或位于同目录 `lyrics/` 子目录
   - 在线抓取失败：查看状态栏错误提示；失败时会在 `.lyrics_cache/debug_online/` 保留 `debug_search.html` 与 `debug_detail.html`
   - 无本地歌词且点击“识别歌词”后无结果：确认已安装 `faster-whisper`、`ctranslate2`，并且 `ffmpeg` 可用
   - 识别慢或下载告警：配置 `HF_TOKEN`，首次下载模型后再次播放会明显更快
   - 报 `cublas64_12.dll`：将 `RHYME_ASR_DEVICE` 设为 `cpu`；新版本在 `cuda` 失败时也会自动回退 CPU
   - 识别失败：查看终端错误信息（例如模型下载失败、音频不可读、依赖缺失）

## 架构说明

### 纯本地架构优势

1. **响应速度快**：所有操作都在本地完成，无网络延迟
2. **真正的音频播放**：基于pydub + sounddevice的本地播放
3. **简化架构**：移除后端服务，降低项目复杂度
4. **易于部署**：无需启动多个服务，单个应用即可运行
5. **资源占用低**：无需维护HTTP服务和网络通信

### 核心组件

- **MusicPlayer类**：主窗口类，组合多个 Mixins 管理 UI 与交互
- **AudioBackend抽象**：可替换音频后端接口
- **AudioPlayer实现**：基于pydub解码 + sounddevice输出
- **音乐库管理**：本地文件扫描和元数据管理
- **播放列表管理**：内存中的播放列表管理
- **歌词服务（A+B+C）**：本地LRC解析 + 在线歌词抓取 + 离线ASR生成缓存
- **UI组件**：PyQt5提供的各种界面组件

### 歌词文件规则

- 编码优先：`UTF-8`（兼容 `GB18030` / `GBK`）
- 时间戳格式：`[mm:ss.xx]` 或 `[mm:ss.xxx]`
- 推荐命名：与音频同名，例如 `song.mp3` 对应 `song.lrc`
- 兼容命名：`标题 - 艺术家.lrc`、`艺术家 - 标题.lrc`、`lyrics/` 子目录

## 性能基线

可使用扫描基准脚本记录优化前后差异：

```bash
cd frontend
python tools/benchmark_scan.py . --repeat 3
```

性能对比报告可使用模板：`frontend/tools/perf_compare_report_template.md`

## 回归测试

项目提供了最小回归测试，覆盖扫描稳定性、播放器状态机和seek边界：

```bash
cd frontend
pytest -q
```

仅运行 Windows UI 冒烟回归：

```bash
cd frontend
pytest -q tests/test_windows_ui_smoke_regression.py
```

## 开发工具链（推荐）

新增开发依赖文件：`frontend/requirements-dev.txt`

```bash
cd frontend
pip install -r requirements-dev.txt
```

基础质量检查命令：

```bash
cd frontend
ruff check .
mypy core apps
pytest -q
```

说明：项目已补充 `frontend/pyproject.toml`，统一了 `ruff`、`mypy`、`pytest` 的基础配置。

### 日志配置（新增）

应用默认输出控制台日志。可通过环境变量启用文件日志（按天滚动）：

- `RHYME_LOG_LEVEL`：日志级别，默认 `INFO`
- `RHYME_LOG_TO_FILE`：是否写入文件（`true/false`），默认 `false`
- `RHYME_LOG_DIR`：日志目录，默认 `<当前工作目录>/logs`
- `RHYME_LOG_BACKUP_DAYS`：滚动日志保留天数，默认 `7`

PowerShell 示例：

```powershell
$env:RHYME_LOG_LEVEL="INFO"
$env:RHYME_LOG_TO_FILE="true"
$env:RHYME_LOG_DIR="D:\\Logs\\RHYME"
$env:RHYME_LOG_BACKUP_DAYS="14"
```

## 开发说明

### 代码结构

```python
class MusicPlayer(QMainWindow):
    - __init__(): 初始化核心组件与状态
    - 通过 Mixins 组合职责
    - ...
```

Windows 桌面端模块化拆分（`frontend/apps/desktop/windows/modules/`）：
- `ui_mixin.py`：界面构建与控件信号连接
- `library_mixin.py`：扫描、搜索、分类与库列表渲染
- `playlist_mixin.py`：歌单增删改、切换、拖拽排序与撤销
- `playback_mixin.py`：播放状态机、进度/音量/模式控制
- `lyrics_mixin.py`：歌词加载、ASR触发与刷新
- `persistence_mixin.py`：`playlists.json` 与 `settings.json` 读写
- `lifecycle_mixin.py`：周期更新与窗口关闭清理
- `shortcut_mixin.py`：键盘快捷键绑定与输入焦点保护

### 信号槽机制

应用使用PyQt5的信号槽机制处理异步事件：
- `ScanWorker.finished`: 扫描线程结束
- `QTimer.timeout`: 进度与界面刷新

## 注意事项

1. **音频格式支持**：需要系统安装相应的音频解码器
2. **文件路径**：确保音乐文件路径正确，应用有权限访问
3. **音量控制**：系统音量也会影响播放音量
4. **ffmpeg 运行时**：`pydub` 依赖系统 `ffmpeg` 可执行文件进行解码
5. **Web 目录说明**：`frontend/apps/web` 仍是历史 API 版页面，依赖后端接口；当前仓库默认可运行的是 Windows 桌面端
6. **导入路径规范**：桌面端与核心模块统一使用 `frontend.*` 或包内相对导入，减少不同启动目录导致的导入异常
7. **这是一个开发环境的实现**：生产环境需要进一步优化

### 设置项说明（当前实现）

- **输出设备策略**：`follow_system`（跟随系统默认）或 `fixed_current`（固定为当前设备）
- **音量统一强度**：`off` / `light` / `medium` / `strong`
- 为兼容旧配置，程序会自动将历史值 `fixed` 映射为 `fixed_current`，`low/high` 映射为 `light/strong`

## 后续优化方向

1. **音频元数据读取**：使用mutagen库读取音频文件的元数据（标题、艺术家、专辑等）
2. **专辑封面显示**：显示歌曲的专辑封面
3. **歌词显示**：同步显示歌词
4. **均衡器**：添加音频均衡器功能
5. **播放历史**：记录最近播放的歌曲
6. **快捷键支持**：添加全局快捷键
7. **系统托盘**：细化托盘交互与多显示器/任务栏兼容
8. **皮肤主题**：支持更换界面主题

## 许可证

MIT License
