test:
	./manage.py test --settings=notesserver.settings.test --with-coverage --cover-package=notesserver,notesapi \
		--exclude-dir=notesserver/settings --cover-inclusive --cover-branches

run:
	./manage.py runserver 0.0.0.0:8042

shell:
	./manage.py shell

