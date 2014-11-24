test: clean
	./manage.py test --settings=notesserver.settings.test --with-coverage --cover-package=notesserver,notesapi \
		--exclude-dir=notesserver/settings --cover-inclusive --cover-branches \
		--cover-html --cover-html-dir=coverage/html/ \
		--cover-xml --cover-xml-file=coverage/coverage.xml

run:
	./manage.py runserver 0.0.0.0:8042

shell:
	./manage.py shell

clean:
	coverage erase

