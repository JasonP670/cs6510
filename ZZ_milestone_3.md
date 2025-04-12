# Jason Petersen & Lourdes Castleton


python main.py

## FCFS
`execute p1.osx 0`

![ganttChart](charts\manual\CPU\MLFQ_manual_CPU_1000000_1000000.png)


## RR
`setSched RR`

`setRR 1 2`

`execute p1.osx 0 p2.osx 0`

![ganttChart](charts\manual\CPU\RR_manual_CPU_1_2.png)


## MLFQ
python main.py

setSched MLFQ
setRR 8 16
execute p4.osx 0 p5.osx 0 p6.osx 0


![ganttChart](charts\manual\CPU\MLFQ_manual_CPU_8_16.png)
