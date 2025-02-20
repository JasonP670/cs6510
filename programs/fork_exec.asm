START           MVI R1 1 ;
                MVI R2 1 ;
                ADD R3 R1 R2 ;

                SWI 10 ; FORK

                MVI R1 0 ; set R1 to 0
                CMP R0 R1 ; compare R0 and R1, if R0 is 0 it is the child process and jump to CHILD_START
                BEQ CHILD_START ;

                SUB R0 R3 R2 ;
                SWI 12 ; WAIT
                SWI 2 ; Print R0, parent should be 1
                SWI 1 ; DONE

CHILD_START     SWI 11 ; EXEC