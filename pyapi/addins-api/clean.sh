#!/bin/sh

echo "Removing *.egg-info"
rm -rf *.egg-info

echo "Removing all .pyc files"
find . -name \*.pyc -delete

echo "Removing tox virtualenv"
rm -rf .tox*

echo "Removing virtual env"
rm -rf .venv*

echo "Removing coverage files"
rm -rf cover

echo "Removig all log files"
rm *.log
