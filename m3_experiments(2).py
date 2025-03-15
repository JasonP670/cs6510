from System import System
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata


def main():
    size = ['S', 'M', 'L']
    prog_type = ['CPU', 'IO']
    quantum_1s = [10, 20, 30]
    quantum_ratios = [2, 3, 4]


    for s in size:
        for p in prog_type:
            results = {
                "waiting_time": [],
                "turnaround_time": [],
                "throughput": [],
                "response_time": [],
                "quantum_1": [],
                "quantum_2": []
            }
            for quantum_1 in quantum_1s:
                for ratio in quantum_ratios:
                    quantum_2 = quantum_1 * ratio
                    system = System()
                    system.scheduler.set_strategy('MLFQ')
                    system.Q1.set_quantum(quantum_1)
                    system.Q2.set_quantum(quantum_2)
                    

                    programs = [
                        f"programs/milestone_3/{s}-{p}-1.osx",
                        f"programs/milestone_3/{s}-{p}-2.osx",
                        f"programs/milestone_3/{s}-{p}-3.osx",
                    ]

                    prepare_program(system, programs)
                    metrics = system.scheduler.schedule_jobs()
                    results["waiting_time"].append(metrics["avg_wait_time"])
                    results["turnaround_time"].append(metrics["avg_turnaround"])
                    results["throughput"].append(metrics["throughput"])
                    results["response_time"].append(metrics["avg_response_time"])
                    results["quantum_1"].append(quantum_1)
                    results["quantum_2"].append(quantum_2)
            plot_3d_graph(results, s, p)

def prepare_program(system, programs):
    for program in programs:
        program_info = system.memory_manager.prepare_program(program)
        pcb = system.create_pcb(program_info, 0)
        system.job_queue.append(pcb)

def plot_3d_graph(results, size, prog_type):
    fig = plt.figure(figsize=(14, 10))

    metrics = ['waiting_time', 'turnaround_time', 'throughput', 'response_time']
    titles = ['Avg Waiting Time', 'Avg Turnaround Time', 'Throughput', 'Avg Response Time']
    z_labels = ['Waiting Time', 'Turnaround Time', 'Throughput', 'Response Time']

    for i, metric in enumerate(metrics):
        ax = fig.add_subplot(2, 2, i+1, projection='3d')

        quantum_1 = np.array(results["quantum_1"])
        quantum_2 = np.array(results["quantum_2"])
        z_values = np.array(results[metric])

        grid_x, grid_y = np.meshgrid(
            np.linspace(min(quantum_1), max(quantum_1), 50),
            np.linspace(min(quantum_2), max(quantum_2), 50)
        )
        grid_z = griddata((quantum_1, quantum_2), z_values, (grid_x, grid_y), method='cubic')


        ax.plot_surface(grid_x, grid_y, grid_z, cmap='viridis', edgecolor='k', alpha=0.8)
        ax.scatter(quantum_1, quantum_2, z_values, color='red', marker='o', label="Data Points")


        ax.set_xlabel('Quantum 1')
        ax.set_ylabel('Quantum 2')
        ax.set_zlabel(z_labels[i])
        ax.set_title(f"{titles[i]} - {size}-{prog_type}")
    
    plt.tight_layout()
    plt.savefig(f"charts/{size}-{prog_type}.png")
    plt.close(fig)




if __name__ == "__main__":
    main()