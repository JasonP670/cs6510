; Setup
MVI R1 0       ; counter
MVI R2 1       ; incrementor
MVI R3 5       ; limit

B JUMP1        ; jump far to force a page fault


; Padding - PAGE 1
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

; PAGE 2
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

; PAGE 3
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

; Target after JUMP1 (forces page fault)
JUMP1 ADD R1 R1 R2
CMP R1 R3
BEQ EXIT
B JUMP2

; PAGE 4
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

; Jump target 2
JUMP2 ADD R1 R1 R2
CMP R1 R3
BEQ EXIT
B JUMP1        ; Loop back

; PAGE 5
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

EXIT MOV R0 R1
SWI 1
