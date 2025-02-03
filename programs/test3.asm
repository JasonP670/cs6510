RESULT  .WORD 0 ;

FOO     .WORD 300 ;

START   MVI R0 5 ; number to calculate factorial
        MVI R1 1 ; result
        MVI R2 0 ; counter
        ADR R3 RESULT ; address to store result
        MVI R4 1 ; increment

FACTORIAL_LOOP  CMP R0 R2 ; check if counter is equal to number
                BEQ END_LOOP ; if yes, end loop

                MUL R1 R1 R2 ; multiply result by counter
                ADD R2 R2 R4 ; increment counter
                B FACTORIAL_LOOP ; repeat loop

END_LOOP        MOV R0 R1 ; move result to R0
                STR R1 [R3] ; store result
                SWI 1 ;