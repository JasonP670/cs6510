; this is an I/O bound program, it will loop forever doing I/O
MVI R2 50 ; set R2 to 50
MVI R1 1 ; set R1 to 1

LOOP SUB R2 R2 R1 ; subtract 1 from Z
    SWI 2   ; print
    BGT LOOP ; loop if Z>0

SWI 1 ; DONE