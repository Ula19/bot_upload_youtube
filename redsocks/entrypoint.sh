#!/bin/sh
# Прозрачный прокси для Cobalt — весь TCP трафик идёт через резидентный IP

PROXY_IP="${PROXY_IP:-127.0.0.1}"
PROXY_PORT="${PROXY_PORT:-1080}"

# генерируем конфиг redsocks
cat > /tmp/redsocks.conf <<EOF
base {
    log_debug = off;
    log_info = on;
    daemon = off;
    redirector = iptables;
}

redsocks {
    local_ip = 0.0.0.0;
    local_port = 12345;
    ip = ${PROXY_IP};
    port = ${PROXY_PORT};
    type = http-connect;
}
EOF

echo "redsocks: proxy=${PROXY_IP}:${PROXY_PORT}"

# iptables — перенаправляем весь TCP (кроме локального) через redsocks
iptables -t nat -N REDSOCKS || true
iptables -t nat -F REDSOCKS

# не проксируем локальный трафик и приватные сети
iptables -t nat -A REDSOCKS -d 0.0.0.0/8 -j RETURN
iptables -t nat -A REDSOCKS -d 10.0.0.0/8 -j RETURN
iptables -t nat -A REDSOCKS -d 127.0.0.0/8 -j RETURN
iptables -t nat -A REDSOCKS -d 172.16.0.0/12 -j RETURN
iptables -t nat -A REDSOCKS -d 192.168.0.0/16 -j RETURN

# весь остальной TCP → redsocks
iptables -t nat -A REDSOCKS -p tcp -j REDIRECT --to-ports 12345

# применяем к исходящему трафику
iptables -t nat -A OUTPUT -p tcp -j REDSOCKS

echo "iptables rules set"

exec redsocks -c /tmp/redsocks.conf
