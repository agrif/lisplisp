(defun fail ()
  (throw "amb tree exhausted"))

(defmacro amb (&rest rest)
  (let ((old-fail fail))
	(if (eq (length rest) 0)
		`(,old-fail)
	  `(call/cc (lambda (cc)
				  (setq fail (lambda ()
							   (setq fail ,old-fail)
							   (cc (amb . ,(cdr rest)))))
				  ,(car rest))))))

(defun require (condition)
  (if (not condition)
	  (fail)))

(setq x (amb 1 2 3))
(setq y (amb 4 5 6))
(print "??? x is " x ", y is " y)
(require (eq (* x y) 10))

(print "### x is " x ", y is " y)
