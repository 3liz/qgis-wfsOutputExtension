PLUGINNAME = wfsOutputExtension

release_zip:
	@echo
	@echo -------------------------------
	@echo Exporting plugin to zip package
	@echo -------------------------------
	@rm -f $(PLUGINNAME).zip
	@git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip HEAD
	@echo "Created package: $(PLUGINNAME).zip"

release_upload:
	@echo
	@echo -----------------------------------------
	@echo Uploading the plugin on plugins.qgis.org.
	@echo -----------------------------------------
	@plugin_upload.py ../$(PLUGINNAME).zip
