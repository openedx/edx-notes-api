PACKAGES = notesserver notesapi
.PHONY: requirements

validate: test.requirements test coverage

test: clean
	./manage.py test --settings=notesserver.settings.test --with-coverage --with-ignore-docstrings \
		--exclude-dir=notesserver/settings --cover-inclusive --cover-branches \
		--cover-html --cover-html-dir=build/coverage/html/ \
		--cover-xml --cover-xml-file=build/coverage/coverage.xml \
		$(foreach package,$(PACKAGES),--cover-package=$(package)) \
		$(PACKAGES)

run:
	./manage.py runserver 0.0.0.0:8042

shell:
	./manage.py shell

clean:
	coverage erase

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
	python manage.py create_index

requirements:
	pip install -q -r requirements/base.txt --exists-action=w

test.requirements: requirements
	pip install -q -r requirements/test.txt --exists-action=w
	@# unicode QUERY_PARAMS are being improperly decoded in test client
	@# remove after https://github.com/tomchristie/django-rest-framework/issues/1891 is fixed
	pip install -q -e git+https://github.com/tymofij/django-rest-framework.git@bugfix/test-unicode-query-params#egg=djangorestframework

develop: test.requirements
