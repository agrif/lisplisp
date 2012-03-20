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

;; a braindead list-p (but! tailrecursive!)
(defun list-p (arg)
  (if (cell-p arg)
	  (list-p (cdr arg))
	(nil-p arg)))

;; another braindead list length
(defun length (arg)
  (if (cell-p arg)
	  (+ 1 (length (cdr arg)))
	(if (nil-p arg)
		0
	  (throw "argument is not a list"))))

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
				  (list 'cons
						(list 'quasiquote (car arg))
						(car unquote-args))
				(throw "invalid arguments to unquote-splicing")))
		  (list 'cons
				(list 'quasiquote (car arg))
				(list 'quasiquote (cdr arg)))))
	(list 'quote arg)))

;; push and pop macros
(defmacro pop (stack)
  `(if (not (cell-p ,stack))
	   nil
	 (let ((pop-item (car ,stack)))
	   (setq ,stack (cdr ,stack))
	   pop-item)))
(defmacro push (element stack)
  `(setq ,stack (cons ,element ,stack)))

;; a macro for running code on each element in a list
(defmacro dolist (binding &rest body)
  (let ((binding-length (length binding)))
	(if (not (eq binding-length 2))
		(if (not (eq binding-length 3))
			(throw "dolist binding is not length 2 or 3"))))
  
  (let ((symbol (car binding)) (target (cadr binding)) (result (cddr binding)))
	(if result
		(setq result (car result)))
	
	`(let ((dolist-work ,target) (,symbol nil))
	   (if (not (list-p ,target))
		   (throw "dolist target is not a list"))
	   
	   (while (not (nil-p dolist-work))
		 (setq ,symbol (car dolist-work))
		 (begin ,@body)
		 (pop dolist-work))
	   
	   ,result)))
