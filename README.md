# NBA Player Performance Model

The goal of this project is to use machine learning methods to predict player's statisitcal outcomes, relative to their betting lines on DraftKings. This is achieved by training a CatBoostRegressor model on a union of player datasets from previous seasons. The input to the model consists of player's statistical averages over his last few games, as well as, features such as home/away, days of rest, opponent defensive rating etc. A certain number of Monte Carlo simulations are then carried out in order to predict the likeliness of the player hitting the over or under.


Setting up Environment:

1. You will need to request an API from [the odds api](https://the-odds-api.com/) for draftking queries
2. Place this in your .env file. API_KEY="{KEY}"
3. Set up a virual environment
4. Run pip install nba_api numpy pandas catboost matplotlib scipy sklearn dotenv
   
Necessary Tech
- Python >= 3.10  
