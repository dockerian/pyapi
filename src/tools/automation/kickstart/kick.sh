#!/bin/sh

# Configuration
SCRIPT_DIR="$(dirname $0)"
VENV_DIR="${SCRIPT_DIR}/venv_kickstart"
KICKSTART_SRC="${VENV_DIR}/kickstart_src"

# If there's a virtual environment that we can use, update the path
if [ ! -d "${VENV_DIR}" ]; then
    echo "Please install kickstart first."
    exit 1
fi

# Run with a specialized python path
export PATH="${VENV_DIR}/bin:${PATH}"
export PYTHONPATH="$(find ${VENV_DIR} -name site-packages):${KICKSTART_SRC}/src"

# Call kickstart
python ${KICKSTART_SRC}/src/kickstart/main.py $@
