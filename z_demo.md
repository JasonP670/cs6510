# Jason Petersen & Lourdes Castleton

## Compile Program

`osx p1.asm 0`
`osx p2.asm 0`
`osx p3.asm 100`

## Run 1 program

`execute p1.osx 0 -v`

## Run programs that overlap time and space

`execute p1.osx 0 p2.osx 0 -v`
`execute p1.osx 0 p2.osx 0 p3.osx 1 -v`

## Fork w/o exec

`execute fork.osx 0 -v`

## Fork w/ exec

`execute exec.osx 0 -v`

## Coredump

`coredump -v`
