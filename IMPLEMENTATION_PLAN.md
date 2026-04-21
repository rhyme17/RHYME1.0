# RHYME 功能实施计划

## 文档信息

- **项目名称**：RHYME 本地音乐播放器
- **文档版本**：v1.0
- **创建日期**：2026-04-14
- **计划周期**：2026年4月 - 2026年12月

---

## 一、功能需求总览

### 1.1 需求分类

| 分类 | 功能项 | 优先级 | 预计工时 |
|------|--------|--------|---------|
| **音频体验** | 音频可视化效果（频谱柱状图） | 高 | 40h |
| **音频体验** | 淡入淡出效果（可配置时长） | 中 | 20h |
| **音频体验** | 音量调节平滑过渡 | 中 | 15h |
| **歌词功能** | 歌词时间轴微调功能 | 高 | 30h |
| **歌词功能** | 简易歌词编辑器 | 高 | 40h |
| **界面增强** | 迷你播放器模式 | 高 | 35h |
| **界面增强** | 桌面歌词功能 | 高 | 45h |
| **歌单管理** | 歌单排序功能 | 中 | 15h |
| **性能优化** | 虚拟滚动 | 高 | 50h |
| **性能优化** | 懒加载机制 | 高 | 30h |
| **性能优化** | 后台预加载 | 中 | 20h |
| **性能优化** | 内存优化 | 中 | 25h |
| **性能优化** | 启动优化 | 中 | 20h |
| **性能优化** | SQLite 数据库优化 | 高 | 60h |
| **交互增强** | 拖拽操作增强 | 中 | 25h |
| **交互增强** | 添加到下一首播放 | 中 | 15h |

**总计工时**：约 485 小时

---

## 二、分阶段实施计划

### 阶段一：音频体验增强（第1-4周）

#### 目标
提升音频播放体验，增加视觉反馈和流畅度

#### 任务清单

##### 1. 音频可视化效果（频谱柱状图）

**技术方案**：
- 使用 `numpy.fft` 进行实时频谱分析
- 从 `sounddevice` 获取音频数据流
- 使用 `QPainter` 绘制频谱柱状图
- 通过 `QTimer` 实现 60fps 刷新

**实现步骤**：
1. 创建 `AudioVisualizerWidget` 类
   - 继承 `QWidget`
   - 实现 `paintEvent` 绘制逻辑
   - 添加频谱数据缓冲区

2. 修改 `AudioPlayer` 类
   - 添加音频数据回调
   - 实现 FFT 变换
   - 提供频谱数据接口

3. 集成到主窗口
   - 在播放控制栏上方添加可视化区域
   - 可配置显示/隐藏
   - 支持多种可视化样式（柱状图、波形等）

**关键代码位置**：
- 新建：`frontend/apps/desktop/windows/modules/audio_visualizer.py`
- 修改：`frontend/core/player.py`
- 修改：`frontend/apps/desktop/windows/modules/ui_mixin.py`

**测试要点**：
- 性能测试：确保不影响播放流畅度
- 内存测试：检查是否有内存泄漏
- 兼容性测试：不同音频格式的表现

##### 2. 淡入淡出效果

**技术方案**：
- 在播放开始时逐渐提升音量
- 在播放结束或切歌时逐渐降低音量
- 使用 `QTimer` 实现平滑过渡

**实现步骤**：
1. 在 `AudioPlayer` 中添加淡入淡出方法
   ```python
   def fade_in(self, duration_ms=1000):
       # 从 0 音量渐变到目标音量
   
   def fade_out(self, duration_ms=1000):
       # 从当前音量渐变到 0
   ```

2. 在播放控制逻辑中集成
   - 播放开始时调用 `fade_in`
   - 切歌前调用 `fade_out`
   - 暂停时可选淡出

3. 添加配置选项
   - 在设置中添加"淡入淡出时长"滑块
   - 可选择启用/禁用

**关键代码位置**：
- 修改：`frontend/core/player.py`
- 修改：`frontend/apps/desktop/windows/modules/playback_mixin.py`
- 修改：`frontend/apps/desktop/windows/modules/settings_dialog.py`

##### 3. 音量调节平滑过渡

**技术方案**：
- 音量滑块拖动时使用动画效果
- 避免突然的音量变化

**实现步骤**：
1. 创建音量动画类
   - 使用 `QPropertyAnimation`
   - 平滑过渡音量值

2. 修改音量调节逻辑
   - 拦截音量滑块的直接设置
   - 使用动画过渡

**关键代码位置**：
- 修改：`frontend/apps/desktop/windows/modules/playback_mixin.py`

---

### 阶段二：歌词功能增强（第5-8周）

#### 目标
完善歌词功能，提供编辑和调整能力

#### 任务清单

##### 1. 歌词时间轴微调功能

**技术方案**：
- 提供全局偏移量设置（±10秒）
- 实时预览调整效果
- 保存偏移量到缓存或 LRC 文件

**实现步骤**：
1. 在歌词显示区域添加控制按钮
   - "提前 0.5秒" / "延后 0.5秒" 按钮
   - 偏移量显示标签
   - "重置" 按钮

2. 修改歌词解析逻辑
   ```python
   def parse_lrc_with_offset(file_path, offset_seconds=0):
       # 解析 LRC 文件并应用偏移量
   ```

3. 实现偏移量持久化
   - 保存到 `.lyrics_cache/offsets.json`
   - 或直接修改 LRC 文件的时间戳

**关键代码位置**：
- 修改：`frontend/core/lrc_parser.py`
- 修改：`frontend/apps/desktop/windows/modules/lyrics_mixin.py`
- 新建：`frontend/apps/desktop/windows/modules/lyrics_offset_dialog.py`

##### 2. 简易歌词编辑器

**技术方案**：
- 提供文本编辑界面
- 支持时间戳编辑
- 实时预览效果

**实现步骤**：
1. 创建歌词编辑器对话框
   - `QTextEdit` 显示歌词文本
   - 时间戳高亮显示
   - 播放按钮实时预览

2. 实现编辑功能
   - 添加/删除时间戳
   - 修改歌词文本
   - 调整时间戳位置

3. 保存功能
   - 保存为 LRC 文件
   - 覆盖原文件或另存

**关键代码位置**：
- 新建：`frontend/apps/desktop/windows/modules/lyrics_editor_dialog.py`
- 修改：`frontend/core/lrc_parser.py`

##### 3. 桌面歌词功能

**技术方案**：
- 创建独立的无边框透明窗口
- 窗口置顶显示
- 支持拖动和调整大小

**实现步骤**：
1. 创建桌面歌词窗口类
   ```python
   class DesktopLyricsWindow(QWidget):
       def __init__(self):
           # 设置窗口标志
           self.setWindowFlags(
               Qt.WindowStaysOnTopHint |
               Qt.FramelessWindowHint |
               Qt.Tool
           )
           # 设置透明背景
           self.setAttribute(Qt.WA_TranslucentBackground)
   ```

2. 实现歌词显示逻辑
   - 同步当前播放歌词
   - 支持字体、颜色自定义
   - 支持双行显示

3. 添加控制功能
   - 右键菜单（关闭、设置、锁定位置）
   - 拖动窗口
   - 调整窗口大小

**关键代码位置**：
- 新建：`frontend/apps/desktop/windows/modules/desktop_lyrics_window.py`
- 修改：`frontend/apps/desktop/windows/modules/lyrics_mixin.py`

---

### 阶段三：界面与交互优化（第9-12周）

#### 目标
优化用户界面，提升交互体验

#### 任务清单

##### 1. 迷你播放器模式

**技术方案**：
- 创建小型播放器窗口
- 只显示核心控制元素
- 支持快速切换回主窗口

**实现步骤**：
1. 创建迷你播放器窗口
   - 显示歌曲名、艺术家
   - 显示当前歌词（可选）
   - 基本播放控制按钮
   - 音量滑块

2. 实现窗口切换
   - 主窗口添加"迷你模式"按钮
   - 迷你窗口添加"恢复主窗口"按钮
   - 记住窗口位置和大小

3. 状态同步
   - 播放状态同步
   - 歌曲信息同步
   - 歌词同步

**关键代码位置**：
- 新建：`frontend/apps/desktop/windows/modules/mini_player_window.py`
- 修改：`frontend/apps/desktop/windows/modules/ui_mixin.py`

##### 2. 拖拽操作增强

**技术方案**：
- 支持文件拖拽添加到音乐库
- 支持歌曲拖拽排序
- 支持拖拽到歌单

**实现步骤**：
1. 实现文件拖拽添加
   - 重写 `dragEnterEvent` 和 `dropEvent`
   - 过滤支持的音频格式
   - 添加到当前歌单或音乐库

2. 实现歌曲拖拽排序
   - 使用 `QListWidget.setDragDropMode`
   - 实现拖拽排序逻辑
   - 保存排序结果

3. 实现拖拽到歌单
   - 拖拽歌曲到歌单列表
   - 添加到目标歌单

**关键代码位置**：
- 修改：`frontend/apps/desktop/windows/modules/library_mixin.py`
- 修改：`frontend/apps/desktop/windows/modules/playlist_mixin.py`

##### 3. 添加到下一首播放

**技术方案**：
- 维护一个临时播放队列
- 在当前歌曲播放完后播放队列中的歌曲

**实现步骤**：
1. 添加"下一首播放"功能
   - 右键菜单添加"下一首播放"选项
   - 维护临时播放队列

2. 修改播放逻辑
   - 播放完当前歌曲后检查队列
   - 如果队列有歌曲则播放队列歌曲
   - 否则按正常顺序播放

**关键代码位置**：
- 修改：`frontend/apps/desktop/windows/modules/playback_mixin.py`
- 修改：`frontend/apps/desktop/windows/modules/playlist_mixin.py`

##### 4. 歌单排序功能

**技术方案**：
- 提供多种排序方式
- 支持升序/降序

**实现步骤**：
1. 添加排序选项
   - 按名称排序
   - 按歌曲数排序
   - 按创建时间排序
   - 按播放次数排序

2. 实现排序逻辑
   ```python
   def sort_playlists(sort_by='name', order='asc'):
       # 排序歌单列表
   ```

**关键代码位置**：
- 修改：`frontend/apps/desktop/windows/modules/playlist_mixin.py`

---

### 阶段四：性能优化（第13-20周）

#### 目标
优化性能，提升大型音乐库的处理能力

#### 任务清单

##### 1. 虚拟滚动实现

**技术方案**：
- 只渲染可见区域的歌曲项
- 动态加载和卸载列表项
- 使用 `QAbstractItemModel`

**实现步骤**：
1. 创建虚拟列表模型
   ```python
   class VirtualSongModel(QAbstractListModel):
       def rowCount(self, parent):
           return len(self.songs)
       
       def data(self, index, role):
           # 按需加载歌曲数据
   ```

2. 实现懒加载
   - 只加载当前可见的歌曲信息
   - 滚动时动态加载新数据
   - 缓存已加载的数据

3. 优化渲染
   - 使用 `QListView` 替代 `QListWidget`
   - 实现 `QItemDelegate` 自定义渲染

**关键代码位置**：
- 新建：`frontend/apps/desktop/windows/modules/virtual_song_model.py`
- 修改：`frontend/apps/desktop/windows/modules/library_mixin.py`

##### 2. 懒加载机制

**技术方案**：
- 按需加载歌曲详细信息
- 延迟加载专辑封面等大资源

**实现步骤**：
1. 分级加载歌曲信息
   - 第一级：基本信息（标题、艺术家、时长）
   - 第二级：详细信息（专辑、年份、流派）
   - 第三级：专辑封面

2. 实现后台加载
   - 使用 `QThreadPool` 后台加载
   - 加载完成后更新界面

**关键代码位置**：
- 修改：`frontend/core/library.py`
- 修改：`frontend/apps/desktop/windows/modules/library_mixin.py`

##### 3. 后台预加载

**技术方案**：
- 预加载下一首歌曲
- 减少切歌时的加载时间

**实现步骤**：
1. 实现预加载逻辑
   - 播放当前歌曲时预加载下一首
   - 预解码音频数据
   - 缓存到内存

2. 智能预加载
   - 根据播放模式预加载
   - 随机模式下预加载多首
   - 限制预加载数量避免内存占用过高

**关键代码位置**：
- 修改：`frontend/core/player.py`
- 修改：`frontend/apps/desktop/windows/modules/playback_mixin.py`

##### 4. 内存优化

**技术方案**：
- 及时释放不用的资源
- 限制缓存大小
- 使用弱引用

**实现步骤**：
1. 实现缓存管理
   - LRU 缓存策略
   - 限制缓存大小
   - 定期清理过期缓存

2. 优化资源加载
   - 使用 `QPixmapCache` 管理图片缓存
   - 及时释放不用的 `QPixmap`
   - 避免重复加载相同资源

**关键代码位置**：
- 新建：`frontend/utils/cache_manager.py`
- 修改：多个模块

##### 5. 启动优化

**技术方案**：
- 延迟加载非必要组件
- 并行初始化
- 优化导入时间

**实现步骤**：
1. 延迟加载
   - 首先显示主窗口
   - 后台加载音乐库
   - 延迟加载设置、主题等

2. 并行初始化
   - 使用多线程初始化不同模块
   - 避免阻塞主线程

**关键代码位置**：
- 修改：`frontend/apps/desktop/windows/app.py`
- 修改：`frontend/apps/desktop/windows/modules/app_setup.py`

##### 6. SQLite 数据库优化

**技术方案**：
- 使用 SQLite 替代 JSON 存储大型音乐库
- 提供数据迁移工具

**实现步骤**：

**第1步：设计数据库结构**

```sql
-- 歌曲表
CREATE TABLE songs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    artist TEXT,
    album TEXT,
    duration INTEGER,
    file_path TEXT UNIQUE NOT NULL,
    file_size INTEGER,
    modified_time INTEGER,
    created_at INTEGER,
    play_count INTEGER DEFAULT 0,
    last_played_at INTEGER
);

-- 歌单表
CREATE TABLE playlists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at INTEGER,
    updated_at INTEGER,
    song_count INTEGER DEFAULT 0
);

-- 歌单歌曲关联表
CREATE TABLE playlist_songs (
    playlist_id TEXT,
    song_id TEXT,
    position INTEGER,
    added_at INTEGER,
    PRIMARY KEY (playlist_id, song_id, position),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
    FOREIGN KEY (song_id) REFERENCES songs(id)
);

-- 索引
CREATE INDEX idx_songs_artist ON songs(artist);
CREATE INDEX idx_songs_album ON songs(album);
CREATE INDEX idx_songs_title ON songs(title);
CREATE INDEX idx_playlist_songs_playlist ON playlist_songs(playlist_id);
```

**第2步：创建数据库管理类**

```python
class MusicDatabase:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.init_tables()
    
    def add_song(self, song_info):
        # 添加歌曲
    
    def get_songs_by_artist(self, artist):
        # 按艺术家查询
    
    def search_songs(self, keyword):
        # 搜索歌曲
```

**第3步：实现数据迁移**

```python
def migrate_from_json_to_sqlite(json_path, db_path):
    # 读取 JSON 数据
    # 写入 SQLite 数据库
    # 验证数据完整性
```

**第4步：修改业务逻辑**

- 修改 `MusicLibrary` 类使用数据库
- 修改 `PlaylistMixin` 使用数据库
- 保持接口不变，只改实现

**关键代码位置**：
- 新建：`frontend/core/database.py`
- 修改：`frontend/core/library.py`
- 修改：`frontend/core/playlist.py`
- 新建：`frontend/tools/migrate_to_sqlite.py`

---

## 三、技术难点与解决方案

### 3.1 音频可视化性能

**难点**：
- 实时 FFT 计算可能影响播放性能
- 60fps 刷新可能导致 CPU 占用高

**解决方案**：
- 使用 `numpy` 优化的 FFT 实现
- 降低频谱分辨率（如 64 个频段）
- 提供性能选项（关闭可视化、降低刷新率）
- 在独立线程中计算频谱

### 3.2 桌面歌词窗口管理

**难点**：
- 窗口置顶可能影响其他应用
- 透明窗口性能
- 多显示器支持

**解决方案**：
- 提供窗口置顶开关
- 使用硬件加速渲染
- 记住窗口位置，支持多显示器

### 3.3 SQLite 并发访问

**难点**：
- 多线程访问数据库
- 写入冲突
- 数据一致性

**解决方案**：
- 使用 SQLite 的 WAL 模式
- 使用连接池
- 适当的锁机制
- 定期备份数据库

### 3.4 虚拟滚动实现

**难点**：
- PyQt5 的虚拟滚动实现较复杂
- 动态数据加载
- 滚动流畅度

**解决方案**：
- 参考 Qt 官方示例
- 使用 `QAbstractItemModel`
- 预加载前后若干项
- 优化渲染性能

---

## 四、测试计划

### 4.1 单元测试

每个新功能都需要编写单元测试：

- 音频可视化测试
- 歌词编辑器测试
- 数据库操作测试
- 虚拟滚动测试

### 4.2 性能测试

**测试场景**：
- 10,000 首歌曲的音乐库
- 快速滚动列表
- 频繁切歌
- 长时间播放

**测试指标**：
- 内存占用
- CPU 占用
- 响应时间
- 启动时间

### 4.3 兼容性测试

**测试环境**：
- Windows 10
- Windows 11
- 不同 DPI 设置
- 不同音频格式

---

## 五、风险管理

### 5.1 时间风险

**风险**：功能开发时间超出预期

**应对**：
- 分阶段交付，优先核心功能
- 简化非核心功能
- 灵活调整计划

### 5.2 技术风险

**风险**：某些功能实现难度大

**应对**：
- 提前调研技术方案
- 参考开源项目实现
- 必要时简化功能

### 5.3 性能风险

**风险**：优化效果不达预期

**应对**：
- 持续性能监控
- 分阶段优化
- 提供性能选项

---

## 六、里程碑与交付物

### 里程碑 1：音频体验增强完成（第4周）

**交付物**：
- 音频可视化效果
- 淡入淡出效果
- 音量平滑过渡

### 里程碑 2：歌词功能增强完成（第8周）

**交付物**：
- 歌词时间轴微调
- 简易歌词编辑器
- 桌面歌词功能

### 里程碑 3：界面与交互优化完成（第12周）

**交付物**：
- 迷你播放器模式
- 拖拽操作增强
- 添加到下一首播放
- 歌单排序功能

### 里程碑 4：性能优化完成（第20周）

**交付物**：
- 虚拟滚动实现
- 懒加载机制
- 后台预加载
- 内存优化
- 启动优化
- SQLite 数据库

---

## 七、后续维护计划

### 7.1 持续优化

- 根据使用反馈持续优化
- 定期性能测试
- 修复发现的问题

### 7.2 功能扩展

- 根据实际需求添加新功能
- 探索更多音频处理功能
- 优化用户体验

---

## 附录

### A. 技术参考

- [Qt Documentation - Model/View Programming](https://doc.qt.io/qt-5/model-view-programming.html)
- [numpy.fft Reference](https://numpy.org/doc/stable/reference/routines.fft.html)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

### B. 开发工具

- **性能分析**：`cProfile`, `memory_profiler`
- **数据库工具**：DB Browser for SQLite
- **UI 设计**：Qt Designer

### C. 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-04-14 | 初始版本，完成实施计划框架 |

---

**文档结束**

*本计划将根据实际开发进度持续更新。*
