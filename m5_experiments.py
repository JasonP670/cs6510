from System import System
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
import datetime


def main():
    page_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


    results = {
            "page_numbers": [],
            "page_sizes": [],
            "page_faults": [],
    }

    for s in page_numbers:
        for n in page_numbers:
            system = System()
            system.set_page_number(n)
            system.set_page_size(s)
            for filepath in ['p10.osx', 'p11.osx', 'p12.osx']:
                system.handle_load(filepath)
                system.run_program(filepath)
            page_faults = system.memory_manager.page_faults
            results["page_numbers"].append(n)
            results["page_sizes"].append(s)
            results["page_faults"].append(page_faults)

    return results

def plot_results(results):
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    x = np.array(results["page_numbers"])
    y = np.array(results["page_sizes"])
    z = np.array(results["page_faults"])

    ax.scatter(x, y, z, c=z, cmap='viridis', s=50)

    ax.set_xlabel('Page Limit (Max Resident Pages)')
    ax.set_ylabel('Page Size (Instructions/Page)')
    ax.set_zlabel('Page Faults')
    ax.set_title('Page Faults vs Page Limit and Page Size')

    plt.tight_layout()
    plt.show()
    

if __name__ == "__main__":
    results = main()
    plot_results(results)