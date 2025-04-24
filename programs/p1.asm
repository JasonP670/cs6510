MVI R1 0 ; counter
MVI R2 1 ; incrementor
MVI R3 10 ; limit
LOOP    ADD R1 R1 R2
        CMP R1 R3 ;
        BEQ END
        B LOOP
END     MOV R0 R1 ; return value
        ; SWI 2 ;
        SWI 1 ; end of program