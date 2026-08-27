SITE_DIR := site
PORT     ?= 8000
HOST     ?= 127.0.0.1

.PHONY: help serve stop list blogger blogger-en

help:
	@echo "Targets:"
	@echo "  serve   Serve $(SITE_DIR)/ over HTTP (PORT=$(PORT), HOST=$(HOST))"
	@echo "  stop    Stop a server previously started by 'make serve'"
	@echo "  list    List the HTML pages available in $(SITE_DIR)/"
	@echo "  blogger    Gera $(SITE_DIR)/geometria_simpletica-blogger.html (fragmento p/ Blogger)"
	@echo "  blogger-en Idem, a partir da versão inglesa symplectic_geometry.html"

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

# BLOGGER_ARGS="--img-base https://..." para apontar aos SVG em vez de data URI
blogger:
	@python3 scripts/make_blogger.py $(BLOGGER_ARGS)

blogger-en:
	@python3 scripts/make_blogger.py --src $(SITE_DIR)/symplectic_geometry.html $(BLOGGER_ARGS)
