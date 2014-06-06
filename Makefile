all:

test:
	@python setup.py test

flake8:
	@flake8 pyiconfinder tests setup.py

publish:
	@python setup.py sdist upload

clean:
	@rm -rf build dist *.egg*

.PHONY: test flake8 publish clean
