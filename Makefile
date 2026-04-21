VERSION := $(shell sed -n 's/^[[:space:]]*version = (\(.*\))/\1/p' __init__.py | tr -d ' ' | sed 's/,/./g; s/\.$$//')
PLUGIN_ZIP := komga-epub-metadata-writer-v$(VERSION).zip
DIST_DIR := dist
PLUGIN_FILES := __init__.py plugin-import-name-komga_epub_metadata_writer.txt

.PHONY: build clean

build:
	mkdir -p $(DIST_DIR)
	rm -f $(DIST_DIR)/*.zip
	zip -q -j $(DIST_DIR)/$(PLUGIN_ZIP) $(PLUGIN_FILES)

clean:
	rm -rf $(DIST_DIR)
