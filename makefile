#######################################################################
# Package-Custom Variables
PACKAGE=dust_filter
SDIST_DEPS = $(PACKAGE)/*.py $(addprefix $(PACKAGE)/, DATE VERSION) \
	makefile setup.py MANIFEST.in
CLEAN_FILES = log
###################################################################
SHELL := /bin/bash

# Standard Makefile Variables

# Version Management
DATEFILE := $(PACKAGE)/DATE
VERSIONFILE := $(PACKAGE)/VERSION
export GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null)
GIT_VERSION := $(shell git describe --tags --dirty --always \
	--match 'v*.*.*' 2>/dev/null)
BASE_DATE := $(shell cat $(DATEFILE))
#BASE_VERSION := $(shell cat $(VERSIONFILE) | sed -e s/-.*//g)
BASE_VERSION := $(shell cat $(VERSIONFILE))
TODAY := $(shell date +%Y/%m/%d)
export VERSION := $(if $(GIT_VERSION),$(GIT_VERSION),$(BASE_VERSION))
#export VERSION = $(BASE_VERSION)
DATE := $(if $(GIT_VERSION), $(TODAY), $(BASE_DATE))
#DATE = $(BASE_DATE)
export UVERSION := $(shell echo $(VERSION) | sed -e s/\\./_/g)
BUMPVERSION := bumpversion --config-file=.bumpversion.$(GIT_BRANCH)

###############################################################################
# Standard Build Targets

# distribution
dist: FORCE sdist rpm archive

# export an archive of the current git working directory (if we are in one)
archive:
	@ARCHCMD="git archive --prefix=$(DIMAGE)_archive-$(VERSION)/ \
		-o dist/$(DIMAGE)_archive-$(VERSION).tar.gz \
		$(GIT_BRANCH)"; \
	if [ -d .git ]; then \
		mkdir -p dist; \
		echo $$ARCHCMD; $$ARCHCMD; \
	else \
		echo "skipping archive creation - this IS an archive"; \
	fi

sdist: .sdist.build FORCE
.sdist.build: $(SDIST_DEPS)
	echo $(VERSION) > $(VERSIONFILE)
	echo $(DATE) > $(DATEFILE)
	python setup.py --version=$(VERSION) sdist
	touch .sdist.build

rpm: .rpm.build FORCE
.rpm.build: $(SDIST_DEPS) setup.cfg
	echo $(VERSION) > $(VERSIONFILE)
	echo $(DATE) > $(DATEFILE)
	python setup.py --version=$(VERSION) bdist_rpm
	touch .rpm.build

deb: .deb.build FORCE
.deb.build: $(SDIST_DEPS) setup.cfg
	echo $(VERSION) > $(VERSIONFILE)
	echo $(DATE) > $(DATEFILE)
	python setup.py --version=$(VERSION) bdist_deb
	touch .deb.build

clean:
	/bin/rm -rf sdist dist build .*.build $(CLEAN_FILES)
	$(MAKE) -C docs clean

########################################################################
# development, release, and convenience targets

FORCE:

info:
	@echo "GIT_BRANCH   = $(GIT_BRANCH)"
	@echo "BASE_VERSION = $(BASE_VERSION)"
	@echo "GIT_VERSION  = $(GIT_VERSION)"
	@echo "VERSION      = $(VERSION)"
	@echo "UVERSION     = $(UVERSION)"

release patch minor major: ensure_release_branch
	@BVOUT=`$(BUMPVERSION) --allow-dirty --dry-run --list $@`; \
	NV=`echo $$BVOUT | grep new_version | sed -r s,"^.*=",,`; \
	PROMPT="release version $$NV from branch $(GIT_BRANCH)? [y/n] "; \
	read -p "$$PROMPT" -n 1 -r; echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
	  echo "aborting on user command"; exit 1; fi

	@echo "proceeding with release"
	$(BUMPVERSION) $@
	echo v`cat .baseversion.$(GIT_BRANCH)` > $(VERSIONFILE)
	echo $(TODAY) > $(DATEFILE)
	git add -u
	git commit -m "releasing version `cat .baseversion.$(GIT_BRANCH)`"
	git tag v`cat .baseversion.$(GIT_BRANCH)`

ensure_release_branch:
	@if [[ -z "$(GIT_BRANCH)" ]]; \
	    then echo "ERROR: not in a working tree"; exit 1; fi
	@if [[ ! "$(GIT_BRANCH)" =~ ^(master|unstable)$$ ]]; \
	    then echo "ERROR: $(GIT_BRANCH) is not releasable branch"; \
	    exit 1; fi

############################################################################
# Custom Targets

test:
	mkdir -p log
	python3 -m dust_filter.core -M

