#!/bin/bash
set -e

# ============================================================
# RHYME Music Server - 完整部署脚本
# 版本: 1.0.0
# 适用: Ubuntu 20.04+
# ============================================================

DOMAIN="rhyme.rhyme17.top"
PROJECT_DIR="/opt/rhyme"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend-web"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[*]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# ============================================================
# 步骤1: 环境检查
# ============================================================
log "步骤1/8: 环境检查"

# 检查是否以 root 或 sudo 运行
if [[ $EUID -ne 0 ]]; then
    error "请使用 sudo 或 root 用户运行此脚本"
fi

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log "Python 版本: $PYTHON_VERSION"

# 检查 Node.js 版本
NODE_VERSION=$(node --version)
log "Node.js 版本: $NODE_VERSION"

# 检查域名解析
log "检查域名解析..."
IP=$(dig +short $DOMAIN)
if [[ -z "$IP" ]]; then
    error "域名 $DOMAIN 未解析到任何 IP"
fi
log "域名 $DOMAIN 解析到: $IP"

# ============================================================
# 步骤2: 创建专用用户
# ============================================================
log "步骤2/8: 创建专用系统用户"

if id "rhyme" &>/dev/null; then
    warn "用户 rhyme 已存在"
else
    log "创建系统用户 rhyme..."
    useradd -r -s /usr/sbin/nologin rhyme
    log "用户 rhyme 创建成功"
fi

# ============================================================
# 步骤3: 克隆项目
# ============================================================
log "步骤3/8: 克隆项目代码"

if [[ -d "$PROJECT_DIR" ]]; then
    if [[ -d "$PROJECT_DIR/.git" ]]; then
        warn "项目目录已存在，将进行更新..."
        cd "$PROJECT_DIR"
        git pull origin main
    else
        warn "项目目录存在但不是 git 仓库，重新克隆..."
        sudo rm -rf "$PROJECT_DIR"
        git clone --depth=1 https://github.com/rhyme17/RHYME1.0.git "$PROJECT_DIR"
    fi
else
    log "克隆项目到 $PROJECT_DIR..."
    git clone --depth=1 https://github.com/rhyme17/RHYME1.0.git "$PROJECT_DIR"
fi

# ============================================================
# 步骤4: 配置后端
# ============================================================
log "步骤4/8: 配置后端服务"

cd "$BACKEND_DIR"

# 创建环境变量文件
log "创建环境变量文件..."
cat > .env << 'EOF'
RHYME_SECRET_KEY=abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
RHYME_CORS_ORIGINS=http://rhyme.rhyme17.top,http://localhost:5173
RHYME_LOG_LEVEL=INFO
RHYME_LOG_TO_FILE=true
EOF
log "环境变量文件创建成功"

# 创建数据目录
log "创建数据目录..."
mkdir -p data/music data/covers data/logs

# 安装依赖
log "安装 Python 依赖..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
fi
venv/bin/pip install -r requirements.txt
log "依赖安装成功"

# ============================================================
# 步骤5: 构建前端
# ============================================================
log "步骤5/8: 构建前端项目"

cd "$FRONTEND_DIR"

log "安装 Node.js 依赖..."
npm install --production

log "构建前端项目..."
npm run build
log "前端构建成功"

# ============================================================
# 步骤6: 配置 Nginx
# ============================================================
log "步骤6/8: 配置 Nginx"

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
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript image/svg+xml;
    gzip_min_length 256;
}
EOF

# 启用站点
rm -f /etc/nginx/sites-enabled/default
if [[ ! -L /etc/nginx/sites-enabled/rhyme ]]; then
    ln -sf /etc/nginx/sites-available/rhyme /etc/nginx/sites-enabled/rhyme
fi

log "Nginx 配置完成"

# ============================================================
# 步骤7: 配置 systemd 服务
# ============================================================
log "步骤7/8: 配置 systemd 服务"

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

log "systemd 服务配置完成"

# ============================================================
# 步骤8: 设置权限并启动服务
# ============================================================
log "步骤8/8: 设置权限并启动服务"

# 设置目录权限
log "设置目录权限..."
chown -R rhyme:rhyme "$PROJECT_DIR"
chmod -R 750 "$PROJECT_DIR"
chmod -R 770 "$BACKEND_DIR/data"

# 启动服务
log "启动后端服务..."
systemctl daemon-reload
systemctl enable rhyme-backend
systemctl restart rhyme-backend

log "启动 Nginx..."
systemctl restart nginx

# 开放防火墙
log "配置防火墙..."
ufw allow 80/tcp
ufw allow 22/tcp
ufw --force enable

# ============================================================
# 验证部署
# ============================================================
log "验证部署..."

sleep 3

# 检查后端状态
if systemctl is-active --quiet rhyme-backend; then
    log "✅ 后端服务运行正常"
else
    error "❌ 后端服务启动失败"
fi

# 检查 Nginx 状态
if systemctl is-active --quiet nginx; then
    log "✅ Nginx 运行正常"
else
    error "❌ Nginx 启动失败"
fi

# 测试 API
API_RESPONSE=$(curl -s http://localhost:8000/)
if echo "$API_RESPONSE" | grep -q "RHYME Music Server"; then
    log "✅ API 服务正常"
else
    error "❌ API 服务异常: $API_RESPONSE"
fi

# ============================================================
# 完成
# ============================================================
echo ""
echo "============================================================"
echo "                    部署完成！"
echo "============================================================"
echo ""
echo "服务地址:"
echo "  首页:    http://$DOMAIN"
echo "  API文档: http://$DOMAIN/docs"
echo "  管理后台: http://$DOMAIN/admin"
echo ""
echo "服务管理:"
echo "  启动后端: systemctl start rhyme-backend"
echo "  停止后端: systemctl stop rhyme-backend"
echo "  重启后端: systemctl restart rhyme-backend"
echo "  查看日志: journalctl -u rhyme-backend -f"
echo ""
echo "注意事项:"
echo "  1. 首次访问请先注册账号"
echo "  2. 在线搜索功能需要联网"
echo "  3. 可在管理后台上传音乐"
echo "============================================================"