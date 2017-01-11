.PHONY: all build clean clean-all cmd cover dev-setup docker list parser processor publish setup show test unittest pytest nosetest functest upload venv

PROJECT := foobar

BUILDS_DIR := builds
BUILDS_ALL := $(BUILDS_DIR)/$(PROJECT)-lambdas.zip
BUILD_PACKAGE := $(PROJECT)
COVERAGE_REPORT := htmlcov/index.html
SYSTOOLS := find rm pip tee virtualenv xargs zip
PYVENV_NAME ?= .venv

DOCKER_USER := dockerian
DOCKER_IMAG := $(PROJECT)
DOCKER_TAGS := $(DOCKER_USER)/$(DOCKER_IMAG)

# TODO: Test the Makefile macros
# to represent "ifdef VAR1 || VAR2", use
#		ifneq ($(call ifdef_any,VAR1 VAR2),) # ifneq ($(VAR1)$(VAR2),)
# to represent "ifdef VAR1 && VAR2", use
#		ifeq ($(call ifdef_none,VAR1 VAR2),) # ifneq ($(and $(VAR1),$(VAR2)),)
ifdef_any := $(filter-out undefined,$(foreach v,$(1),$(origin $(v))))
ifdef_none := $(filter undefined,$(foreach v,$(1),$(origin $(v))))


all: clean-all dev-setup test

list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs

clean clean-cache:
	@echo
	@echo "--- Removing pyc and log files"
	find . -name '.DS_Store' -type f -delete
	find . -name \*.pyc -type f -delete -o -name \*.log -delete
	rm -Rf .cache
	rm -Rf .vscode
	rm -Rf $(PROJECT)/.cache
	rm -Rf $(PROJECT)/tests/__pycache__
	rm -rf *_parquet
	@echo
	@echo "--- Removing coverage files"
	find . -name .coverage -type f | xargs rm -rf
	find . -name cover -type d | xargs rm -rf
	rm -rf .coveragerc
	rm -rf htmlcov
	rm -rf $(PROJECT)/cover
	@echo
	@echo "--- Removing *.egg-info"
	rm -Rf *.egg-info
	rm -Rf $(PROJECT)/*.egg-info
	@echo
	@echo "--- Removing tox virtualenv"
	rm -Rf $(PROJECT)/.tox*
	@echo
	@echo "--- Removing build"
	rm -rf $(PROJECT)_build.tee
	rm -rf $(BUILDS_DIR)
	@echo
	@echo "- DONE: $@"

clean-all: clean-cache
ifeq ("$(wildcard /.dockerenv)","")
	# not in a docker container
	@echo
	@echo "--- Removing virtualenv"
	rm -rf .venv
	@echo "--- Removing docker image $(DOCKER_TAGS)"
	docker rm -f $(shell docker ps -a|grep $(DOCKER_IMAG)|awk '{print $1}') 2>/dev/null || true
	docker rmi -f $(shell docker images -a|grep $(DOCKER_TAGS) 2>&1|awk '{print $1}') 2>/dev/null || true
	rm -rf docker_build.tee
endif
	@echo
	find . -name '*.tee' -type f -delete
	@echo "--- Uninstalling $(PROJECT)"
	pip uninstall $(PROJECT) -y 2>/dev/null; true
	rm -Rf database/*.bak
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	@echo "--- Cleaning up pip list in $(VIRTUAL_ENV) ..."
	pip freeze | grep -v "^-e" | xargs pip uninstall -y || true
else
	@echo "--- Removing virtual env"
	rm -Rf $(PROJECT)/.venv*
endif
	@echo
	@echo "- DONE: $@"

check-tools:
	@echo
	@echo "--- Checking for presence of required tools: $(SYSTOOLS)"
	$(foreach tool,$(SYSTOOLS),\
	$(if $(shell which $(tool)),$(echo "boo"),\
	$(error "ERROR: Cannot find '$(tool)' in system $$PATH")))
	@echo
	@echo "- DONE: $@"

# build targets
$(PROJECT)_build.tee:
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	tools/build.sh all | tee $(PROJECT)_build.tee
	@echo "- DONE: $@"
else
	VENV_NAME=$(PYVENV_NAME) tools/make_venv.sh "$@"
endif

build: test-all build-lambdas
	@echo ""
	@echo "- DONE: $@"
	@echo ""

build-lambdas: $(PROJECT)_build.tee check-tools
	@echo ""
	@echo "- DIST: $(BUILDS_ALL)"
	@echo ""
	@echo "- DONE: $@"
	@echo ""


# deploy targets
deploy-dev: deploy-lambda-dev
	@echo
	@echo "- DONE: $@"

deploy-lambda-dev: build-lambdas
	@echo
	@echo "--- Deploying lambda [dev] ---"
	tools/deploy.sh myLambda dev
	@echo "- DONE: $@"
	@echo

deploy-lambda-prod: build
	@echo
	@echo "--- Deploying lambda [prod] ---"
	tools/deploy.sh myLambda prod
	@echo "- DONE: $@"
	@echo

deploy-lambda-test: build
	@echo
	@echo "--- Deploying parser [test] ---"
	tools/deploy.sh myLambda test
	@echo "- DONE: $@"
	@echo

deploy-test: deploy-lambda-test
	@echo
	@echo "- DONE: $@"


# docker targets
docker cmd: docker_build.tee
ifeq ("$(wildcard /.dockerenv)","")
	@echo ""
	@echo `date +%Y-%m-%d:%H:%M:%S` "Start bash in container '$(DOCKER_IMAG)'"
	tools/run.sh "$@"
else
	@echo "env in the container:"
	@echo "-----------------------------------------------------------------------"
	@env | sort
	@echo "-----------------------------------------------------------------------"
endif
	@echo "- DONE: $@"

docker_build.tee: Dockerfile
ifeq ("$(wildcard /.dockerenv)","")
	# make in a docker host environment
	@echo ""
	@echo `date +%Y-%m-%d:%H:%M:%S` "Building '$(DOCKER_TAGS)'"
	@echo "-----------------------------------------------------------------------"
	docker build -t $(DOCKER_TAGS) . | tee docker_build.tee
	@echo "-----------------------------------------------------------------------"
	@echo ""
	docker images --all | grep -e 'REPOSITORY' -e '$(DOCKER_TAGS)'
	@echo "................................................................"
	@echo "- DONE: {docker build}"
	@echo ""
endif


# setup and dev-setup targets
$(PYVENV_NAME)/bin/activate: check-tools requirements-test.txt
	@echo
ifeq ("$(VIRTUAL_ENV)", "")
	@echo "Checking python venv: $(PYVENV_NAME)"
	@echo "----------------------------------------------------------------------"
	test -d $(PYVENV_NAME) || virtualenv $(PYVENV_NAME)
	@echo
	@echo "--- Installing required dev packages [$(PYVENV_NAME)] ..."
	$(PYVENV_NAME)/bin/pip install -Ur requirements-test.txt
	@echo
	$(PYVENV_NAME)/bin/pip list
	# touch $(PYVENV_NAME)/bin/activate
else
	@echo "--- Cleaning up pip list in $(VIRTUAL_ENV) ..."
	pip freeze | grep -v "^-e" | xargs pip uninstall -y || true
	@echo
	@echo "--- Setting up $(PROJECT) develop ..."
	python setup.py develop
	@echo
	@echo "--- Installing required dev packages ..."
	# running setup.py in upper level of `$(PROJECT)` folder to register the package
	pip install -r requirements-test.txt
	@echo
	pip list
endif
	@echo
	@echo "- DONE: $@"

dev-setup: $(PYVENV_NAME)/bin/activate
	@echo "----------------------------------------------------------------------"
	@echo "Python environment: $(PYVENV_NAME)"
	@echo "- Activate command: source $(PYVENV_NAME)/bin/activate"
	@echo

setup:
	@echo
	@echo "--- Starting setup ..."
	python setup.py install
	cd $(PROJECT) && pip install -r requirements.txt
	@echo
	@echo "- DONE: $@"

sql:
ifeq ("$(wildcard /.dockerenv)","")
	tools/create-sql.sh
else
	@echo ""
	@echo "Cannot start MySQLWorkbench in the container."
endif
	@echo
	@echo "- DONE: $@"


# test targets
show show-test: $(COVERAGE_REPORT)
ifeq ("$(wildcard /.dockerenv)","")
	@echo "--- Opening $(COVERAGE_REPORT)"
ifeq ($(OS), Windows_NT) # Windows
	start "$(COVERAGE_REPORT)"
else ifeq ($(shell uname),Darwin) # Mac OS
	open "$(COVERAGE_REPORT)"
else
	nohup xdg-open "$(COVERAGE_REPORT)" >/dev/null 2>&1 &
endif
else
	@echo ""
	@echo "Cannot open test coverage in the container."
endif

cover: test clean show-test

unittest: check-tools
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	@echo "--- Starting unittest discover ..."
	@echo
	python -m unittest discover -bcfv
	@echo
	@echo "- DONE: $@"
else
	VENV_NAME=$(PYVENV_NAME) tools/make_venv.sh dev-setup "$@"
endif

nosetest nosetests: check-tools
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	@echo "--- Starting nosetetss ..."
	@echo
	# nosetests must be in the same path with setup.cfg
	nosetests
	@echo "......................................................................"
	@echo "See coverage report: cover/index.html"
	@echo
	@echo "- DONE: $@"
else
	VENV_NAME=$(PYVENV_NAME) tools/make_venv.sh dev-setup "$@"
endif

functest: clean-cache check-tools
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	@echo "--- Starting pytest for functional tests ..."
	@echo
	pytest -c setup.cfg -m "functest" --flakes --pep8 --pylint -s -vv --cov-fail-under=20
	@echo
	@echo "- DONE: $@"
else
	VENV_NAME=$(PYVENV_NAME) tools/make_venv.sh "$@"
endif

test pytest: clean-cache check-tools
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	@echo "--- Starting pytest for unit tests ..."
	@echo
	pytest -c setup.cfg -m "not functest" --flakes --pep8 --pylint -s -vv
	@echo
	@echo "- DONE: $@"
else
	VENV_NAME=$(PYVENV_NAME) tools/make_venv.sh "$@"
endif

test-all-only:
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	# @echo "--- Setup $(PROJECT) develop [$@] ..."
	# python setup.py develop
	# @echo
	pip list
	@echo
	@echo "--- Starting pytest for all tests ..."
	pytest -c setup.cfg --flakes --pep8 --pylint -s -vv
else
	VENV_NAME=$(PYVENV_NAME) tools/make_venv.sh "$@"
endif

test-all: clean-all dev-setup test-all-only
	@echo
	@echo "- DONE: $@"


serve:
	pserve development.ini --reload


dist: build publish
	@echo "- DONE: $@"

publish upload:
	@echo
	tools/publish-builds.sh
	@echo

dvenv:
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	@echo "----------------------------------------------------------------------"
	@echo "Python environment: $(VIRTUAL_ENV)"
	@echo "- Activate command: source $(VIRTUAL_ENV)/bin/activate"
	@echo "- Deactivating cmd: deactivate"
	@echo "----------------------------------------------------------------------"
else
	@echo "Cleaning up python venv: $(PYVENV_NAME)"
	rm -rf $(PYVENV_NAME)
endif
	@echo ""
	@echo "- DONE: $@"
	@echo ""

venv: check-tools
	@echo
ifeq ("$(VIRTUAL_ENV)", "")
	@echo "Preparing for venv: [$(PYVENV_NAME)] ..."
	virtualenv $(PYVENV_NAME)
	@echo "----------------------------------------------------------------------"
	@echo "Python environment: $(PYVENV_NAME)"
	@echo "- Activate command: source $(PYVENV_NAME)/bin/activate"
else
	@echo "----------------------------------------------------------------------"
	@echo "- Activated python venv: $(VIRTUAL_ENV)"
endif
	@echo "----------------------------------------------------------------------"
	@echo "- DONE: $@"
	@echo ""
