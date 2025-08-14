from typing import Iterable
import numpy as np
import matplotlib.pyplot as plt

def plot_distribution(values: Iterable[float], outfile: str):
    vals = np.array(list(values))
    fig = plt.figure()
    plt.hist(vals, bins=60)
    plt.title("Monte Carlo – Monthly Total Equity Distribution")
    plt.xlabel("Total equity (€)")
    plt.ylabel("Frequency")
    fig.tight_layout()
    fig.savefig(outfile, dpi=160)
    plt.close(fig)
