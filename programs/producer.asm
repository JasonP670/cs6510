        MVI R1 1 ; incrementor
        MVI R2 10 ; limit
        MVI R3 1 ; counter

LOOP    SWI 33 ; mutex wait
        ADD R1 R1 R3 ; increment item
        MOV R0 R1 ; item to produce
        SWI 30 ; Produce item
        SWI 34 ; mutex signal
        CMP R1 R2 ; check if limit reached
        BEQ END ; if yes, end program
        B LOOP ; repeat loop

END     SWI 1 ; end of program    
