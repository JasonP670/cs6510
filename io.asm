START   MVI R1 1 ;
        SWI 20 ;
        MVI R2 0 ;
        SWI 20 ;
        ADD R0 R1 R2 ;
        SWI 1 ;
