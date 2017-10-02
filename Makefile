.PHONY: clean dev-setup serve test

clean:
	find . -name '.DS_Store' -type f -delete
	find . -name *.pyc -type f -delete
	cd pyapi/addins-api && make clean
	cd pyapi/catalog-api && make clean
	cd demo && make clean

dev-setup-addins:
	cd pyapi/addins-api && make dev-setup

dev-setup-catalog:
	cd pyapi/catalog-api && make dev-setup

dev-setup: dev-setup-catalog dev-setup-addins


serve-addins:
	cd pyapi/addins-api && make serve

serve-catalog:
	cd pyapi/catalog-api && make serve


test-addins:
	cd pyapi/addins-api && make test

test-catalog:
	cd pyapi/catalog-api && make test

test: test-addins test-catalog
