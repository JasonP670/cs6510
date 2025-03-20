import os
from random import randint

class ProgramCreator:
    def __init__(self, qty=3):
        
        s_lines = 20
        m_lines = 500
        l_lines = 2000

        self.SIZES = {
            'small': {
                'lines': s_lines,
                'qty': qty,
                'display_name': 'S'
            }, 
            'medium': {
                'lines': 500,
                'qty': m_lines,
                'display_name': 'M'
            },
            'large': {
                'lines': 2000,
                'qty': l_lines,
                'display_name': 'L'
            }
        }

    def run(self):
        for size_key in self.SIZES:
            self.create_programs(size_key)
        self.compile_programs()

    def create_programs(self, size_key):
        # Get info
        size = self.SIZES[size_key]
        qty, lines, display_name = size['qty'], size['lines'] - 3, size['display_name']
        directory = "programs/milestone_3"
        
        os.makedirs(directory, exist_ok=True) # Ensure directory exists

        for i in range(qty):
            self.generate_program_file(directory, f"{display_name}-CPU-{i+1}.asm", lines, 'CPU')
            self.generate_program_file(directory, f"{display_name}-IO-{i+1}.asm", lines, 'IO')


    def generate_program_file(self, directory, file_name, lines, program_type):
        """ Generates an assembly program file with randomized instructions """
        with open(f"{directory}/{file_name}", 'w') as f:
            f.write("MVI R0 0 \n")
            f.write("MVI R1 1 \n")
            for _ in range(lines):
                line = self.make_line(program_type)
                f.write(f"{line} \n")
            f.write("SWI 1 \n")


    def make_line(self, program_type):
        """Returns a randomly generated assembly instruction based on program type."""
        instruction_set = ("ADD R0 R0 R1", "SWI 21")
        probabilities = {
            "CPU": (9, 1),
            "IO": (5, 5)
        }

        return instruction_set[0] if randint(1, 10) <= probabilities[program_type][0] else instruction_set[1]
            

    def compile_programs(self):
        """ Compiles all generated assembly programs """
        pos = 0
        for size_key, size in self.SIZES.items():
            display_name = size['display_name']
            directory = "programs/milestone_3"
            for i in range(size['qty']):
                lines = size['lines']
                cpu_file = f"{directory}/{display_name}-CPU-{i+1}.asm"
                io_file = f"{directory}/{display_name}-IO-{i+1}.asm"
                os.system(f"osx {cpu_file} {pos}")
                bites = lines * 6
                pos += bites + 10
                os.system(f"osx {io_file} {pos}")
                bites = lines * 6
                pos += bites + 10




if __name__ == '__main__':
    creator = ProgramCreator()
    creator.run()