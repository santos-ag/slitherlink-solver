.PHONY: all test clean

all: test

test:
	python3 solver_runner.py

clean:
	rm -f instancias/*.tmp.cnf
