;; Lisp IO Functions -- support for builtins/io.py

(defmacro set-up-io-functions (fd)
  `(begin
	(defun print (&rest args)
	  (dolist (arg args)
		(if (string-p arg)
			(write ,fd arg)
		  (write ,fd (unparse arg))))
	  (write ,fd "\n"))))

;; by default, all functions work with stdout

(set-up-io-functions 'stdout)
