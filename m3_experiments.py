from System import System
import os


def main():
    system = System()
    base_path = 'programs/milestone_3'
    size = 'S'
    strategy = 'FCFS'
    quantum_1 = 4
    quantum_2 = 16
    
    programs = []
    for i in range(3):
        cpu_file = f"{base_path}/{size}-CPU-{i+1}.osx"
        io_file = f"{base_path}/{size}-IO-{i+1}.osx"
        programs.append(cpu_file)
        programs.append(io_file)
    
    system.scheduler.set_strategy(strategy)
    system.Q1.set_quantum(quantum_1)
    system.Q2.set_quantum(quantum_2)

    prepare_program(system, programs)
    metrics = system.scheduler.schedule_jobs()
    print(metrics)

def prepare_program(system, programs):
    for program in programs:
        program_info = system.memory_manager.prepare_program(program)
        pcb = system.create_pcb(program_info, 0)
        system.job_queue.append(pcb)


if __name__ == "__main__":
    main()