; This is an I/O bound program, it will loop forever doing an SWI instruction
LOOP  SWI 0  ; Do some kind of I/O operation here
      B LOOP ; Loop to Beginning (infinite loop)