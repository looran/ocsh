PREFIX=/usr/local
BINDIR=$(PREFIX)/bin

all:

install:
	install -m 0755 octopuss.py $(BINDIR)/op

tests:
	python test_octopuss.py
