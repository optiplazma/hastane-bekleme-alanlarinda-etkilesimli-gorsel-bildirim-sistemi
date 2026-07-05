#!/bin/bash

# NOT: Aşağıdaki "SUNUCU_IP_ADRESI" ifadesini, Flask sunucusunun
# çalıştığı makinenin yerel ağ IP adresiyle değiştirin (örn: 192.168.1.50)

export DISPLAY=:0

until xdpyinfo &>/dev/null; do
    sleep 1
done

pkill chromium 2>/dev/null
rm -f /home/pi/.chromium-kiosk/Default/SingletonLock

sleep 3

xset s off
xset -dpms
xset s noblank

# Google Translate'i kalıcı olarak kapat
mkdir -p /home/pi/.chromium-kiosk/Default
cat > /home/pi/.chromium-kiosk/Default/Preferences << 'EOF'
{
  "translate": {"enabled": false},
  "translate_blocked_languages": ["tr"],
  "translate_whitelists": {}
}
EOF

# Sunucuya bağlanana kadar bekle
COUNTER=0
while [ $COUNTER -lt 30 ]; do
    if ping -c 1 -W 1 SUNUCU_IP_ADRESI &> /dev/null; then
        break
    fi
    sleep 2
    COUNTER=$((COUNTER+1))
done

# Beyaz ekran için sonsuz döngü - chromium çökerse yeniden başlat
while true; do
    chromium \
    --kiosk \
    --user-data-dir=/home/pi/.chromium-kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --no-first-run \
    --disable-notifications \
    --disable-features=TranslateUI,Translate \
    --disable-translate \
    --disable-sync \
    --password-store=basic \
    --no-default-browser-check \
    --disable-popup-blocking \
    --disable-extensions \
    --disable-plugins \
    --lang=tr \
    --accept-lang=tr-TR,tr \
    --overscroll-history-navigation=0 \
    http://SUNUCU_IP_ADRESI:5000
    
    # Chromium kapanırsa 5 saniye bekle, tekrar başlat
    sleep 5
done
