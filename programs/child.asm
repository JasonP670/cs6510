MVI R1 9 ;
MVI R2 111 ;
MUL R0 R1 R2 ;
SWI 2 ; Print R0, should be 999
SWI 1 ; DONE