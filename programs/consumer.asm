        MVI R1 10       ; initial item
        MVI R2 1        ; limit
        MVI R3 1        ; decrementor

LOOP    SWI 33          ; mutex wait
        SWI 31          ; consume item
        SUB R1 R1 R3    ; decrement item
        MOV R0 R1       ; 
        SWI 34          ; mutex signal
        CMP R1 R2       ; check if limit reached
        BLT END         ; if yes, end program
        B LOOP          ; if no, repeat loop
END     SWI 1           ; end of program
