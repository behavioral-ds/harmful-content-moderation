import pandas as pd
import numpy as np
import time
from datetime import datetime
from dask.distributed import Client

from fit_hawkes_pwl import parallelize_fit_dask
from fit_hawkes_pwl import rolling_window_pwl
from fit_hawkes_pwl import branching_ratio

from dask.distributed import get_client

if __name__ == '__main__':
    
    # Dataset options
    name_i = 'americafirst'
    # name_i = 'climatescam'
    
    file_tw = '../data/twitter_' + name_i + '_hashtag.pkl'
    
    file_end ='.pkl'
    df = pd.read_pickle(file_tw)
    df = df.sort_values('created_at')
    df.reset_index(drop=True, inplace=True)
    df_d = df.drop_duplicates(subset="created_at", keep='first')
    # Boolean array of posts
    posts = df_d.status.values == 'post'

    data_list = []

    # Parameter of power-law distribution
    alpha = 2.016
    
    for idx, data_i in df.iterrows():
        time_i = data_i['created_at'].timestamp()
        
        if data_i['author_id'] != '':
            follower = data_i['author_followers']
        else:
            follower = round((alpha - 1) / (alpha - 2))
            # follower = 0
        
        data_list.append((time_i, follower))

    data_list.sort(key=lambda tup: tup[0])

    d = {x: 0 for x, _ in data_list}

    for name, num in data_list:
        d[name] += num

    output_list = list(map(tuple, d.items()))
    output_list.sort(key=lambda tup: tup[0])

    start_time = datetime.strptime('2022-07-01T00:00:00.000Z', "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

    events_offset = list(list(zip(*output_list))[0])
    events_s = np.array(events_offset) - np.array(start_time)

    # Impotant to replace 0 followers with 1 for log-likelihood computation
    marks = np.array(list(list(zip(*output_list))[1]))
    marks[marks == 0] = 1
    
    print(f'# of events: {len(events_s)}')
    print(f'# of posts: {np.sum(posts)}')

    beta_max = alpha - 1

    # Solver: 'trust-constr' or 'SLSQP' or 'L-BFGS-B' or 'ipopt'
    solver = 'trust-constr'
    win_size = 5000
    c = 30
    n_run = 50
    
    client = Client(n_workers=10)

    columns = ['guess', 'p_fit', 'loglike', 'solver', 'range', 'mu', 'time_delta']

    bounds = ((1e-6, beta_max), (1e-6, 2.5), (1e-6, 2.5))

    results = parallelize_fit_dask(
        fun=rolling_window_pwl,
        fun_branch=branching_ratio,
        guess_size=3,
        events=events_s,
        marks=marks,
        posts=posts,
        bounds=bounds,
        solver=solver,
        c=c,
        win_size=win_size,
        n_run=n_run
    )

    df = pd.DataFrame(results, columns=columns)
    time_str = time.strftime("%Y%m%d-%H%M%S")
    file_path = '../data/fits/pwl-fits-' + name_i + '-'+ str(win_size) + '-c-' + str(c) + '-' + time_str + '-' + solver + file_end
    df.to_pickle(file_path, protocol=5)