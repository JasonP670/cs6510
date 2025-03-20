from System import System
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
import datetime
from ProgramCreator import ProgramCreator


def main():
    size = ['S', 'M', 'L']
    prog_type = ['CPU', 'IO']
    quantum_1s = [10, 20, 30]
    quantum_ratios = [2, 3, 4]

    ProgramCreator().run()



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
            best_configs = {
                'min_waiting_time': {"value": float("inf"), "config": None},
                'min_turnaround_time': {"value": float("inf"), "config": None},
                # 'max_throughput': {"value": float("-inf"), "config": None},
                'min_response_time': {"value": float("inf"), "config": None},
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

                    for program in programs:
                        system.prepare_program(program, 0)
                    metrics = system.scheduler.schedule_jobs()
                    results["waiting_time"].append(metrics["avg_wait_time"])
                    results["turnaround_time"].append(metrics["avg_turnaround"])
                    results["throughput"].append(metrics["throughput"])
                    results["response_time"].append(metrics["avg_response_time"])
                    results["quantum_1"].append(quantum_1)
                    results["quantum_2"].append(quantum_2)


                    if metrics['avg_wait_time'] < best_configs['min_waiting_time']['value']:
                        best_configs['min_waiting_time'] = {'value': metrics['avg_wait_time'], 'config': {'quantum_1': quantum_1, 'quantum_2': quantum_2}}

                    if metrics['avg_turnaround'] < best_configs['min_turnaround_time']['value']:
                        best_configs['min_turnaround_time'] = {'value': metrics['avg_turnaround'], 'config': {'quantum_1': quantum_1, 'quantum_2': quantum_2}}

                    # if metrics['throughput'] > best_configs['max_throughput']['value']:
                    #     best_configs['max_throughput'] = {'value': metrics['throughput'], 'config': {'quantum_1': quantum_1, 'quantum_2': quantum_2}}

                    if metrics['avg_response_time'] < best_configs['min_response_time']['value']:
                        best_configs['min_response_time'] = {'value': metrics['avg_response_time'], 'config': {'quantum_1': quantum_1, 'quantum_2': quantum_2}}

                    
                    with open(f'charts/{s}/{p}/BestConfig.txt', 'w') as f:
                        f.write(f"Best Configurations for {s}-{p}\n")
                        f.write(f"Min Waiting Time: {best_configs['min_waiting_time']['value']} - ({best_configs['min_waiting_time']['config']['quantum_1']}, {best_configs['min_waiting_time']['config']['quantum_2']})\n")
                        f.write(f"Min Turnaround Time: {best_configs['min_turnaround_time']['value']} - ({best_configs['min_turnaround_time']['config']['quantum_1']}, {best_configs['min_turnaround_time']['config']['quantum_2']})\n")
                        # f.write(f"Max Throughput: {best_configs['max_throughput']['value']} - ({best_configs['max_throughput']['config']['quantum_1']}, {best_configs['max_throughput']['config']['quantum_2']})\n")
                        f.write(f"Min Response Time: {best_configs['min_response_time']['value']} - ({best_configs['min_response_time']['config']['quantum_1']}, {best_configs['min_response_time']['config']['quantum_2']})\n")

            if len(quantum_1s) > 1:
                plot_3d_graph(results, s, p)
    print("========== DONE ==========")


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
    plt.savefig(f"charts/{size}/{prog_type}/graphs.png")
    plt.close(fig)


if __name__ == "__main__":
    start_time = datetime.datetime.now()
    main()
    print(f"Execution Time: {datetime.datetime.now() - start_time}")