MVI R1 0 ;
MVI R2 1 ;
ADD R0 R1 R2 ;
SWI 2 ; Print R0, should be 1
SWI 1 ; DONE