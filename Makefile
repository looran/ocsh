PREFIX=/usr/local
BINDIR=$(PREFIX)/bin

all:

install:
	install -m 0755 octopshh.py $(BINDIR)/op

tests:
	python test_octopshh.py
