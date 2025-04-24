; Initialize registers
MVI R1 0        ; counter
MVI R2 1        ; increment
MVI R3 6        ; loop limit

B LOOP_START    ; Jump to far loop start (causes fault)

; Padding - PAGE 1
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

; Padding - PAGE 2
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

; Actual loop start - PAGE 3
LOOP_START ADD R1 R1 R2
           CMP R1 R3
           BEQ END_LOOP
           B MIDDLE

; Padding - PAGE 4
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

; Middle jump point - PAGE 5
MIDDLE ADD R1 R1 R2
       CMP R1 R3
       BEQ END_LOOP
       B LOOP_START

; Padding - PAGE 6
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

; Exit block - PAGE 7
END_LOOP MOV R0 R1
         SWI 1
