#!/bin/sh

echo "Removing *.egg-info"
rm -rf *.egg-info

echo "Removing virtual env"
rm -rf .venv*
rm -rf venv*

echo "Removing tox virtualenv"
rm -rf .tox*

echo "Removing coverage files"
rm -rf .coverage
rm -rf cover

echo "Removig all log files"
rm *.log

echo "Removing all .pyc files"
find . -name \*.pyc -delete

echo "Removing all .DS_Store files"
find . -name \.DS_Store -delete
