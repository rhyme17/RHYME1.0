# RHYME Music Server - 开发者手册

## 项目概述

RHYME 是一个现代化的音乐播放器系统，支持 Web 端和桌面端，提供在线搜索、音乐库管理、歌单同步等功能。

## 技术栈

- **后端**: FastAPI + Python 3.12
- **前端**: Vue 3 + Element Plus + Vite
- **数据库**: SQLite
- **部署**: Nginx + systemd

## 目录结构

```
RHYME/
├── backend/              # 后端服务
│   ├── app/             # FastAPI 应用
│   ├── data/            # 数据目录（音乐、封面、数据库）
│   └── venv/            # Python 虚拟环境
├── frontend-web/        # Web 前端
│   ├── src/             # 源代码
│   ├── dist/            # 构建产物
│   └── node_modules/    # Node.js 依赖
├── deploy/              # 部署配置
│   ├── nginx.conf       # Nginx 配置
│   ├── rhyme-backend.service  # systemd 服务
│   └── deploy_full.sh   # 一键部署脚本
└── docs/                # 文档
```

## 开发环境

### 后端开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端开发

```bash
# 进入前端目录
cd frontend-web

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 部署流程

### 前置准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3.12 python3.12-venv python3-pip nginx git nodejs npm
```

### 创建专用用户

```bash
# 创建系统用户（不允许登录）
sudo useradd -r -s /usr/sbin/nologin rhyme
sudo groupadd rhyme 2>/dev/null || true
sudo usermod -aG rhyme rhyme
```

### 克隆项目

```bash
# 克隆项目到 /opt/rhyme
sudo git clone --depth=1 https://github.com/rhyme17/RHYME1.0.git /opt/rhyme

# 设置目录权限
sudo chown -R admin:admin /opt/rhyme
chmod -R 755 /opt/rhyme
```

### 配置后端

```bash
cd /opt/rhyme/backend

# 创建环境变量文件
cat > .env << 'EOF'
RHYME_SECRET_KEY=your-secret-key-here
RHYME_CORS_ORIGINS=http://rhyme.rhyme17.top,http://localhost:5173
RHYME_LOG_LEVEL=INFO
RHYME_LOG_TO_FILE=true
EOF

# 创建数据目录
mkdir -p data/music data/covers data/logs

# 安装 Python 依赖
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### 构建前端

```bash
cd /opt/rhyme/frontend-web

# 安装 Node.js 依赖
npm install

# 构建前端
npm run build
```

### 配置 Nginx

```bash
# 创建 Nginx 配置
cat > /etc/nginx/sites-available/rhyme << 'EOF'
server {
    listen 80;
    server_name rhyme.rhyme17.top;

    client_max_body_size 60M;

    root /opt/rhyme/frontend-web/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript image/svg+xml;
}
EOF

# 启用站点
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/rhyme /etc/nginx/sites-enabled/rhyme
```

### 配置 systemd 服务

```bash
# 创建 systemd 服务文件
cat > /etc/systemd/system/rhyme-backend.service << 'EOF'
[Unit]
Description=RHYME Music Server
After=network.target

[Service]
Type=simple
User=rhyme
Group=rhyme
WorkingDirectory=/opt/rhyme/backend
EnvironmentFile=/opt/rhyme/backend/.env
ExecStart=/opt/rhyme/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 重新加载 systemd
sudo systemctl daemon-reload
```

### 设置权限

```bash
# 设置数据目录权限
sudo chown -R rhyme:rhyme /opt/rhyme/backend/data
sudo chmod -R 770 /opt/rhyme/backend/data

# 设置前端目录权限
sudo chmod -R 755 /opt/rhyme/frontend-web/dist

# 将 www-data 添加到 rhyme 组
sudo usermod -aG rhyme www-data
```

### 启动服务

```bash
# 启动后端服务
sudo systemctl enable rhyme-backend
sudo systemctl start rhyme-backend

# 启动 Nginx
sudo systemctl restart nginx

# 开放防火墙
sudo ufw allow 80/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable
```

### 验证部署

```bash
# 检查后端状态
sudo systemctl status rhyme-backend

# 检查 Nginx 状态
sudo systemctl status nginx

# 测试 API
curl http://localhost:8000/

# 测试前端
curl http://rhyme.rhyme17.top/
```

## 服务管理

### 后端服务

```bash
# 启动
sudo systemctl start rhyme-backend

# 停止
sudo systemctl stop rhyme-backend

# 重启
sudo systemctl restart rhyme-backend

# 查看状态
sudo systemctl status rhyme-backend

# 查看日志
sudo journalctl -u rhyme-backend -f
```

### Nginx

```bash
# 启动
sudo systemctl start nginx

# 停止
sudo systemctl stop nginx

# 重启
sudo systemctl restart nginx

# 查看日志
tail -f /var/log/nginx/error.log
```

## 数据库管理

### 查看数据库

```bash
# 使用 sqlite3 连接数据库
sqlite3 /opt/rhyme/backend/data/database.sqlite

# 查看所有表
.tables

# 查看音乐列表
SELECT * FROM musics LIMIT 10;

# 退出
.exit
```

## 备份与恢复

### 备份

```bash
# 备份数据库
cp /opt/rhyme/backend/data/database.sqlite /backup/rhyme_db_$(date +%Y%m%d).sqlite

# 备份音乐文件
tar -czf /backup/rhyme_music_$(date +%Y%m%d).tar.gz /opt/rhyme/backend/data/music
```

### 恢复

```bash
# 恢复数据库
cp /backup/rhyme_db_YYYYMMDD.sqlite /opt/rhyme/backend/data/database.sqlite

# 恢复音乐文件
tar -xzf /backup/rhyme_music_YYYYMMDD.tar.gz -C /opt/rhyme/backend/data/
```

## 常见问题

### 500 错误

```bash
# 查看后端日志
sudo journalctl -u rhyme-backend -f
```

### 权限错误

```bash
# 修复数据目录权限
sudo chown -R rhyme:rhyme /opt/rhyme/backend/data
sudo chmod -R 770 /opt/rhyme/backend/data
```

### 无法访问网站

```bash
# 检查防火墙
sudo ufw status

# 检查端口占用
sudo lsof -i :80
```

### 前端样式异常

```bash
# 重新构建前端
cd /opt/rhyme/frontend-web
npm run build
sudo systemctl restart nginx
```

## API 文档

部署成功后，API 文档可在以下地址访问：
- Swagger UI: http://rhyme.rhyme17.top/docs
- ReDoc: http://rhyme.rhyme17.top/redoc

## 开发规范

### 代码风格

- Python: 遵循 PEP 8 规范
- JavaScript/TypeScript: 使用 Prettier 格式化
- Vue: 使用 Composition API

### 提交规范

```
feat: 新增功能
fix: 修复 bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加测试
chore: 构建/工具相关
```

## 许可证

MIT License