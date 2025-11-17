# NBA Player Performance Model

The goal of this project is to use machine learning methods to predict player's statisitcal outcomes, relative to their betting lines on DraftKings. This is achieved by training a CatBoostRegressor model on a union of player datasets from previous seasons. The input to the model consists of player's statistical averages over his last few games, as well as, features such as home/away, days of rest, opponent defensive rating etc. A certain number of Monte Carlo simulations are then carried out in order to predict the likeliness of the player hitting the over or under.

Setting up Environment:

1. You will need to request an API from [the odds api](https://the-odds-api.com/) for draftking queries
2. Place this in your .env file. API_KEY="{KEY}"
3. Set up a virual environment
4. Run pip install nba_api numpy pandas catboost matplotlib scipy sklearn dotenv

Necessary Tech
- Python 3.10 or Python 3.11 - Catboost does not work on other Python models

 Calculator
- Includes functions for calculating probability under or over, expected values, expected payout

 DataFetcher
 - Ingests nba data using the [nba_api](https://github.com/swar/nba_api)
 - Handles cleaning of data and preparation of features

Model
- Features: FG2_PCT, FG3_PCT, FORM_FG2A, FORM_FG3A, FORM_FTA, FORM_MIN, FORM_PTS, FT_PCT, HOME, OPP_DEF_RATING, OPP_PACE, REST
- Given the list of features above, can train a CatBoost model for point prediction

Dashboard
- Plots Monte Carlo Simulation of Player Points
- Frequency Vs Predicted Points Bar Graph which; also shows Betting line

Portfolio
- Manages json portfolio where you can keep track of player's ev, actual points, predicted points, line and date

Main

- refresh_data_files: Takes in a list of players and number of games (used to create the form features) and creates a player dataset
- visualize_player_outcomes: Takes in a player name and produces a dashboard using the Dashboard Class
- get_highest_evs_tonight: Runs the model for every player playing on the run date and returns the top 5 with the highest EV based on their betting line
