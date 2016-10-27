.PHONY: clean dev-setup serve test

clean:
	find . -name '.DS_Store' -type f -delete
	find . -name *.pyc -type f -delete
	cd src/addins-api && make clean
	cd src/catalog-api && make clean
	cd demo && make clean

dev-setup-addins:
	cd src/addins-api && make dev-setup

dev-setup-catalog:
	cd src/catalog-api && make dev-setup

dev-setup: dev-setup-catalog dev-setup-addins


serve-addins:
	cd src/addins-api && make serve

serve-catalog:
	cd src/catalog-api && make serve


test-addins:
	cd src/addins-api && make test

test-catalog:
	cd src/catalog-api && make test

test: test-addins test-catalog
