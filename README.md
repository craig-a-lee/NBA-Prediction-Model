# NBA Player Performance Model

The goal of this project is to use machine learning methods to predict player's statisitcal outcomes, relative to their betting lines on DraftKings. This is achieved by training a CatBoostRegressor model on a union of player datasets from previous seasons. The input to the model consists of player's statistical averages over his last few games, as well as, features such as home/away, days of rest, opponent defensive rating etc. A certain number of Monte Carlo simulations are then carried out in order to predict the likeliness of the player hitting the over or under.

Th tehcnical stack
- Python
- Pandas
- Matplot
- Numpy
- Odds API
- NBA API 
