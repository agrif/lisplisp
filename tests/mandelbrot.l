;; some global settings
(setq max-iterations 200)
(setq width 160)
(setq height 60)
(setq center '(-0.7 0.0))
;(setq center '(0.0 0.0))
(setq radius 1.5)
(setq aspect-ratio 0.5) ;; width / height per pixel

(setq julia-set nil)
(setq julia-constant '(0.25 -0.6))

;; complex number maths
(defun c+ (a b)
  (list (+ (car a) (car b)) (+ (cadr a) (cadr b))))
(defun c* (a b)
  (if (number-p a)
	  ((* a (car b)) (* a (cadr b)))
	(if (number-p b)
		((* (car a) b) (* (cadr a) b))
	  (list (+ (* (car a) (car b)) (* -1 (cadr a) (cadr b)))
			(+ (* (cadr a) (car b)) (* (car a) (cadr b)))))))
(defun mag2 (a)
  (+ (* (car a) (car a)) (* (cadr a) (cadr a))))

;; iteration loop
(defun do-iter (p)
  (setq iteration 0)
  (setq iterating t)
  (setq z (if julia-set p '(0 0)))
  (while iterating
	(setq z (c+ (c* z z) (if julia-set julia-constant p)))
	(if (> (mag2 z) 4.0)
		(setq iterating nil)
	  (setq iteration (+ iteration 1)))
	(if (eq iteration max-iterations)
		(setq iterating nil)))
  (if (eq iteration max-iterations)
	  -1
	iteration))

;; pixel 'color'
(defun get-pixel (iters)
  (if (eq iters -1)
	  " "
	(if (< iters (* max-iterations 0.4))
		"#"
	  ".")))

;; step size, per pixel
(setq step (/ (* radius 2) (+ width -1)))

;; iteration variables
(setq x 0 y 0)
(setq point (list (* -1 step (/ width 2))
				  (* -1 (/ step aspect-ratio) (/ height 2))))
(setq point (c+ center point))
(setq origin-x (car point))

;; finally, the iteration
(while (not (eq y height))
  (while (not (eq x width))
	(let ((iters (do-iter point)))
	  (write 'stdout (get-pixel iters)))
	(setq x (+ x 1))
	(setq point (list (+ (car point) step) (cadr point))))
  (setq y (+ y 1))
  (setq x 0)
  (setq point (list origin-x
					(+ (cadr point) (/ step aspect-ratio))))
  (write 'stdout "\n"))
