.PHONY: help tests
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

tests: ## [host] Run tests (uses docker)
	docker compose run lo_api python3 -m unittest discover -s lotemplate/unittest
