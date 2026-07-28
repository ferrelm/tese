SITE_DIR := site
PORT     ?= 8000
HOST     ?= 127.0.0.1

.PHONY: help serve stop list

help:
	@echo "Targets:"
	@echo "  serve   Serve $(SITE_DIR)/ over HTTP (PORT=$(PORT), HOST=$(HOST))"
	@echo "  stop    Stop a server previously started by 'make serve'"
	@echo "  list    List the HTML pages available in $(SITE_DIR)/"

# Kill only our own leftover http.server on this port; never touch anything else.
# -x -f matches the whole command line exactly, so shells and editors that merely
# mention this string on their own command line are not affected.
stop:
	@pkill -x -f "python3 -m http.server $(PORT) --bind $(HOST) --directory $(SITE_DIR)" \
		&& echo "Stopped previous server on port $(PORT)" || true

serve: stop
	@echo "Serving $(SITE_DIR)/ at http://$(HOST):$(PORT)/  (Ctrl-C to stop)"
	@python3 -m http.server $(PORT) --bind $(HOST) --directory $(SITE_DIR)

list:
	@ls -1 $(SITE_DIR)/*.html
