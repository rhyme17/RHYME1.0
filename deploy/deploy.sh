#!/bin/bash
set -e

SERVER_DIR="/opt/rhyme"
DOMAIN="rhyme.rhyme17.top"
BACKEND_PORT="8001"

echo "========================================="
echo "  RHYME Music Server - 部署脚本"
echo "========================================="

echo "[1/7] 安装系统依赖..."
apt update && apt install -y python3 python3-venv python3-pip nginx git curl wget

echo "[2/7] 部署项目代码..."
if [ -d "$SERVER_DIR" ]; then
    cd $SERVER_DIR && git pull || true
else
    git clone https://github.com/rhyme17/RHYME1.0.git $SERVER_DIR
fi

echo "[3/7] 配置后端..."
cd $SERVER_DIR/backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i "s/change-this-to-a-random-secret-key/$SECRET/" .env
    echo "已生成 .env 文件，请编辑配置 GitHub OAuth 等参数"
fi

mkdir -p data/music data/covers

echo "[4/7] 构建 Web 前端..."
cd $SERVER_DIR/frontend-web
npm install
npm run build

echo "[5/7] 配置 systemd 服务..."
cp $SERVER_DIR/deploy/rhyme-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable rhyme-backend
systemctl restart rhyme-backend

echo "[6/7] 配置 Nginx..."
cp $SERVER_DIR/deploy/nginx.conf /etc/nginx/sites-available/rhyme
rm -f /etc/nginx/sites-enabled/rhyme
ln -s /etc/nginx/sites-available/rhyme /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "[7/7] 配置 SSL 证书..."
if [ ! -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
    apt install -y certbot python3-certbot-nginx
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
fi

echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo "  访问地址: https://$DOMAIN"
echo "  后端状态: systemctl status rhyme-backend"
echo "  后端端口: $BACKEND_PORT"
echo "  Nginx日志: tail -f /var/log/nginx/error.log"
echo "========================================="
