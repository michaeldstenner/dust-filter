MANPAGES_BASE = df2000
OTHERDOCS_BASE = 
VERSIONFILE := ../dust_filter/VERSION

BASE_VERSION := $(shell cat $(VERSIONFILE))
DOC_VERSION = $(if $(VERSION),$(VERSION),$(BASE_VERSION))

MANPAGES_GROFF = $(MANPAGES_BASE:=.1.gz)
MANPAGES_PDF = $(MANPAGES_BASE:=.pdf)
OTHERDOCS_PDF = $(OTHERDOCS_BASE:=.pdf)

MANCMD = pandoc -s -f markdown -t man
TEXCMD = pandoc -V version=$(DOC_VERSION) -t latex --template=latex.template

all: $(MANPAGES_GROFF) $(MANPAGES_PDF) $(OTHERDOCS_PDF)

info:
	@echo $(MANPAGES_GROFF)

%.1.gz: %.md
	$(MANCMD) $*.md | gzip > $@

%.tex: %.md
	$(TEXCMD) $*.md -o $@

%.pdf: %.tex
	pdflatex $*.tex

clean:
	/bin/rm -f *.aux *.tex *.log *.dvi *.out

cleanall: clean
	/bin/rm -f *.pdf *.1.gz
