#!/usr/bin/env bash
################################################################
# Create SQL script from MySQL Workbench schema file (.mwb)
#
# Prerequisite:
#   - MySQL Workbench 6.0+ with command line tools
#       must be installed and closed while running this script
#   - Environment variables:
#       PROJECT (optional, default value "catelog")
#       DB_PATH (optional, default "../database")
#
################################################################
set -e
script_file="${BASH_SOURCE[0]##*/}"
script_base="$( cd "$( echo "${BASH_SOURCE[0]%/*}/.." )" && pwd )"
script_path="${script_base}/tools/${script_file}"

PROJECT=${PROJECT:-catelog}
DB_PATH=${DB_PATH:-${script_base}/database}

schema_file="${PROJECT}.mwb"
outsql_file="${PROJECT}.sql"


# main process
function main() {
  shopt -s nocasematch
  if [[ "$@" =~ (--help|/help|-\?|/\?) ]]; then
    usage; return
  fi

  local OS_="$(getOS)"
  local cmd="$(which mysql-workbench)"
  local mwb="${1:-${DB_PATH}/${schema_file}}"
  local out="${2:-${DB_PATH}/${outsql_file}}"

  if [[ "${cmd}" == "" ]]; then
    if [[ "${OS_}" == "darwin" ]]; then
      cmd="/Applications/MySQLWorkbench.app/Contents/MacOS/MySQLWorkbench"
    else
      cmd="/usr/bin/mysql-workbench"
    fi
  fi
  if [[ ! -e "${cmd}" ]]; then
    log_error "Cannot find app: ${cmd}" -1
  elif [[ ! -e "${mwb}" ]]; then
    log_error "Cannot find mwb: ${mwb}" -2
  fi

  local pse="$(ps -ef| grep -i -e [s]ql-*workbench -e [p]pid)"
  local pid="$(ps -ef| grep -i -e [s]ql-*workbench|awk '{print $2}')"

  echo ""
  if [[ "${pid}" != "" ]]; then
    echo "${pse}"
    log_trace "MySQLWorkbench is running. Please quit the app and retry." WARNING
    return 9
  fi

  echo `date +"%Y-%m-%d %H:%M:%S"` "Creating ${outsql_file} ..."
  rm -rf "${out}"

  create_sql "${mwb}" "${out}"  # creating sql script from mwb

  if [[ ! -e "${out}" ]]; then
    log_error "Failed to generate sql script."
  fi
  echo "-----------------------------------------------------------------------"
  echo "Generated SQL script: ${out}"

}

# read MySQLWorkbench model file (*.mwb) from $1 to create sql script ($2)
function create_sql() {
  mwb="${1:-${DB_PATH}/${schema_file}}"
  out="${2:-${DB_PATH}/${outsql_file}}"
  run="
import os
import grt
from grt.modules import DbMySQLFE
catalog = grt.root.wb.doc.physicalModels[0].catalog
# for options, see DbMySQLSQLExport::set_option in db_mysql_sql_export.cpp
#     GenerateAttachedScripts
#     GenerateCreateIndex
#     GenerateDocumentProperties
#     GenerateDrops
#     GenerateInserts
#     GenerateSchemaDrops
#     GenerateUse
#     GenerateWarnings
#     NoFKForInserts
#     NoUsersJustPrivileges
#     NoViewPlaceholders
#     OmitSchemata
#     RoutinesAreSelected
#     SkipFKIndexes
#     SkipForeignKeys
#     TablesAreSelected
#     TriggersAfterInserts
#     TriggersAreSelected
#     UsersAreSelected
#     ViewsAreSelected
# https://github.com/mysql/mysql-workbench
DbMySQLFE.generateSQLCreateStatements(catalog, catalog.version, {
    'GenerateCreateIndex': 1,
    'GenerateDocumentProperties': 1,
    'GenerateDrops': 1,
    'GenerateInserts': 1,
    'GenerateSchemaDrops': 1,
    'OmitSchemata': 0,
    'GenerateUse': 1
})
DbMySQLFE.createScriptForCatalogObjects('${out}', catalog, {})
  "
  "${cmd}" --model "${mwb}" --run-python "${run}" \
    --log-level debug3 --log-to-stderr --quit-when-done --verbose
  echo ""
}

# getOS function sets OS environment variable in runtime
function getOS() {
  # Detect the platform (similar to $OSTYPE)
  UNAME="$(uname)"
  case ${UNAME} in
    'Darwin')
      OS="darwin"
      ;;
    'FreeBSD')
      OS="bsd"
      alias ls='ls -G'
      ;;
    'Linux')
      OS="linux"
      alias ls='ls --color=auto'
      ;;
    'SunOS')
      OS="solaris"
      ;;
    'WindowsNT')
      OS="windows"
      ;;
    'AIX') ;;
    *) ;;
  esac

  if [[ "${OS}" != "" ]]; then echo ${OS} && return; fi

  case "${OSTYPE}" in
    bsd*)     OS="bsd" ;;
    darwin*)  OS="darwin" ;;
    linux*)   OS="linux" ;;
    solaris*) OS="soloris" ;;
    *)        OS="" ;;
  esac
  echo "${OS}"
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

# usage() func: show help
function usage() {
  local headers="0"
  echo ""
  echo "USAGE: ${script_file} --help"
  echo ""
  echo "$(cat ${script_file} | grep -e '^#   \$[1-9] - ')"
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


[[ $0 != "${BASH_SOURCE}" ]] || main "$@"
