# Makefile of the datection package containing test launchers

test-html:
	if [ -d "test/logs/cover" ]; then rm -r test/logs/cover; fi
	nosetests --with-coverage --cover-html --cover-html-dir=test/logs/cover \
		--cover-package=datection --verbose
test-shell:
	nosetests --with-coverage --cover-package=datection --verbose
all:
	nosetests --with-coverage --cover-package=datection --verbose
