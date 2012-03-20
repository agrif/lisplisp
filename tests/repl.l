(setq libreadline
	  (ffi-library "libreadline.dylib"))
(setq readline
	  (ffi-procedure libreadline "readline" 'char* 'char*))
(setq add-history
	  (ffi-procedure libreadline "add_history" 'void 'char*))

(while (setq input (readline ">>> "))
  (catch (lambda (err trace)
		   (write 'stdout "Error: ")
		   (write 'stdout err)
		   (write 'stdout "\n"))
	(write 'stdout (unparse (eval (parse input))))
	(write 'stdout "\n")
	(add-history input)))
(write 'stdout "\n")
