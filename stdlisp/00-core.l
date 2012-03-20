;; Core Lisp Functions -- support for
;; builtins/core.py, builtins/procedure.py, builtins/types.py

;; useful function for creating lists of evaluated arguments
(setq list (lambda (&rest rest) rest))

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
(defun cddr (cell)
  (cdr (cdr cell)))

;; an implementation of quasiquote

(defmacro unquote (arg)
  (list 'quote (list 'unquote arg)))

(defmacro unquote-splicing (arg)
  (list 'quote (list 'unquote-splicing arg)))

(defmacro quasiquote (arg)
  (if (cell-p arg)
	  (if (eq (car arg) 'unquote)
		  (let ((unquote-args (cdr arg)))
			(if (and (cell-p unquote-args) (nil-p (cdr unquote-args)))
				(car unquote-args)
			  (throw "invalid arguments to unquote")))
		
		(if (and (cell-p (cdr arg)) (cell-p (cadr arg)) (eq (car (cadr arg)) 'unquote-splicing))
			(let ((first (car arg)) (unquote-args (cdr (cadr arg))))
			  (if (and (cell-p unquote-args) (nil-p (cdr unquote-args)))
				  (list 'quote (cons
								(eval (list 'quasiquote (car arg)))
								(eval (car unquote-args))))
				(throw "invalid arguments to unquote-splicing")))
		  (list 'quote (cons
						(eval (list 'quasiquote (car arg)))
						(eval (list 'quasiquote (cdr arg)))))))
	(list 'quote arg)))
