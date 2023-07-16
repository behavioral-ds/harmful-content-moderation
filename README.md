# dsa-content-moderation

This repository contains code and data accompanying the publication "Digital Services Act: Estimate the Effectiveness of Moderating Harmful Online Content"

## Reference:
* TBD

## Repository Content:
This repository contains the following code scripts:
* `twitter-data-extraction.ipynb`
* `run_hawkes_pwl.py`
* `plot-contours.ipynb`
* `plot-social-media-dynamics-deletion.ipynb`

The following data and plots are also available:
* `data/twitter-climatescam-hashtag.csv` – contains tweet ids from Twitter associated with the hashtag #climatescam 
* `data/twitter-americafirst-hashtag.csv` – contains tweet ids from Twitter associated with the hashtag #americafirst or #americansfirst

Fig. 1 - Social Media Dynamics as Self-Exciting Point Process.

![Plot](plots/delete-plot.png)

Fig. 2 (a) - Reaction time $\Delta$ to achieve harm reduction of $\chi=20$\%.

![Plot](plots/delta-chi20p-deletion.png)

Fig. 2 (b) - Harm reduction $\chi$ when content is removed within $\Delta=24$ hours.

![Plot](plots/chi-delta24hour-deletion.png)

## License:
Both the dataset and the code in this repository are distributed under the General Public License v3 (GPLv3) license. You can find a copy of the license in the LICENSE file included in this repository. If you have any inquiries regarding licensing or any other questions, please feel free to reach out to us at Marian-Andrei@rizoiu.eu.
