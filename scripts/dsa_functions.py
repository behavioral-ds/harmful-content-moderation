import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def n_star(
    alpha: float,
    beta: float,
    c: int,
    kappa: float,
    theta: float
):
    """
        Branching factor ($n^{*}$)
    """
    
    try:
        kernel_term = 1 / (theta * c ** theta)
        influence_term = (alpha - 1)/(alpha - beta - 1)
        n = kappa * influence_term * kernel_term
    except:
        n = np.nan
    
    return n

def tau_life(
    c: float,
    theta: float
):
    """
        Content half-life ($\tau_{1/2}$)
    """
    tau_half = c * (2 ** (1 / theta) - 1)
    
    return tau_half

def calc_chi_powerlaw(
    theta: float,
    n: float,
    delta_: float,
    c: int
):
    """
        Harm ($\chi$)
    """
    
    n_delta = n * (1 - (c ** theta) * (c + delta_) ** (- theta))
    
    chi = (n - n_delta) / (1 - n_delta)
    
    return chi

def calc_chi_powerlaw_abs(
    theta: float,
    n: float,
    delta_: float,
    c: int
):
    """
        Harm ($\chi$)
    """
    
    n_delta = n * (1 - (c ** theta) * (c + delta_) ** (- theta))
    
    chi = 1 / (1 - n) - 1 / (1 - n_delta)
    
    return chi

def calc_delta_powerlaw(
    theta: float,
    n: float,
    chi_: float,
    c: int
):
    """
        Reaction time ($\Delta$)
    """
    
    try:
        
        term1 = 1 / (n * c ** theta)
        
        term2 = (chi_ * (1 - n)) / (1 - chi_)
        
        # 604800 - 7 * 24 * 60 * 60 - 1 week
        delta = min(max(0, (term1 * term2) ** (-(1 / theta)) - c), 604800)
        
    except:
        delta = None
        
    return delta

def read_in_dfs(
    file_paths: list,
    only_best: bool,
    alpha: float,
    c: int,
    delta_: float,
    chi_: float
):
    """
        Compute for analysis relevant parameters
    """

    df_all = []
    
    for i, path in enumerate(file_paths):
        
        df = pd.read_pickle(path)
        print(f'Dataset: {i+1} - shape: {df.shape}')
        print(f'File: {path}')
        
        df['beta'] = df.apply(lambda x: x['p_fit'][0], axis=1)
        df['kappa'] = df.apply(lambda x: x['p_fit'][1], axis=1)
        df['theta'] = df.apply(lambda x: x['p_fit'][2], axis=1)

        # Remove entries where the random guess and the fit are identical
        df['g_p'] = df.apply(lambda x: all(x['guess'] == x['p_fit']), axis=1)
        df = df[df['g_p'] == False]
        print(f'Dataset: {i+1} - shape (only converged): {df.shape}')
        
        if only_best == True:
            # Get from random starts the one with the highest loglikelihood
            idx = df.groupby(['range'])['loglike'].transform(max) == df['loglike']
            df = df[idx].reset_index(drop=True)
            print(f'Dataset: {i+1} - shape (only best loglikelihood): {df.shape}')
        
        df['n_star'] = df.apply(lambda x: n_star(alpha,
                                         x['beta'], 
                                         c,
                                         x['kappa'],
                                         x['theta']), 
                                axis=1)
        
        df['chi'] = df.apply(lambda x: calc_chi_powerlaw(
                                         x['theta'], 
                                         x['n_star'],
                                         delta_,
                                         x['theta']), 
                             axis=1)
        
        df['delta'] = df.apply(lambda x: calc_delta_powerlaw(
                                         x['theta'], 
                                         x['n_star'],
                                         chi_,
                                         c), 
                             axis=1)
        
        # Only stationary Hawkes processes
        df = df[df['n_star'] <= 1].reset_index(drop=True)
        print(f'Dataset: {i+1} - shape (stationary): {df.shape}')

        # Calculate content half-life
        df['tau_'] = df.apply(lambda x: tau_life(c, x['theta']), axis=1)
        
        df = df.dropna().reset_index(drop=True)
        
        df_all.append(df)
    
    return df_all

def plot_distr(
    df_all: list
):

    for df in df_all:
        fig, axs = plt.subplots(1, 4, figsize=(12,4))

        # basic plot
        axs[0].boxplot(df.beta.values)
        axs[0].set_ylim([0, 1])
        axs[0].set_xticks([1], [r'$\beta$'], fontsize=14)
        axs[1].boxplot(df.kappa.values)
        axs[1].set_ylim([0, 1])
        axs[1].set_xticks([1], [r'$\kappa$'], fontsize=14)
        axs[2].boxplot(df.theta.values)
        axs[2].set_ylim([0, 1])
        axs[2].set_xticks([1], [r'$\theta$'], fontsize=14)
        axs[3].boxplot(df.n_star.values)
        axs[3].set_ylim([0, 1])
        axs[3].set_xticks([1], [r'$n^{*}$'], fontsize=14)

        plt.show()
        
        df.describe()

def print_stats(
    df: pd.DataFrame
):

    tau_mean = np.mean(df.tau_.values)
    tau_median = np.median(df.tau_.values)

    n_star_mean = np.mean(df.n_star)
    n_star_median = np.median(df.n_star.values)

    chi_mean = np.mean(df.chi.values)
    chi_median = np.median(df.chi.values)
    
    print(f'τ_1/2 - mean: {np.round(tau_mean / 60, 2)} mins')
    print(f'τ_1/2 - median: {np.round(tau_median / 60, 2)} mins')

    print(f'n^star - mean: {np.round(n_star_mean, 2)}')
    print(f'n^star - median: {np.round(n_star_median, 2)}')

    print(f'χ - mean: {np.round(chi_mean * 100, 2)}%')
    print(f'χ - median: {np.round(chi_median * 100, 2)}%')