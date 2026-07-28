SITE_DIR := site
PORT     ?= 8000
HOST     ?= 127.0.0.1

.PHONY: help serve list

help:
	@echo "Targets:"
	@echo "  serve   Serve $(SITE_DIR)/ over HTTP (PORT=$(PORT), HOST=$(HOST))"
	@echo "  list    List the HTML pages available in $(SITE_DIR)/"

serve:
	@echo "Serving $(SITE_DIR)/ at http://$(HOST):$(PORT)/  (Ctrl-C to stop)"
	@python3 -m http.server $(PORT) --bind $(HOST) --directory $(SITE_DIR)

list:
	@ls -1 $(SITE_DIR)/*.html
