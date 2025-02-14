# OS Implementation by Jason Petersen & Lourdes Castleton

CS6510 - Spring 2025

# Start

`python main.py`

Start the OS by running the main.py file. This starts the system and the command line interface

# Load a program

`shell > load test.osx [-v]`

By starting the program you should see the prompt `shell >`. Type `load` followed by the program name. Optionally you can type `-v` to laod the program in verbose mode.

# Run a program

`shell > run [-v]`

To run a program simply type run, you will get a confirmation when the program has finished running. Optionally you can type `-v` to run the program in verbose mode.

# Check memory

`shell > coredump [-v]`

If you would like to see the contents of the memory type `coredump`. Optional `-v` flag will display the memory in the terminal, without the optional flag the memory will be saved to the file `memory.txt`.

# Check errors

`shell > errordump [-v]`

Checks for system errors. See Engineering Glossary List for system error code definitions. Optional `-v` flag will display errors in the terminal, without the optional flag the errors will be saved to the file `errors.txt`.

# Switch to bash mode

`shell > bash`

To switch the command line interface to the bash version type `bash` into the terminal. The command line will now appear as `bash > `.

At the moment bash mode does not do anything, including loading and running programs. It's simply a placeholder to be implemented later.

# Switch to shell mode

`bash > shell`

To switch back to shell mode type `shell` into the bash command line. In shell mode you can load and run programs.

# Exit the program

`shell > (bash > ) exit`

The program will continue to run until the user runs the command `exit`. This will close the program.

# Run tests

Run the file tests\run_tests.py. This will run multiple tests to ensure everything is working as expected. It includes unit tests as well as end to end tests.
