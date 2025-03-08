import os
from random import randint

SIZES = {
    'small': {
        'lines': 20,
        'qty': 3,
        'display_name': 'S'
    }, 
    'medium': {
        'lines': 500,
        'qty': 3,
        'display_name': 'M'
    },
    'large': {
        'lines': 2000,
        'qty': 3,
        'display_name': 'L'
    }
}

def main():
    for size_key in SIZES:
        create_programs(size_key)
    # create_programs()
    compile_programs()

def create_programs(size_key):
    # Get info
    size = SIZES[size_key]
    qty, lines, display_name = size['qty'], size['lines'], size['display_name']
    directory = f"programs/milestone_3"
    
    os.makedirs(directory, exist_ok=True) # Ensure directory exists

    for i in range(qty):
        generate_program_file(directory, f"{display_name}-CPU-{i+1}.asm", lines, 'CPU')
        generate_program_file(directory, f"{display_name}-IO-{i+1}.asm", lines, 'IO')


def generate_program_file(directory, file_name, lines, program_type):
    """ Generates an assembly program file with randomized instructions """
    with open(f"{directory}/{file_name}", 'w') as f:
        f.write("MVI R0 0 \n")
        f.write("MVI R1 1 \n")
        for _ in range(lines):
            line = make_line(program_type)
            f.write(f"{line} \n")
        f.write("SWI 1 \n")


def make_line(program_type):
    """Returns a randomly generated assembly instruction based on program type."""
    instruction_set = ("ADD R0 R0 R1", "SWI 20")
    probabilities = {
        "CPU": (9, 1),
        "IO": (5, 5)
    }

    return instruction_set[0] if randint(1, 10) <= probabilities[program_type][0] else instruction_set[1]
        

def compile_programs():
    """ Compiles all generated assembly programs """
    for size_key, size in SIZES.items():
        pos = 10
        display_name = size['display_name']
        directory = f"programs/milestone_3"
        for i in range(size['qty']):
            cpu_file = f"{directory}/{display_name}-CPU-{i+1}.asm"
            io_file = f"{directory}/{display_name}-IO-{i+1}.asm"
            os.system(f"osx {cpu_file} {pos}")
            os.system(f"osx {io_file} {pos}")
            pos += size['lines'] + 10




if __name__ == '__main__':
    main()