#!/usr/bin/env bash
############################################################
# Run "make ${1:-test}" inside a Docker container
############################################################
set -e
script_file="${BASH_SOURCE[0]##*/}"
script_base="$( cd "$( echo "${BASH_SOURCE[0]%/*}/.." )" && pwd )"
script_path="$( cd "$( echo "${BASH_SOURCE[0]%/*}" )" && pwd )"

# main function
function main() {
  ARGS="$@"
  GITHUB_REPO="pyapi"
  GITHUB_USER="dockerian"
  DOCKER_NAME="pyapi"
  DOCKER_IMAG="${GITHUB_USER}/${DOCKER_NAME}"
  DOCKER_TAGS=$(docker images 2>&1|grep ${DOCKER_IMAG}|awk '{print $1;}')
  # detect if running inside the container
  DOCKER_PROC="$(cat /proc/1/cgroup 2>&1|grep -e "/docker/[0-9a-z]\{64\}"|head -1)"
  SOURCE_PATH="/pyapi/${DOCKER_NAME}"

  cd -P "${script_base}" && pwd

  MAKE_ARGS="${ARGS:-test}"
  # get a list of make targets
  MAKE_LIST="$(make -qp|awk -F':' '/^[a-zA-Z0-9][^$#\/\t=]*:([^=]|$)/ {split($1,A,/ /);for(i in A)print A[i]}'|sort)"
  MAKE_BASH=""
  # checking target(s) from command line
  for target in ${MAKE_ARGS}; do
    t="`echo ${MAKE_LIST}|xargs -n1 echo|grep -e \"^${target}$\"`"
    if [[ ! -n "$t" ]]; then
      echo "Makefile does not have target: ${target}"
      return
    elif [[ -e "/.dockerenv" ]] || [[ "${DOCKER_PROC}" != "" ]]; then
      if [[ "${target}" == "show" ]] || [[ "${target}" == "show-test" ]]; then
        echo "Cannot open test coverage in the container."
        echo "See: cover/index.html"
        return
      elif [[ "${target}" == "sql" ]]; then
        echo "Cannot start MySQLWorkbench in the container."
        return
      fi
    elif [[ "${target}" == "cmd" ]]; then
      MAKE_BASH="; /bin/bash"
    fi
  done

  # run make directly if already inside the container
  if [[ -e "/.dockerenv" ]] || [[ "${DOCKER_PROC}" != "" ]]; then
    make ${MAKE_ARGS}
    return
  fi

  # check existing docker image
  echo -e "\nChecking docker image [${DOCKER_IMAG}] for '${GITHUB_REPO}'"
  if [[ "${DOCKER_TAGS}" != "${DOCKER_IMAG}" ]]; then
    echo -e "\nBuilding docker image [${DOCKER_IMAG}] for '${GITHUB_REPO}'"
    echo "----------------------------------------------------------------------"
    docker build -t ${DOCKER_IMAG} .
    echo "----------------------------------------------------------------------"
  fi

  # configure and start the container
  CMD="docker run -it --rm
    --hostname ${DOCKER_NAME}
    --name ${DOCKER_NAME} --net="host"
    -e DEBUG=${DEBUG}
    -e PROJECT
    -e AWS_ACCESS_KEY_ID
    -e AWS_DEFAULT_REGION
    -e AWS_SECRET_ACCESS_KEY
    -e BUILD_ARTIFACT
    -e BUILDS_DIR
    -e BUILD_NUMBER
    -e LOCAL_USER_ID=${LOCAL_USER_ID:-$(id -u)}
    -e LOCAL_GROUP_ID=${LOCAL_GROUP_ID:-$(id -g)}
    -e USER
    -e MYSQL_HOST
    -e MYSQL_PORT
    -e MYSQL_DATABASE
    -e MYSQL_PASSWORD
    -e MYSQL_USERNAME
    -e S3_BUCKET
    -e S3_PREFIX
    -e VERBOSE
    -v "${PWD}":${SOURCE_PATH}
    ${DOCKER_IMAG}"

  echo -e "\nRunning 'make ${MAKE_ARGS}' in docker container"
  echo "${CMD} bash -c \"make ${MAKE_ARGS} ${MAKE_BASH}\""
  echo "......................................................................"
  if [[ "${MAKE_ARGS}" != "cmd" ]]; then
    ${CMD} bash -c "make ${MAKE_ARGS} ${MAKE_BASH}"
  else
    ${CMD}
  fi
  echo "......................................................................"
}

# check_tools() func verifies prerequsite tools
function check_tools()
{
  local tool_set="${@:-aws}"
  for tool in ${tool_set}; do
    if ! [[ -x "$(which ${tool})" ]]; then
      log_error "Cannot find command '${tool}'"
    fi
  done
}

# log_error() func: exits with non-zero code on error unless $2 specified
function log_error() {
  log_trace "$1" "ERROR" $2
}

# log_trace() func: print message at level of INFO, DEBUG, WARNING, or ERROR
function log_trace() {
  local err_text="${1:-Here}"
  local err_name="${2:-INFO}"
  local err_code="${3:-1}"

  if [[ "${err_name}" == "ERROR" ]] || [[ "${err_name}" == "FATAL" ]]; then
    HAS_ERROR="true"
    echo -e "\n${err_name}: ${err_text}" >&2
    exit ${err_code}
  else
    echo -e "\n${err_name}: ${err_text}"
  fi
}


[[ $0 != "${BASH_SOURCE}" ]] || main "$@"
