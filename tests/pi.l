;; calculate Pi!

(setq max-count 20000) ;; max iterations
(setq notify 200) ;; how often to print our current value

;; iteration variables
(setq counter 0)
(setq gather 0)

;; helper
(defun get-term (i)
  (* (/ 4 (+ 1 (* 2 i)))
	 (if (integer-p (/ i 2)) 1 -1)))

;; calculation loop
(while (nil-p (eq counter max-count))
  (setq gather (+ gather (get-term counter)))
  (setq counter (+ 1 counter))
  (if (not (integer-p (/ counter notify)))
	  nil
	(write 'stdout "current: ")
	(write 'stdout (unparse gather))
	(write 'stdout "\n")))

;; print the result
(write 'stdout "calculated pi: ")
(write 'stdout (unparse gather))
(write 'stdout "\nin ")
(write 'stdout (unparse max-count))
(write 'stdout " terms\n")
