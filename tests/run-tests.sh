#!/bin/bash

set -e

VENV_PATH=/.local/venv

PIP_INSTALL="$VENV_PATH/bin/pip install -U"

echo "Creating virtualenv"
python3 -m venv --system-site-packages $VENV_PATH

echo "Installing required packages..."
$PIP_INSTALL -q pip setuptools wheel
$PIP_INSTALL -q --prefer-binary -r requirements.txt

# Disable qDebug stuff that bloats test outputs
export QT_LOGGING_RULES="*.debug=false;*.warning=false"

# Disable python hooks/overrides
export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1
export QGIS_SERVER_LOG_LEVEL=0

exec  $VENV_PATH/bin/pytest -v --qgis-plugins=/src $@

