MVI R0 100000000  ; add a huge number to loop through
MVI R1 0     ; add ending number
MVI R2 1     ; decrement counter

LOOP SUB R0 R0 R2 ; decrement R0 by R2
CMP R0 R1    ; set Z to if R0 == R1

BNE LOOP     ; if R0 != R1 loop

SWI 0