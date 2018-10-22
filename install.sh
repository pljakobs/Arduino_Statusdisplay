#if [ -f /dev/spi-1 ]; then
    echo "### installing dependencies"
    apt install python-setuptools python-psutil python-pil python-pip python-netifaces
    pip install Adafruit-SSD1306 Adafruit-BBIO Adafruit-GPIO netifaces configparser
    echo "### copying files"
    cp status.py /usr/bin/
    cp status.service /etc/systemd/system
    cp status.cfg /etc/
    echo "### reloading systemd"
    systemctl daemon-reload
    echo "### enabling service"
    systemctl enable status
    echo "### starting service"
    systemctl start status
#else
#    echo "please use raspi-config to enable spi and try again"
#fi
