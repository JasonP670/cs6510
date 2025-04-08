START           MVI R1 1 ; Initialize counter
                MVI R2 10 ; Number of items to produce
                MVI R3 0 ; Current item count

PRODUCE_LOOP    CMP R3 R2 ; Compare current count with target
                BEQ DONE ; If equal, we're done
                
                ; Produce item (in this case, just use counter as item)
                MVI R4 1 ; Shared memory key (should be set by parent)
                ;PUSH R1  Push item to stack
                SWI 30 ; System call to produce item
                
                ADD R3 R3 1 ; Increment counter
                ADD R1 R1 1 ; Increment item value
                JMP PRODUCE_LOOP

DONE            SWI 1 ; End program 