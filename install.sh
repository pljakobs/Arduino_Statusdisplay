echo "### installing dependencies"
apt install python-setuptools python-psutil python-pil
pip install Adafruit-SSD1306 Adafruit-BBIO
echo "### copying files"
cp status.py /usr/bin/
cp status.service /etc/systemd/system
echo "### reloading systemd"
systemctl daemon-reload
echo "### starting service"
sysetmctl start status
