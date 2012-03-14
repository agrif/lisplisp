;; Core Lisp Functions -- support for
;; builtins/core.py, builtins/procedure.py, builtins/types.py

;; useful function for creating lists of evaluated arguments
(setq list (lambda (&rest cdr) cdr))

;; macro definition macro (yes. really.)
(setq defmacro
	  (macro (symbol args &rest body)
			 ;; return the expression `(setq ,symbol (macro ,args . ,body))
			 (list 'setq symbol (cons 'macro (cons args body)))))

;; similar for functions
(defmacro defun (symbol args &rest body)
  (list 'setq symbol (cons 'lambda (cons args body))))

;; common synonyms for nil-p
(setq null nil-p)
(setq not nil-p)

;; shortcuts for common car/cdr combinations
(defun caar (cell)
  (car (car cell)))
(defun cadr (cell)
  (car (cdr cell)))
(defun cdar (cell)
  (cdr (car cell)))
(defun cddr(cell)
  (cdr (cdr cell)))

;; an implementation of quasiquote
;; doesn't support splicing or nesting

(defun expand-unquotes (el)
  (if (cell-p el)
	  (if (eq (car el) 'unquote)
		  (eval (cadr el))
		(cons (expand-unquotes (car el)) (expand-unquotes (cdr el))))
	el))

(defmacro quasiquote (arg)
  (list 'quote (expand-unquotes arg)))
