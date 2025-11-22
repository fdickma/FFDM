#!/bin/sh
python -m venv env
env/bin/pip install yfinance sqlalchemy matplotlib scipy chardet flask flask_sqlalchemy flask_login bcrypt psutil
# env/bin/pip install --upgrade *
env/bin/pip freeze > requirements.txt
env/bin/pip install --upgrade -r requirements.txt
