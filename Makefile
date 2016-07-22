project_name = eayunstack-auto-evacuate
version = $(shell grep "Version" netmon.spec | awk '{print $$2}')

sources:
    git archive --format=tar --prefix=$(project_name)-$(version)/ HEAD | gzip -9v > $(project_name)-$(version).tar.gz
