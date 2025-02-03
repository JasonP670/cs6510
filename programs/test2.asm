RESULT .WORD 0 ;

MVI R0 5 ; times to add
MVI R1 0 ; result
MVI R2 0 ; counter
ADR R3 RESULT ; address to store result
MVI R4 5 ; number to add
MVI R5 1 ; incrementor


ADD_LOOP    CMP R0 R2 ; check if counter is equal to number
            BEQ END_LOOP ; if yes, end loop
            
            ADD R1 R1 R4 ; 
            ADD R2 R2 R5 ; increment counter
            B ADD_LOOP

END_LOOP    MOV R0 R1 ; move result to R0
            STR R1 [R3] ; store result
            SWI 2 ;
            SWI 1 ;
MVI R0 3 ;
MVI R1 2 ;
ADD R2 R1 R2 ;
SUB R3 R1 R2 ;
MUL R4 R1 R2 ;
DIV R5 R1 R2 ;

SWI 1 ;