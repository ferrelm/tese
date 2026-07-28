SITE_DIR := site
PORT     ?= 8000
HOST     ?= 127.0.0.1

.PHONY: help serve stop list

help:
	@echo "Targets:"
	@echo "  serve   Serve $(SITE_DIR)/ over HTTP (PORT=$(PORT), HOST=$(HOST))"
	@echo "  stop    Stop a server previously started by 'make serve'"
	@echo "  list    List the HTML pages available in $(SITE_DIR)/"

SERVE_CMD := python3 -m http.server $(PORT) --bind $(HOST) --directory $(SITE_DIR)

# Frees the port, but only if it is our own server holding it. See the script:
# it waits for the port to actually be released before returning.
stop:
	@scripts/free_port.sh $(PORT) "$(SERVE_CMD)"

serve: stop
	@echo "Serving $(SITE_DIR)/ at http://$(HOST):$(PORT)/  (Ctrl-C to stop)"
	@$(SERVE_CMD)

list:
	@ls -1 $(SITE_DIR)/*.html
