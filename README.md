# gap-trading


## deployment on linode ubuntu

```
apt-get upgrade
timedatectl list-timezones
timedatectl set-timezone America/Los_Angeles
git clone https://github.com/hackingthemarkets/gap-trading.git
cp sample_config.py config.py
apt-install python-pip3
cd gap-trading
pip3 install -r requirements.txt
```
