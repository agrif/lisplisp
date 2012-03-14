;; calculate Pi!

(setq max-count 20000) ;; max iterations
(setq notify 200) ;; how often to print our current value (unused)

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
  (if (integer-p (/ counter notify))
	  nil))

;; print the result
gather
