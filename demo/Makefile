.PHONY: clean dev-setup serve test

clean:
	find . -name '.DS_Store' -type f -delete
	find . -name .coverage -type f | xargs rm -rf
	find . -name cover -type d | xargs rm -rf
	find . -name *.egg-info -type d | xargs rm -rf
	find . -name *.pyc -type f -delete
	find . -name .venv* -type f -delete
	find . -name .tox* -type f -delete

serve:
	pserve development.ini --reload

dev-setup:
	python setup.py develop --user
	pip install -r requirements-test.txt --user

test:
	nosetests
