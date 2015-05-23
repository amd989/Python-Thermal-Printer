Python-Thermal-Printer
======================

## Setup
If you would like to use github.py, you'll need to install `github3.py` and its dependencies (which, sadly, do not have a Raspbian package). I installed it like this:
```bash
sudo apt-get install libffi-dev
sudo apt-get install python-setuptools
sudo easy_install pip
sudo pip install --pre github3.py
```

You'll also need to install sqlite3 in order to use github.py:
```bash
sudo apt-get install sqlite3
```
