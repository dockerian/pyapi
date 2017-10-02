#!/bin/sh

echo "Removing all .DS_Store files"
find . -name \.DS_Store -delete

echo "Removing all .pyc files"
find . -name \*.pyc -delete

echo "Removing *.egg-info"
rm -rf *.egg-info

echo "Removing tox virtualenv"
rm -rf .tox*

echo "Removing virtual env"
rm -rf .venv*
rm -rf venv*

echo "Removing coverage files"
rm -rf cover

echo "Removig all log files"
rm *.log
