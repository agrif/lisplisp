;; calculate Pi!

(setq max-count 20000) ;; max iterations
(setq notify 200) ;; how often to print our current value (unused)

;; iteration variables
(setq counter 0)
(setq gather 0)

(while (nil-p (eq counter max-count))
  (setq gather
		(+ gather (*
				   (/ 4 (+ 1 (* 2 counter)))
				   (if (integer-p (/ counter 2)) 1 -1))))
  (setq counter (+ 1 counter))
  (if (integer-p (/ counter notify))
	  nil))

gather
