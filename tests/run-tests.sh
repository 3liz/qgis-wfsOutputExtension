#!/bin/bash

set -e

# Add /.local to path
export PATH=$PATH:/.local/bin

echo "Installing required packages..."
pip3 install -q -U --prefer-binary --user -r requirements.txt

# Disable qDebug stuff that bloats test outputs
export QT_LOGGING_RULES="*.debug=false;*.warning=false"

# Disable python hooks/overrides
export QGIS_DISABLE_MESSAGE_HOOKS=1
export QGIS_NO_OVERRIDE_IMPORT=1

echo -n "" > /src/tests/qgis_server.log
export QGIS_SERVER_LOG_FILE="/src/tests/qgis_server.log"
export QGIS_SERVER_LOG_LEVEL=0

pytest -v --qgis-plugins=/src $@
