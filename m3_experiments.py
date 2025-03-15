from System import System
import os


def main():
    sizes = ['S', 'M', 'L']
    quantum_1s = [8, 16, 32]
    quantum_ratios = [2, 3, 4]

    test_cases = [
        (size, q1, q1*ratio)
        for size in sizes
        for q1 in quantum_1s
        for ratio in quantum_ratios
    ]

    for size, q1, q2 in test_cases:
        run(size, q1, q2)
    

    
    

def run(size, quantum_1, quantum_2):
    base_path = 'programs/milestone_3'

    system = System()
    system.scheduler.set_strategy('MLFQ')
    system.Q1.set_quantum(quantum_1)
    system.Q2.set_quantum(quantum_2)
        
    programs = []
    for i in range(3):
        cpu_file = f"{base_path}/{size}-CPU-{i+1}.osx"
        io_file = f"{base_path}/{size}-IO-{i+1}.osx"
        programs.append(cpu_file)
        programs.append(io_file)
    

    prepare_program(system, programs)
    metrics = system.scheduler.schedule_jobs()
    print(f"Size: {size}, Quantum 1: {quantum_1}, Quantum 2: {quantum_2}")
    print(metrics)

def prepare_program(system, programs):
    for program in programs:
        program_info = system.memory_manager.prepare_program(program)
        pcb = system.create_pcb(program_info, 0)
        system.job_queue.append(pcb)


if __name__ == "__main__":
    main()