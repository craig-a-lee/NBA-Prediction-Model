from Calculator import Calculator
from Dashboard import Dashboard
from DataFetcher import DataFetcher
from Model import Model
from Portfolio import Portfolio
import pandas as pd
import os

# Create data fetcher
fetcher = DataFetcher()

# Create calculator
calculator = Calculator()

# Create dashboard
dashboard = Dashboard()

all_files = os.listdir("player_data")
csv_files = [f for f in all_files if f.endswith('.csv')]

# Create dataset
df = pd.DataFrame()
for file in csv_files:
    df = pd.concat([df, pd.read_csv("player_data/" + file)])

# Create model
n = 1000 # number of simulations
model = Model(fetcher.FEATURES)
model.train(df)

# Create portfolio
filename = "betting_data/portfolio.json"
portfolio = Portfolio(filename, fetcher, calculator, model)

# Create odds dict
odds_dict = fetcher.get_all_player_props()

def refresh_data_files(players, num_games):
    """
    Creates data sets
    :param players: players to create dataframes for
    """
    for player in players:
        fetcher.create_player_dataset(player, num_games)

def visualize_player_outcomes(player="Stephen Curry"):
    """
    Visualizes the outcomes of a monte carlo simulation for the player's upcoming game
    :param player: player to consider
    """
    info = fetcher.get_player_props(player)
    if info is not None:
        date = info['date'] # %mm/%dd/%yyyy
        line = info['over']['line']
        input = fetcher.create_player_model_input(player, date)
        preds = model.simulate(input, ['REST'], n)
        dashboard.plot_prediction_distribution(preds, line, player)

def get_highest_evs_tonight(certainty_line=0.9):
    """
    Gets the players with the highest ev tonight, considering all players with available props
    :return: df of players, containing prediction information
    """
    results = {'PLAYER': [], 'LINE': [], 'OUTCOME': [], 'P_OUTCOME': [], 'EV': []}
    for player in odds_dict:
        info = fetcher.get_player_props(player)
        date = info['date']
        line = info['over']['line']
        over_price = info['over']['price']
        under_price = info['under']['price']
        input = fetcher.create_player_model_input(player, date)
        if input is not None:
            preds = model.simulate(input, ['REST'], n)
            over_count = 0
            for pred in preds:
                if pred > line:
                    over_count += 1
            p_over = over_count / n
            p_under = 1 - p_over
            over_ev = (p_over * (1  - over_price)) - (1 - p_over)
            under_ev = (p_under * (1 - under_price)) - (1 - p_under)
            found = False
            if p_over > certainty_line:
                better_ev = over_ev
                better_bet = 'OVER'
                p_outcome = p_over
                found = True
            elif p_under > certainty_line:
                found = True
                better_ev = under_ev
                better_bet = 'UNDER'
                p_outcome = p_under
            else:
                continue
            if found:
                results['PLAYER'] += [player]
                results['LINE'] = [line]
                results['OUTCOME'] += [better_bet]
                results['P_OUTCOME'] += [p_outcome]
                results['EV'] += [better_ev]
    df = pd.DataFrame(results)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(df)

if __name__=="__main__":
    visualize_player_outcomes("Rudy Gobert")
    # refresh_data_files()
    # get_highest_evs_tonight()
