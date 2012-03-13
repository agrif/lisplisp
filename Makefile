PYPY=/home/agrif/local/pypy

PYTHON=python
TRANSLATOR=${PYPY}/pypy/translator/goal/translate.py

.PHONY : all jit

all :
	${PYTHON} ${TRANSLATOR} target-lisp.py

jit :
	${PYTHON} ${TRANSLATOR} --opt=jit target-lisp.py

clean :
	rm -f target-lisp-c target-lisp.pyc
