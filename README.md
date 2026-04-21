# RHYME - 个人音乐库管理系统

一个完整的个人音乐库解决方案，包含 **Web 端**、**桌面端** 和 **后端 API**。

## 项目概述

RHYME 是一个支持在线搜索、本地管理、多端访问的音乐库系统：
- **Web 端**：Vue 3 + Element Plus，支持浏览器在线听歌
- **桌面端**：PyQt5 本地播放器，支持离线播放和高级功能
- **后端 API**：FastAPI + SQLite，提供音乐管理和流媒体服务

## 项目结构

```
RHYME/
├── backend/                    # 后端 API 服务
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic 模型
│   │   └── utils/             # 工具函数
│   ├── data/                  # 数据存储（gitignore）
│   ├── requirements.txt
│   └── .env.example
├── frontend-web/              # Web 前端
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 通用组件
│   │   ├── layouts/          # 布局组件
│   │   └── stores/           # Pinia 状态
│   ├── package.json
│   └── vite.config.js
├── frontend/                  # 桌面端
│   ├── apps/desktop/windows/ # Windows 桌面端
│   ├── core/                 # 核心业务逻辑
│   └── requirements.txt
├── deploy/                    # 部署配置
│   ├── nginx.conf
│   ├── rhyme-backend.service
│   └── deploy.sh
└── README.md
```

## 功能特性

### 核心功能
- **统一搜索**：优先搜索本地音乐库，同时展示在线搜索结果
- **一键导入**：在线歌曲可一键下载并导入音乐库
- **流媒体播放**：支持 HTTP Range 请求的流式播放
- **歌词同步**：自动匹配本地歌词或在线获取

### Web 端
- 响应式设计，支持桌面和移动端
- 深色主题，现代化 UI
- 在线搜索和播放
- 管理员后台（音乐上传、标签管理）

### 桌面端
- 本地音乐文件扫描
- 多歌单管理
- 歌词显示和编辑
- 离线 ASR 歌词识别
- 系统托盘支持

## 快速开始

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. 启动 Web 前端

```bash
cd frontend-web
npm install
npm run dev
```

访问 http://localhost:5173

### 3. 启动桌面端

```bash
# Windows
start.bat

# 或直接运行
python frontend/app.py
```

## 生产部署

### 服务器要求
- Ubuntu 20.04+
- Python 3.10+
- Node.js 18+
- Nginx

### 一键部署

```bash
# 1. 克隆项目
git clone <YOUR_REPO_URL> /opt/rhyme
cd /opt/rhyme

# 2. 运行部署脚本
chmod +x deploy/deploy.sh
./deploy/deploy.sh

# 3. 配置环境变量
vim backend/.env

# 4. 重启服务
systemctl restart rhyme-backend
systemctl restart nginx
```

### 访问地址
- 生产环境：https://rhyme.rhyme17.top
- API 文档：https://rhyme.rhyme17.top/docs

## 环境变量

### 后端配置 (backend/.env)

```env
RHYME_SECRET_KEY=your-random-secret-key
RHYME_CORS_ORIGINS=https://rhyme.rhyme17.top
RHYME_GITHUB_CLIENT_ID=your-github-client-id
RHYME_GITHUB_CLIENT_SECRET=your-github-client-secret
RHYME_GITHUB_REDIRECT_URI=https://rhyme.rhyme17.top/api/auth/github/callback
RHYME_ADMIN_GITHUB_IDS=12345678
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/musics/` | GET | 获取音乐列表 |
| `/api/musics/` | POST | 上传音乐（管理员） |
| `/api/musics/{id}/stream` | GET | 流式播放音乐 |
| `/api/online/unified-search` | GET | 统一搜索（本地+在线） |
| `/api/online/import` | POST | 导入在线歌曲 |
| `/api/auth/login` | POST | 用户名密码登录 |
| `/api/auth/github/authorize` | GET | GitHub OAuth |

完整 API 文档：http://localhost:8000/docs

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI, SQLAlchemy, SQLite |
| Web 前端 | Vue 3, Element Plus, Pinia, Vite |
| 桌面端 | Python, PyQt5, pydub, mutagen |
| 部署 | Nginx, systemd, Let's Encrypt |

## 开发指南

### 代码规范
- Python: PEP 8, 使用 ruff 检查
- JavaScript: ESLint, Prettier
- 提交信息: Conventional Commits

### 运行测试

```bash
# 后端测试
cd backend
pytest

# 桌面端测试
cd frontend
pytest -q
```

### 代码检查

```bash
# Python
ruff check backend frontend

# JavaScript
cd frontend-web
npm run lint
```

## 许可证

MIT License
