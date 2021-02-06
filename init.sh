#!/bin/sh
pip3 install -r requirements.txt && \
virualenv venv-flask && \
. venv-flask/bin/activate && \
pip3 install vwo-python-sdk && \
pip3 install python-dotenv && \
pip3 install flask