.PHONY: ci_down ci_start ci_stop ci_test ci_up

ci_up: ## Create containers used to run tests on ci CI
	docker compose -f .ci/docker-compose-ci.yml up -d

ci_start: ## Start containers stopped by `ci_stop`
	docker compose -f .ci/docker-compose-ci.yml start

ci_test: ## Run tests on Docker containers, as on ci CI
	docker exec -e TERM=$(TERM) -e TOXENV=$(TOXENV) -u root -it edx_notes_api /edx/app/edx_notes_api/edx_notes_api/.ci/run_tests.sh

ci_pii_check: ## Run pii annotations checker on Docker containers, as on ci CI
	docker exec -e TERM=$(TERM) -e TOXENV=$(TOXENV) -u root -it edx_notes_api /edx/app/edx_notes_api/edx_notes_api/.ci/run_pii_checker.sh

ci_stop: ## Stop running containers created by `ci_up` without removing them
	docker compose -f .ci/docker-compose-ci.yml stop

ci_down: ## Stop and remove containers and other resources created by `ci_up`
	docker compose -f .ci/docker-compose-ci.yml down

