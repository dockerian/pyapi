#!/bin/bash

# Configuration
SCRIPT_DIR="$(dirname $0)"
VENV_DIR="${SCRIPT_DIR}/venv_kickstart"
KICKSTART_SRC="${VENV_DIR}/kickstart_src"

# Function that exits with argument $1 as the return code and all further
# arguments being treated as an optional message
die () {
  retcode=1

  if [ $# -gt 1 ]; then
    # Bind the return code
    retcode=$2
    shift
  fi

  # Is there a message too?
  if [ $# -gt 0 ]; then
    echo $@
  fi

  exit $retcode
}

if [ -z $(which virtualenv 2> /dev/null) ]; then
  die "Python virtualenv is required to install Kickstart"
fi

if [ -d "${VENV_DIR}" ]; then
  echo "Kickstart virtualenv already exists, skipping venv setup."
else
  virtualenv "${VENV_DIR}"
fi

# Upgrade PIP just in case
${VENV_DIR}/bin/pip install --upgrade pip

# Check to see if there's a kickstart source dir already there, if so, blast it
if [ -d "${KICKSTART_SRC}" ]; then
    rm -rf "${KICKSTART_SRC}"
fi

# Clone kickstart (you're going to need to be able to see the repo)
git clone -q git@github.com:hpcloud/helion-kickstart.git "${KICKSTART_SRC}"

if [ $? -ne 0 ]; then
  # If the above clone failed it may have done so because this user doesn't
  # have their ssh key added. Let's use HTTPS this time.
  git clone https://github.com/hpcloud/helion-kickstart "${KICKSTART_SRC}"
fi

if [ $? -eq 0 ]; then
  # Check out the current version tag
  pushd "${KICKSTART_SRC}"
  git checkout -q "${KICKSTART_VERSION}"
  popd

  # Install all the deps
  ${VENV_DIR}/bin/pip install -r "${KICKSTART_SRC}/tools/install-requires.txt"
fi
