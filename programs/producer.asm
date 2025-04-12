        MVI R1 0 ; incrementor
        MVI R2 10 ; limit
        MVI R3 1 ; counter

LOOP    CMP R1 R2 ; compare incrementor with limit
        BGT END ; if incrementor > limit, go to end
        SWI 30 ; call system call to produce value
        ADD R1 R1 R3 ; increment incrementor by counter
        MOV R0 R1 ;
        B LOOP ; repeat loop

END     SWI 1 ; end of program    
