START   MVI R1 1      ; Initialize counter
        MVI R2 1000   ; Loop limit
        MVI R3 0      ; Accumulator

LOOP    MUL R3 R1 R2   ; Multiply accumulator by counter
        ADD R3 R1 R2     ; Add counter to result
        ADD R1 R1 R1   ; Increment counter
        CMP R1 R2     ; Compare counter with limit
        BGT LOOP       ; Jump if less than or equal     
SWI 2          ; Output the result (assuming SWI 2 is for output)
SWI 1           ; Halt program