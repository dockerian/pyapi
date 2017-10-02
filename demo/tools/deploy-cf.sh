#!/usr/bin/env bash
##############################################################################
# Deploy AWS CloudFormation stack
#
# Command line arguments:
#   $1 - main stack name of cloudformation
#   $2 - deployment alias/tag, e.g.: dev (default), prod, tes
#
# Other options
#   $@ =~ '--test' to print command only (same as DRY_RUN_ONLY=1)
#
# Expecting the runtime host is assigned with proper AWS Role;
# or from ~/.aws or the following environment variables (see check_depends)
#   AWS_ACCESS_KEY_ID
#   AWS_SECRET_ACCESS_KEY
#   AWS_DEFAULT_REGION (optional)
#   PREFIX_NAME (optional, default 'CyberInt')
#   STACK_NAME (optional, default 'Reaper')
#   BUILD_ENV (optional, default to $2 or 'dev')
# and git workspace having ".git" folder with optional
#   GIT_REVISION_TAG (or using current commit sha)
#
##############################################################################
set -eo pipefail
script_file="${BASH_SOURCE[0]##*/}"
script_base="$( cd "$( echo "${BASH_SOURCE[0]%/*}/.." )" && pwd )"
script_path="${script_base}/tools/${script_file}"
builds_path="${script_base}/builds"
config_path="${script_base}/cloudformation"
cfmain_file="cloudformation.json"
prefix_name="${PREFIX_NAME:-CyberInt}"
stacks_list="[]"

# step 0: predefine environment variables
BUILD_ENV="${BUILD_ENV:-test}"
CHECK_STACK="${CHECK_STACK:-false}"
CHECK_STACK_ONLY="${CHECK_STACK_ONLY:-false}"
STACK_NAME="${STACK_NAME:-Sockeye}"
S3_BUCKET="${S3_BUCKET:-cyber-intel}"
S3_PREFIX="${S3_PREFIX:-sockeye}"
S3_PREFIX_BUILDS="${S3_PREFIX_BUILDS:-${S3_PREFIX}/builds}"
DEPLOY_TAG="${GIT_REVISION_TAG:-None}"
DRY_RUN_ONLY="${DRY_RUN_ONLY:-true}"
USE_S3="${USE_S3:-false}"

# step 2: main entrypoint to start with parsing command line arguments
function main() {
  ARG_STACK="${1:-${STACK_NAME}}"
  ARG_ENV="${2:-${BUILD_ENV}}"
  ARG_PARAM="cloudformation_config_${ARG_ENV}.json"
  pwd
  BUILD_ENV="${ARG_ENV}"
  CF_STACK_NAME="${prefix_name}-${ARG_STACK}-${ARG_ENV}"
  USE_ARG3="false"
  USE_ARG4="false"
  USE_PARAMETERS_FILE="true"  # default to use parameter file until not found
  HAS_ERROR="false"

  shopt -s nocasematch
  for arg in $@ ; do
    if [[ "${arg}" =~ (help|/h|-\?|\/\?) ]] || [[ "${arg}" == "-h" ]]; then
      usage; return
    fi
  done
  if [[ "$@" =~ (--help|/help|-\?|/\?) ]]; then
    usage; return
  fi

  check_cmdline_args $@
  check_depends

  # resolving BUILD_NAME value as partial s3 prefix
  check_git_commit_sha_or_tag

  set +u
  if [[ "$1" == "list" ]] || [[ "$@" =~ (--list) ]] ; then
    do_list_stacks; return
  fi
  set -u

  CONFIGURATION="${3:-${config_path}/${cfmain_file}}"
  if [[ "${CHECK_STACK_ONLY}" != "true" ]]; then
    S3_PREFIX_CFT="${S3_PREFIX_BUILDS}/cloudformation"
    PARAMETERFILE="${4:-${config_path}/${ARG_PARAM}}"

    check_cloudformation_parameter_file
    check_deploy_args $@

    do_deployment "${CF_STACK_NAME}"
  fi

  do_summary
}

# abspath(): output a relative path to absolute path
function abspath() {
  set +u
  local thePath
  if [[ ! "$1" =~ ^/ ]]; then thePath="$PWD/$1"; else thePath="$1"; fi
  echo "$thePath"|(
  IFS=/
  read -a parr
  declare -a outp
  for i in "${parr[@]}";do
    case "$i" in
    ''|.) continue ;;
    ..)
      len=${#outp[@]}
      if ((len!=0));then unset outp[$((len-1))]; else continue; fi
      ;;
    *)
      len=${#outp[@]}
      outp[$len]="$i"
      ;;
    esac
  done
  echo /"${outp[*]}"
  )
  set -u
}

# check stack status
#   - args: $1: cloudformation stack name
#           $2: a string flag to turn on stdout, e.g. 1|enable|on|true|yes
#   --- return: set CF_STACK_STATUS
function check_cf_stack_status() {
  local cf_name="${1:-${CF_STACK_NAME}}"
  local on_echo="${2:-false}"
  local aws_cli="aws cloudformation"
  local aws_cmd="${aws_cli} describe-stacks"
  local cmd_arg="--stack-name ${cf_name}"
  local cmd_out="$(${aws_cmd} ${cmd_arg} 2>/dev/null)"
  local s_query='.Stacks[]|select(.StackName=="'${cf_name}'")|.StackStatus'
  local cf_stat="$(echo ${cmd_out}|jq -M -r ${s_query})"
  if [[ "${cf_stat}" != "" ]] && [[ "${on_echo}" =~ (1|enable|on|true|yes) ]]; then
    echo "......................................................................."
    echo "${cmd_out}" | jq -M -r '.Stacks[0]'
    echo "......................................................................."
    log_debug "Status == ${cf_stat}"
    echo ""
  fi

  CF_STACK_STATUS="${cf_stat}"
}

function check_cf_stack_status_complete() {
  set +u
  local cf_name="${1:-${CF_STACK_NAME}}"
  local timeout="${2:-499}"
  local elapsed="$(date +%s)"
  local seconds="10"
  echo ""
  echo `date +'%Y-%m-%d %H:%M:%S'` "Checking complete status for stack: ${cf_name}"
  set -u

  until [[ $timeout -lt 0 ]]; do
    check_cf_stack_status "${cf_name}"  # no stdout

    if [[ "${CF_STACK_STATUS}" == "" ]]; then
      log_trace "Cannot get status for stack '${cf_name}'."
      break
    elif [[ "${CF_STACK_STATUS}" =~ (ROLLBACK) ]]; then
        log_trace "The stack '${cf_name}' failed as in '${CF_STACK_STATUS}'."
        break
    elif [[ "${CF_STACK_STATUS}" =~ (.+_COMPLETE$) ]]; then
      log_trace "The stack '${cf_name}' status: '${CF_STACK_STATUS}'."
      break
    fi
    # Note: since there is about 1~2 seconds lag in checking stack status
    #       actual timeout would be ${timeout} + 1 * ${timeout}/${seconds}
    local msg="sleeping ${seconds} [${CF_STACK_STATUS}] timeout: ${timeout}"
    echo `date +'%Y-%m-%d %H:%M:%S'` "- ${msg} ..."
    timeout=$(( timeout - ${seconds} ))
    sleep $(( $seconds - 1 ))
  done
  elapsed=$(( $(date +%s) - ${elapsed} ))
  echo ""
  echo "`date +'%Y-%m-%d %H:%M:%S'` Elapsed: ${elapsed} [timeout: ${timeout}]"
  log_trace "Stack Status: ${CF_STACK_STATUS}"
  echo ""
}

# check cloudformation parameter file
function check_cloudformation_parameter_file() {
  if [[ "${PARAMETERFILE}" =~ (^s3://([^\/]+)/(.+)$) ]]; then return; fi

  local src="${script_base}/cloudformation"

  if [[ "${BUILD_ENV}" == "prod" ]]; then
    src="${src}/config_prod.json"
  elif [[ "${BUILD_ENV}" == "qa" ]]; then
    src="${src}/config_qa.json"
  else
    src="${src}/config_test.json"
  fi

  log_trace "Using parameter file ${src} for environment [${BUILD_ENV}]"

  PARAMETERFILE="${src}"
}

# check command line arguments
function check_cmdline_args() {
  set +u
  if [[ "${USE_S3}" =~ (1|enable|on|true|yes) ]]; then
    if [[ "$3" != "" ]]; then USE_ARG3="true"; fi
    if [[ "$4" != "" ]]; then USE_ARG4="true"; fi
    USE_S3="true"
  fi
  if [[ "${DRY_RUN_ONLY}" =~ (1|enable|on|true|yes) ]]; then
    DRY_RUN_ONLY="true"
  fi
  if [[ "${CHECK_STACK_ONLY}" =~ (1|enable|on|true|yes) ]]; then
    CHECK_STACK_ONLY="true"
    CHECK_STACK="true"
  fi
  if [[ "${CHECK_STACK}" =~ (1|enable|on|true|yes) ]]; then
    CHECK_STACK="true"
  fi
  set -u
}

# check_depends(): verifies preset environment variables exist
function check_depends() {
  local conf_aws=""
  local list_cmd="aws cloudformation list-stacks"
  local tool_set="awk aws jq sleep"
  set +u
  echo "......................................................................."
  echo "Checking dependencies: ${tool_set}"
  for tool in ${tool_set}; do
    if ! [[ -x "$(which ${tool})" ]]; then
      log_error "Cannot find command '${tool}'"
    fi
  done

  if [[ "${DRY_RUN_ONLY}" == "true" ]]; then return; fi

  echo ""
  echo "Checking list of aws cloudformation list-stacks ..."
  if [[ "${conf_aws}" == "" ]]; then
    conf_aws=$(${list_cmd} || true)
  fi

  if [[ "${conf_aws}" == "" ]]; then
    log_error 'Cannot access to `'"${list_cmd}"'`.'
  fi

  stacks_list="${conf_aws}"
}

# check_deploy_args(): verifies command line arguments
function check_deploy_args() {
  shopt -s nocasematch

  CONFIGURATION="$(abspath "${CONFIGURATION}")"
  PARAMETERFILE="$(abspath "${PARAMETERFILE}")"

  if [[ ! "${PARAMETERFILE}" ]]; then
    log_trace "Cannot find deployment parameter file: '${PARAMETERFILE}'" WARN
    USE_PARAMETERS_FILE="false"
  fi

  if [[ ! "${CONFIGURATION}" ]]; then
    log_trace "Cannot find deployment configguration file: '${CONFIGURATION}'" WARN
  fi

  set +u
  echo "......................................................................."
  echo "CONFIGURATION = ${CONFIGURATION}"
  echo "   PARAMETERS = ${PARAMETERFILE}"
  echo "......................................................................."
  set -u

}

# check_git_commit_sha_or_tag(): get git commit sha or revision tag
function check_git_commit_sha_or_tag() {
  echo ""
  echo "--- Checking git commit sha or revision tag ---"
  cd -P "${script_base}" && pwd
  # see https://git-scm.com/docs/pretty-formats
  local commit_sha="$(git rev-parse --short HEAD)"
  local commit_tag="$(git describe --tags --abbrev 2>/dev/null)"
  local commit_dts="$(TZ=UTC git log --oneline --no-walk --pretty=format:'%cI' 2>/dev/null)"
  local prefix_ymd="$(TZ=UTC date +'%Y%m%d-%H%M%S')"

  if [[ "${commit_dts}" != "" ]]; then
    prefix_ymd="${commit_dts:0:4}${commit_dts:5:2}${commit_dts:8:2}"
    log_trace "Set yyyymmdd prefix [${prefix_ymd}] from committer's date [${commit_dts}]"
  else
    TZ=UTC git log --oneline --no-walk --pretty=format:'%h %aE %aI [%cI] %s'
    log_error "Cannot get git committer's date."
  fi

  if [[ "${DEPLOY_TAG}" != "None" ]]; then
    if [[ "${DEPLOY_TAG}" != "${commit_tag}" ]]; then
      git describe --tags --abbrev
      log_error "GIT_REVISION_TAG [${DEPLOY_TAG}] does not match '${commit_tag}' for current revision [${commit_sha}]"
    fi
    # NOTE: The s3 partial prefix must match to where set in 'publish-builds.sh'
    BUILD_NAME="${prefix_ymd}_${commit_tag}"
    log_trace "Using revision tag and commit sha for s3 build prefix: ${BUILD_NAME}"
  elif [[ "${commit_sha}" != "" ]]; then
    BUILD_NAME="${prefix_ymd}_${commit_sha}"
    log_trace "Using commit sha for s3 build prefix: ${BUILD_NAME}"
  else
    log_error "Cannot get GIT_REVISION_TAG or git commit sha."
  fi

  S3_PREFIX_BUILDS="${S3_PREFIX_BUILDS}/${BUILD_NAME}"
  log_trace "Set s3 build prefix: ${S3_PREFIX_BUILDS}"
}

# check_response(): check function configuration changes
#   - $1: phase of the process, e.g. "create", "publish"
function check_response() {
  set +u
  echo ""
  echo "Checking error responses from aws cloudformation cli ..."
  echo "......................................................................."
  if [[ "${CF_RESPONSE_ERROR}" == "" ]]; then
    log_trace "No cloud formation errors."
  elif echo "${CF_RESPONSE_ERROR}" | grep -q "No updates are to be performed."; then
    log_trace "No changes to the cloud formation template detected."
  else
    echo "${CF_RESPONSE_ERROR}"
    echo "......................................................................."
    log_fatal "Cloud formation error!"
  fi

  echo ""
  set -u
}

# check_return_code(): checks exit code from last command
function check_return_code() {
  local return_code="${1:-0}"
  local action_name="${2:-AWS CLI}"

  if [[ "${return_code}" != "0" ]]; then
    log_fatal "${action_name} [code: ${return_code}]" ${return_code}
  else
    echo "Success: ${action_name}"
    echo ""
  fi
}

# check_s3_file(): check if s3:// file exists
function check_s3_file() {
  if [[ "$1" == "" ]]; then return; fi
  aws s3 ls $1
}

# do_deployment(): deploy cloudformation stack
function do_deployment() {
  local cf_name="${1:-${CF_STACK_NAME}}"
  set +u
  echo ""
  echo "Checking description for stack: ${cf_name}"
  set -u

  check_cf_stack_status "${cf_name}" enable_stdout

  if [[ "${CF_STACK_STATUS}" != "" ]]; then
    if [[ ! "${CF_STACK_STATUS}" =~ (.+_COMPLETE$) ]]; then
      log_error "The stack '${cf_name}' is in status '${CF_STACK_STATUS}'."
    else
      log_trace "Updating stack [${cf_name}] ..."
      do_deploy_stack update "${cf_name}"
      do_update_services
    fi
  else
    log_trace "Creating stack [${cf_name}] ..."
    do_deploy_stack create "${cf_name}"
  fi
}

# do_deploy_stack(): deploy a new cloudformation stack
function do_deploy_stack() {
  if [[ "$1" != "create" ]] && [[ "$1" != "update" ]]; then
    log_error "Invalid command for 'aws cloudformation' cli: $1-stack"
  fi

  local arg_cmd="${1:-update}"
  local cf_name="${2:-${CF_STACK_NAME}}"
  local aws_cli="aws cloudformation"
  local aws_cmd="${aws_cli} ${arg_cmd}-stack"
  local aws_arg="--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM"
  local cmd_arg="--stack-name ${cf_name} ${aws_arg}"
  local cmd_opt="--template-body file://${CONFIGURATION}"
  local aws_url="https://${S3_BUCKET}.s3.amazonaws.com"

  cmd_opt="${cmd_opt} --parameters file://${PARAMETERFILE}"
  echo "......................................................................."
  cat ${PARAMETERFILE}

  local cmdline="${aws_cmd} ${cmd_arg} ${cmd_opt}"
  local cmdname="$([[ "$1" == "create" ]] && echo "Creating" || echo "Updating")"
  set +u
  echo "......................................................................."
  echo "${cmdname} cloudformation stack ..."
  echo -e "  - name: ${cf_name}"
  echo -e "  - exec:\n\n${cmdline}"
  echo ""
  set -u

  if [[ "${DRY_RUN_ONLY}" == "true" ]]; then
    echo "-----------------------------------------------------------------------"
    echo "- NOTE: Use above command line in deployment process."
    return
  fi

  set +e
  CF_RESPONSE_ERROR=$(${cmdline} 2>&1 > /dev/null)
  set -e

  check_response
  check_cf_stack_status_complete
}

# do_list_stacks(): display deployed stacks
function do_list_stacks() {
  local aws_cli="aws cloudformation"
  local aws_cmd="${aws_cli} list-stacks"
  local filters="[ .StackSummaries[]|select(.StackStatus|tostring|contains(\"DELETE\")|not) ]"
  local cmd_out="echo ${stacks_list}"
  set +u
  echo ""
  echo "Getting list of cloudformation stacks"
  echo "......................................................................."
  echo "${stacks_list}" | jq -M -r "${filters}"
  echo ""
  set -u
}

# print out summary info
function do_summary() {
  local action="${1:-deployed stack}"
  echo ""
  if [[ "${DRY_RUN_ONLY}" == "true" ]]; then
    echo "- DONE"
    return
  fi
  echo "-----------------------------------------------------------------------"
  echo "- DONE: ${action} [${CF_STACK_NAME}]"
  echo ""
}

function do_update_services() {
  get_service_arns

  local cmd="aws ecs update-service --force-new-deployment --cluster ${ECS_CLUSTERS} --service"

  for service in ${ECS_SERVICES}; do
    echo "Redeploying ${service}..."
    local response=$(${cmd} "${service}" 2>&1 > /dev/null)
    if [[ ${response} != "" ]]; then
      log_trace "Error when updating service ${service}: ${response}" WARNING
    fi
  done
}

function get_cluster_arn() {
  local cf_name="${1:-${CF_STACK_NAME}}"
  echo ""
  echo "Getting Sockeye cluster arn from stack: ${cf_name}"
  echo "......................................................................."

  local aws_cli="aws cloudformation"
  local aws_cmd="${aws_cli} describe-stack-resources"
  local cmd_arg="--stack-name ${cf_name}"
  local cmd_out="$(${aws_cmd} ${cmd_arg} 2>/dev/null)"
  local stquery=".StackResources[]|select(.ResourceType|tostring"
  local cluster_query="${stquery}|contains(\"ECS::Cluster\")).PhysicalResourceId"
  ECS_CLUSTERS="$(echo ${cmd_out}|jq -M -r ${cluster_query} 2>/dev/null)"

  if [[ "${ECS_CLUSTERS}" == "" ]]; then
    echo "${cmd_out}"
    echo "......................................................................."
    log_trace "Cannot find any ECS Clusters associated with stack: ${cf_name}" WARNING
  fi
}

function get_service_arns() {
  local cf_name="${1:-${CF_STACK_NAME}}"
  echo ""
  echo "Getting Sockeye service names from stack: ${cf_name}"
  echo "......................................................................."

  local aws_cli="aws cloudformation"
  local aws_cmd="${aws_cli} describe-stack-resources"
  local cmd_arg="--stack-name ${cf_name}"
  local cmd_out="$(${aws_cmd} ${cmd_arg} 2>/dev/null)"
  local stquery=".StackResources[]|select(.ResourceType|tostring"
  local cluster_query="${stquery}|contains(\"ECS::Cluster\")).PhysicalResourceId"
  local service_query="${stquery}|contains(\"ECS::Service\")).PhysicalResourceId"

  ECS_CLUSTERS="$(echo ${cmd_out}|jq -M -r ${cluster_query} 2>/dev/null)"
  ECS_SERVICES="$(echo ${cmd_out}|jq -M -r ${service_query} 2>/dev/null)"
  # readarray -t y <<<"$ECS_SERVICES"

  echo "ECS clusters: ${ECS_CLUSTERS}"
  if [[ "${ECS_CLUSTERS}" == "" ]]; then
    echo "${cmd_out}"
    echo "......................................................................."
    log_trace "Cannot find any ECS Clusters associated with stack: ${cf_name}" WARNING
  fi

  echo "-----------------------------------------------------------------------"
  echo "${ECS_SERVICES}"
  echo ""
  if [[ "${ECS_SERVICES}" == "" ]]; then
    echo "${cmd_out}"
    echo "......................................................................."
    log_trace "Cannot find any services associated with stack: ${cf_name}" WARNING
  fi
}

# log_debug() func: print message as debug warning
function log_debug() {
  log_trace "$1" "${2:-DEBUG}"
}

# log_error() func: exits with non-zero code on error unless $2 specified
function log_error() {
  log_trace "$1" "ERROR" $2
}

# log_fatal() func: exits with non-zero code on fatal failure unless $2 specified
function log_fatal() {
  log_trace "$1" "FATAL" $2
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

# usage() func: show help
function usage() {
  local headers="0"
  echo ""
  echo "USAGE: ${script_file} {PROJECT_NAME} {ENVIRONMENT}"
  echo ""
  # echo "$(cat ${script_path} | grep -e '^#   \$[1-9] - ')"
  while IFS='' read -r line || [[ -n "${line}" ]]; do
    if [[ "${headers}" == "0" ]] && [[ "${line}" =~ (^#[#=-\\*]{59}) ]]; then
      headers="1"
      echo "${line}"
    elif [[ "${headers}" == "1" ]] && [[ "${line}" =~ (^#[#=-\\*]{59}) ]]; then
      headers="0"
      echo "${line}"
    elif [[ "${headers}" == "1" ]]; then
      echo "${line}"
    fi
  done < "${script_path}"
}


set +u
[[ "$1=None" == "=None" ]] && usage && exit
set -u

ARGS=""
# step 1: pre-processing optional arguments
for arg in $@; do
  if [[ "${arg}" =~ "--s3" ]]; then
    USE_S3="true"
  elif [[ "${arg}" =~ "--test" ]]; then
    DRY_RUN_ONLY="true"
  elif [[ "${arg}" =~ "--stage" ]]; then
    if [[ "${arg}" =~ "--stage-only" ]]; then
      CHECK_STACK_ONLY="true"
    fi
    CHECK_STACK="true"
  else
    ARGS="${ARGS} "${arg}""
  fi
done

# main entrance, preventing from source
[[ $0 != "${BASH_SOURCE}" ]] || main ${ARGS}
