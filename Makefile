PACKAGES = notesserver notesapi
.PHONY: requirements check_keywords

validate: test.requirements test

pytest: test-start-services test test-stop-services

test: clean
	python -Wd -m pytest

test-start-services:
	docker compose -f notesserver/docker-compose.test.yml --project-name=edxnotesapi_test up -d --remove-orphans

test-stop-services:
	docker compose -f notesserver/docker-compose.test.yml --project-name=edxnotesapi_test stop

pii_check: test.requirements pii_clean
	DJANGO_SETTINGS_MODULE=notesserver.settings.test code_annotations django_find_annotations --config_file .pii_annotations.yml \
		--lint --report --coverage

check_keywords: ## Scan the Django models in all installed apps in this project for restricted field names
	DJANGO_SETTINGS_MODULE=notesserver.settings.test python manage.py check_reserved_keywords --override_file db_keyword_overrides.yml

run:
	./manage.py runserver 0.0.0.0:8120

shell:
	./manage.py shell

clean:
	coverage erase

pii_clean:
	rm -rf pii_report
	mkdir -p pii_report

quality: pycodestyle pylint

pycodestyle:
	pycodestyle --config=.pycodestyle $(PACKAGES)

pylint:
	DJANGO_SETTINGS_MODULE=notesserver.settings.test pylint $(PACKAGES)

diff-coverage:
	diff-cover build/coverage/coverage.xml --html-report build/coverage/diff_cover.html

diff-quality:
	diff-quality --violations=pep8 --html-report build/coverage/diff_quality_pep8.html
	diff-quality --violations=pylint --html-report build/coverage/diff_quality_pylint.html

coverage: diff-coverage diff-quality

create-index:
	python manage.py search_index --rebuild -f

migrate:
	python manage.py migrate --noinput

static:  # provide the static target for devstack's tooling.
	@echo "The notes service does not need staticfiles to be compiled. Skipping."

requirements:
	pip install -q -r requirements/base.txt --exists-action=w

test.requirements:
	pip install -q -r requirements/test.txt --exists-action=w

develop: requirements test.requirements

piptools: ## install pinned version of pip-compile and pip-sync
	pip install -r requirements/pip-tools.txt

prepare-common-constraints:
	curl -s https://raw.githubusercontent.com/openedx/edx-lint/master/edx_lint/files/common_constraints.txt \
	    | grep -iv '^[dD]jango' > requirements/common_constraints.txt

compile-requirements: export CUSTOM_COMPILE_COMMAND=make upgrade
compile-requirements: prepare-common-constraints
compile-requirements: piptools ## Re-compile *.in requirements to *.txt (without upgrading)
	# Make sure to compile files after any other files they include!
	pip-compile ${COMPILE_OPTS} --rebuild --allow-unsafe -o requirements/pip.txt requirements/pip.in
	pip-compile ${COMPILE_OPTS} -o requirements/pip-tools.txt requirements/pip-tools.in
	pip install -qr requirements/pip.txt
	pip install -qr requirements/pip-tools.txt
	pip-compile ${COMPILE_OPTS} --allow-unsafe -o requirements/base.txt requirements/base.in
	pip-compile ${COMPILE_OPTS} --allow-unsafe -o requirements/test.txt requirements/test.in
	pip-compile ${COMPILE_OPTS} --allow-unsafe -o requirements/ci.txt requirements/ci.in
	pip-compile ${COMPILE_OPTS} --allow-unsafe -o requirements/quality.txt requirements/quality.in
	# Let tox control the Django version for tests
	grep -e "^django==" requirements/base.txt > requirements/django.txt
	sed '/^[dD]jango==/d' requirements/test.txt > requirements/test.tmp
	mv requirements/test.tmp requirements/test.txt

upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	$(MAKE) compile-requirements COMPILE_OPTS="--upgrade"
