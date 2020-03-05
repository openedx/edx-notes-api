.PHONY: travis_down travis_start travis_stop travis_test travis_up

travis_up: ## Create containers used to run tests on Travis CI
	docker-compose -f .travis/docker-compose-travis.yml up -d

travis_start: ## Start containers stopped by `travis_stop`
	docker-compose -f .travis/docker-compose-travis.yml start

travis_test: ## Run tests on Docker containers, as on Travis CI
	docker exec -e TERM=$(TERM) -e TOXENV=$(TOXENV) -it edx_notes_api /edx/app/edx_notes_api/edx_notes_api/.travis/run_tests.sh

travis_pii_check: ## Run pii annotations checker on Docker containers, as on Travis CI
	docker exec -e TERM=$(TERM) -e TOXENV=$(TOXENV) -it edx_notes_api /edx/app/edx_notes_api/edx_notes_api/.travis/run_pii_checker.sh

travis_stop: ## Stop running containers created by `travis_up` without removing them
	docker-compose -f .travis/docker-compose-travis.yml stop

travis_down: ## Stop and remove containers and other resources created by `travis_up`
	docker-compose -f .travis/docker-compose-travis.yml down

docker_auth:
	echo "$$DOCKER_PASSWORD" | docker login -u "$$DOCKER_USERNAME" --password-stdin

docker_build:
	docker build . --target app -t "openedx/edx-notes-api:latest"
	docker build . --target app -t "openedx/edx-notes-api:$$TRAVIS_COMMIT"
	docker build . --target newrelic -t "openedx/edx-notes-api:latest-newrelic"
	docker build . --target newrelic -t "openedx/edx-notes-api:$$TRAVIS_COMMIT-newrelic"

docker_push: docker_build docker_auth ## push to docker hub
	docker push "openedx/edx-notes-api:latest"
	docker push "openedx/edx-notes-api:$$TRAVIS_COMMIT"
	docker push "openedx/edx-notes-api:latest-newrelic"
	docker push "openedx/edx-notes-api:$$TRAVIS_COMMIT-newrelic"
