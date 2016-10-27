.PHONY: clean dev-setup serve test

clean:
	find . -name '.DS_Store' -type f -delete
	find . -name \*.pyc -type f -delete -o -name \*.log -delete
	find . -name .coverage -type f | xargs rm -rf
	find . -name cover -type d | xargs rm -rf
	rm -rf *.egg-info
	rm -rf .tox*
	rm -rf .venv*

serve:
	pserve development.ini --reload

dev-setup:
	python setup.py develop --user
	pip install -r requirements-test.txt --user

test:
	nosetests
