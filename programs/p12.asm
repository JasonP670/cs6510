; SETUP (Page 0)
MVI R1 0        ; counter
MVI R2 1        ; incrementor
MVI R3 10       ; limit
MVI R4 1        ; toggle value
MVI R5 0        ; toggle flag

B START         ; jump to logic

; PAGE 1 - Padding
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

; PAGE 2 - START
START CMP R1 R3
      BGT DONE          ; stop if R1 >= R3

      ADD R5 R5 R4      ; toggle: 0 → 1, 1 → 2
      CMP R5 R4
      BEQ EVEN_BRANCH
      MVI R5 0
      B ODD_BRANCH

; PAGE 3 - EVEN
EVEN_BRANCH ADD R1 R1 R2
            ADD R1 R1 R2
            B START

; PAGE 4 - ODD
ODD_BRANCH ADD R1 R1 R2
           B START

; PAGE 5 - Padding
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0
MVI R0 0

; PAGE 6 - DONE
DONE  MOV R0 R1
      SWI 1
