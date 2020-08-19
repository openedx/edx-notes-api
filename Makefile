PACKAGES = notesserver notesapi
.PHONY: requirements

ifdef TOXENV
TOX := tox -- #to isolate each tox environment if TOXENV is defined
endif

include .travis/docker.mk

validate: test.requirements test

test: clean
	$(TOX)python -Wd -m pytest

pii_check: test.requirements pii_clean
	code_annotations django_find_annotations --config_file .pii_annotations.yml \
		--lint --report --coverage

run:
	./manage.py runserver 0.0.0.0:8120

shell:
	./manage.py shell

clean:
	coverage erase

pii_clean:
	rm -rf pii_report
	mkdir -p pii_report

quality:
	pep8 --config=.pep8 $(PACKAGES)
	pylint $(PACKAGES)

diff-coverage:
	diff-cover build/coverage/coverage.xml --html-report build/coverage/diff_cover.html

diff-quality:
	diff-quality --violations=pep8 --html-report build/coverage/diff_quality_pep8.html
	diff-quality --violations=pylint --html-report build/coverage/diff_quality_pylint.html

coverage: diff-coverage diff-quality

create-index:
	python manage.py rebuild_index

migrate:
	python manage.py migrate --noinput

static:  # provide the static target for devstack's tooling.
	@echo "The notes service does not need staticfiles to be compiled. Skipping."

requirements:
	pip install -q -r requirements/base.txt --exists-action=w

test.requirements: requirements
	pip install -q -r requirements/test.txt --exists-action=w

develop: test.requirements

piptools: ## install pinned version of pip-compile and pip-sync
	pip install -r requirements/pip-tools.txt

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: piptools ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	# Make sure to compile files after any other files they include!
	pip-compile --upgrade -o requirements/travis.txt requirements/travis.in
	pip-compile --upgrade -o requirements/pip-tools.txt requirements/pip-tools.in
	pip-compile --upgrade -o requirements/base.txt requirements/base.in
	pip-compile --upgrade -o requirements/test.txt requirements/test.in
	# Let tox control the Django version for tests
	grep -e "^django==" requirements/base.txt > requirements/django.txt
	sed '/^[dD]jango==/d' requirements/test.txt > requirements/test.tmp
	mv requirements/test.tmp requirements/test.txt

docker_build:
	docker build . --target app -t "openedx/edx-notes-api:latest"
	docker build . --target newrelic -t "openedx/edx-notes-api:latest-newrelic"

docker_auth:
	echo "$$DOCKERHUB_PASSWORD" | docker login -u "$$DOCKERHUB_USERNAME" --password-stdin

docker_tag: docker_build
	docker tag "openedx/edx-notes-api:latest" "openedx/edx-notes-api:$$GITHUB_SHA"
	docker tag "openedx/edx-notes-api:latest-newrelic" "openedx/edx-notes-api:$$GITHUB_SHA-newrelic"

docker_push: docker_tag docker_auth ## push to docker hub
	docker push "openedx/edx-notes-api:latest"
	docker push "openedx/edx-notes-api:$$GITHUB_SHA"
	docker push "openedx/edx-notes-api:latest-newrelic"
	docker push "openedx/edx-notes-api:$$GITHUB_SHA-newrelic"
