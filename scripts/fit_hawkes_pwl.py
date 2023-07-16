import numpy as np
import numba
from scipy import optimize
from typing import Callable
from scipy.optimize import NonlinearConstraint
from cyipopt import minimize_ipopt
from dask import delayed, compute

import warnings
warnings.filterwarnings("ignore") # Not optimal as all warnings are suppressed

alpha = 2.016

def ismonotonic(
    events: np.ndarray
):
    # Checks if arrivals are monotonically increasing
    return np.all(np.diff(events) > 0)

@numba.jit(nopython=True)
def powerlaw(
    tau: np.ndarray,
    m: np.ndarray,
    beta: float,
    c: float,
    kappa: float,
    theta: float
):
    return kappa * (m ** beta) * (tau + c) ** (-(1 + theta))

def fit_MLE_UHP_pwl(
    events: np.ndarray,
    marks: np.ndarray,
    T: float,
    c: float,
    mu: float,
    guess: np.ndarray,
    bounds: tuple,
    solver: str
):
    """
    Description:
        Maximum-likelihood estimation (MLE)
        for univariate Hawkes process with power-law kernel
    Return:
        params_fit: (np.ndarray) - parameter estimates
        loglike: (float) - loglikelihood
    """
    
    if not ismonotonic(events):
        raise Exception('Event series is not monotonically increasing.')
        
    args = ((events, marks, T, c, mu),)
    
    if (solver=='trust-constr' or solver=='SLSQP' or solver=='L-BFGS-B'):
        res = optimize.minimize(loglikelihood_UHP_pwl,
                                guess, 
                                args=args,
                                method=solver, 
                                bounds=bounds,
                                tol=1e-6, 
                                options={'maxiter': 1e3})
        
    elif (solver=='ipopt'):
        res = minimize_ipopt(loglikelihood_UHP_pwl,
                             guess,
                             args=args, 
                             bounds=bounds,
                             tol=1e-6,
                             options={'maxiter': 1000})

    else:
        res = optimize.minimize(loglikelihood_UHP_pwl, 
                                guess, 
                                args=args,
                                method=solver,
                                tol=1e-6, 
                                options={'maxiter': 1e3})
        
    params_fit = res.x
    loglike = -res.fun
    
    return params_fit, loglike

# @numba.jit(nopython=True)
def loglikelihood_UHP_pwl(
    x: np.ndarray,
    args: tuple
):
    """
    Description:
        Log-likelihood function
        for univariate Hawkes process with power-law kernel
    Return:
        negative log-likelihood: (float)
    """

    events = args[0]
    marks = args[1]
    T = args[2]
    c = args[3]
    mu = args[4]
    
    beta = x[0]
    kappa = x[1]
    theta = x[2]
    
    log_sum = 0
    kern_sum = 0
    
    for i, t_i in enumerate(events):
        if i != 0:
             kern_sum = np.sum(powerlaw(tau=t_i - events[events<t_i], m=marks[:i], 
                                 kappa=kappa, 
                                 beta=beta,
                                 c=c,
                                 theta=theta
                                ))

        log_sum += np.log(mu + kern_sum)

    sub_term1 = (c ** (-theta)) / theta
    sub_term2 = (T + c - events) ** (-theta) / theta
    integral_kern_sum = kappa * np.dot((marks ** beta), (sub_term1 - sub_term2))

    return -(log_sum - mu * T - integral_kern_sum)

def rolling_window_pwl(
    events: np.ndarray,
    marks: np.ndarray,
    posts: np.ndarray,
    guess: np.ndarray,
    bounds: np.ndarray,
    solver: str,
    c: int,
    win_size: int
):
    """
    Description:
        Rolling window for events
    Return:
        return_list: (list) - list of [guess, p_fit, loglike, solver, counter]
    """
    
    counter = 0
    return_list = []
    end = win_size
    increase = int(win_size)
    start = 0

    while end < len(events):
        print(f'Start: {start} / {len(events)}')
        
        events_sec = events[start:end] - events[start]
        marks_sec = marks[start:end]
        posts_sec = posts[start:end]
        time_delta = events_sec[-1]
        
        mu = np.sum(posts_sec) / time_delta

        if np.sum(posts_sec) > 0: 
            try:
                p_fit, loglike = fit_MLE_UHP_pwl(
                    events=events_sec, 
                    marks=marks_sec,
                    T=time_delta,
                    c=c,
                    mu=mu,
                    guess=guess,
                    bounds=bounds,
                    solver=solver
                )

            except:
                p_fit = np.array([np.nan, np.nan, np.nan])
                loglike = np.nan

            return_list.append([guess, p_fit, loglike, solver, counter, mu, time_delta])
            start += increase
        end += increase
        counter += 1

    return return_list

def branching_ratio(
    guess: np.ndarray,
    c: int
):
    """
    Description:
        Calculate branching ratio for guess
    Return:
        branching coefficient: (float)
    """

    return guess[1] * ((alpha - 1)/(alpha - guess[0] - 1)) * (1 / (guess[2] * (c ** guess[2])))

def parallelize_fit_dask(
    fun: Callable,
    fun_branch: Callable,
    guess_size: int,
    events: np.ndarray,
    marks: np.ndarray,
    posts: np.ndarray,
    bounds: tuple,
    solver: str,
    c: int,
    win_size: int,
    n_run: int
):
    """
    Description:
        Parallelize maximum likelihood estimation
    Return:
        data_list: (list)
    """
    
    estimates_results = []
    
    np.random.seed(11111)
    
    for run_i in range(n_run):
        guess = np.random.uniform(size=guess_size)
        
        while (fun_branch(guess, c) > 1) and (any(guess <= 1e-3)):
            guess = np.random.uniform(size=guess_size)
        result_i = delayed(fun)(events, marks, posts, guess, bounds, solver, c, win_size)
        estimates_results.append(result_i)
    
    estimates_results = compute(*estimates_results, scheduler='distributed')

    data_list = [item for sublist in estimates_results for item in sublist]
    return data_list