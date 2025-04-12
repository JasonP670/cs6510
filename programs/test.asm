START MVI R1 1
      MVI R2 10
      MVI R3 0
      MVI R4 1

LOOP  CMP R3 R2
      BEQ DONE
      SWI 30
      ADD R3 R3 R4
      ADD R1 R1 R4
      B LOOP

DONE  SWI 1