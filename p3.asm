MVI R1 2 ;
MVI R2 1 ;
ADD R0 R1 R2 ;
SWI 2 ; Print R0, should be 3
SWI 1 ;