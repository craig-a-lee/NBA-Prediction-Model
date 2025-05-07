from dateutil.utils import today
from nba_api.stats.static import players
from nba_api.stats.static import teams
from nba_api.stats.endpoints import PlayerGameLogs
from nba_api.stats.endpoints import playergamelog, teamgamelog, leaguegamelog
from nba_api.stats.endpoints import ScoreboardV2
from nba_api.stats.endpoints import BoxScoreTraditionalV2, CommonTeamRoster, teamestimatedmetrics
import pandas as pd
import numpy as np
import requests
import json
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

class DataFetcher:
    load_dotenv()
    ODDS_API_KEY = os.getenv("API_KEY")
    BASE_URL = "https://api.the-odds-api.com/v4"
    DEFAULT_NUM_GAMES = 5
    DEFAULT_STAT = 'PTS'
    DEFAULT_CUTOFF = '01/01/2025'
    DEFAULT_BOOKIE = "draftkings"
    ODDS_FILE = "betting_data/odds.json"
    STAT_COLUMNS = ['PTS', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'MIN']
    FEATURES = ['HOME', 'REST', 'FORM_PTS', 'FORM_FG2A', 'FORM_FG3A',
                'FORM_FTA', 'FG2_PCT', 'FG3_PCT', 'FT_PCT', 'FORM_MIN',
                'OPP_PACE', 'OPP_DEF_RATING' ]
    def __init__(self, season="2024-25", season_type="Playoffs"):
        self.season = season
        self.season_type = season_type

    def get_player_stats_on_date(self, player_name, game_date):
        """
        Returns a player's traditional box score stats for a given date
        :param player_name: full name of player
        :param game_date: date of the game
        :return player's stat-line as a dict, or None if no data found
        """
        # Get scoreboard (contains game IDs)
        scoreboard = ScoreboardV2(game_date=game_date)
        game_ids = scoreboard.game_header.get_data_frame()['GAME_ID'].tolist()

        player_id = self.get_player_id(player_name)

        # Search each game for the player
        for game_id in game_ids:
            time.sleep(0.6)  # avoid rate-limiting
            boxscore = BoxScoreTraditionalV2(game_id=game_id)
            player_stats = boxscore.player_stats.get_data_frame()
            match = player_stats[player_stats['PLAYER_ID'] == player_id]
            if not match.empty:
                return match.iloc[0].to_dict()

        print(f"No stat-line found for {player_name} on {game_date}.")
        return None

    def get_player_id(self, player_name):
        """
        Fetches a player's unique id in npa_api based on name
        :param player_name: player to find id for
        :return: player's id number or None if player not found
        """
        player_dict = players.find_players_by_full_name(player_name)
        if not player_dict:
            print(f"Player '{player_name}' not found.")
            return None

        player_id = player_dict[0]['id']
        return player_id

    def calculate_averages(self, logs):
        """
        Calculate_averages calculates a players averages
        :param logs: game logs with statistical recordings
        :return: total/gps for each category
        """
        gp = len(logs)
        if gp == 0:
            return "Game logs are empty"
        avg_stats = logs[self.STAT_COLUMNS].mean().to_dict()
        return avg_stats

    def get_last_x_games_averages(self, player_name, num_games=5):
        """
        get_last_x_games_averages calculates players averages of last x games
        :param player_name: player
        :param num_games: number of games
        :return: a df with players average stats over last x games
        """
        # Fetch game logs for the current season
        last_x_games = self.get_last_x_game_logs(player_name, num_games=5)

        # Select key stats
        per_game_averages = self.calculate_averages(last_x_games)
        return per_game_averages

    def get_last_x_game_logs(self, player_name, num_games=DEFAULT_NUM_GAMES, cutoff_date=DEFAULT_CUTOFF ):
        """
        get_last_x_game_logs fetches a player's game logs for last *num_games* games
        :param player_name: player to find logs for
        :param num_games: number of games to consider
        :param cutoff_date: only consider games played no or after this day
        :return: player's last *num_games* game logs as df or None
        """
        player_id = self.get_player_id(player_name)
        game_logs = PlayerGameLogs(player_id_nullable=player_id, season_nullable=self.season, season_type_nullable=self.season_type)
        stats_df = game_logs.get_data_frames()[0]

        if stats_df.empty:
            print(f"No game data available for {player_name} in {self.season}.")
            return None

        # Only include games since cutoff_date
        stats_df['GAME_DATE'] = pd.to_datetime(stats_df['GAME_DATE'])
        stats_df = stats_df[stats_df['GAME_DATE'] >= cutoff_date]

        # Sort by most recent game and get the last X games
        last_x_games = stats_df.head(num_games)

        if len(last_x_games) < num_games:
            print(f"{player_name} has not played enough games since {cutoff_date}.")
            return None

        return last_x_games

    def get_last_x_stats_in_category(self, player_name, num_games=DEFAULT_NUM_GAMES, stat=DEFAULT_STAT, cutoff_date=DEFAULT_CUTOFF):
        """
        Get players last x recordings of a statistical category
        :param player_name: player
        :param num_games: number of games to consider
        :param stat: statistical category
        :param cutoff_date: only consider games played no or after this day
        :return: stat recordings as Series or None
        """
        logs = self.get_last_x_game_logs(player_name, num_games, cutoff_date)
        if logs is not None and stat in logs.columns.tolist():
            return logs[stat]
        return None


    def get_nba_teams_playing_on_date(self, date):
        """
        Get teams playing on a given day
        :param date: date to query for
        :return: list of team's playing
        """
        scoreboard = ScoreboardV2(game_date=date)

        nba_teams = teams.get_teams()
        team_id_map = {team['id']: team['full_name'] for team in nba_teams}

        # Get game headers
        games = scoreboard.game_header.get_dict()['data']

        # Extract teams playing
        matchups = []
        for game in games:
            home_team_id = game[6]  # HOME_TEAM_ID
            away_team_id = game[7]  # VISITOR_TEAM_ID
            home_team = team_id_map.get(home_team_id, f"Unknown({home_team_id})")
            away_team = team_id_map.get(away_team_id, f"Unknown({away_team_id})")
            matchups += [home_team, away_team]

        return matchups

    def get_team_id(self, team_name):
        """
        get_team fetches a player's id in nba_api based on name
        :param team_name: team to search for
        :return: team's id
        """
        teams_info = teams.get_teams()
        team = next((team for team in teams_info if team['full_name'] == team_name), None)
        return team['id']

    # private
    def get_upcoming_events(self, sport_key="basketball_nba", regions="us"):
        """
        Fetch upcoming events for a given sport.
        """
        url = f"{self.BASE_URL}/sports/{sport_key}/events"
        params = {
            "regions": regions,
            "apiKey": self.ODDS_API_KEY
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching events: {response.status_code} {response.text}")
        return response.json()

    def extract_opponent(self, row):
        """
        Given a row, extract the opponent of the team we're interested in
        :param row: contains matchup information
        :return: team of interest or None if not available
        """
        parts = row['MATCHUP'].split(' ')
        if '@' in parts:
            return parts[-1]
        elif 'vs.' in parts:
            return parts[-1]
        return None

    def extract_home(self, row):
        """
        Given a matchup, extract the team we're interested in, "home" here refers to that team
        :param row: contains matchup information
        :return: team of interest or None if not available
        """
        parts = row['MATCHUP'].split(' ')
        if '@' in parts:
            return parts[0]
        elif 'vs.' in parts:
            return parts[0]
        return None

    def get_opponent_def_rating_avg(self, opponent_id, game_date, num_games):
        """
        Calculate the opponent's average of their defensive rating in the last few games
        :param opponent_id: id of opponent
        :param game_date: date of game
        :param num_games: number of games to consider
        :return: calculated defensive rating or None if data is missing
        """
        game_logs = teamgamelog.TeamGameLog(team_id=opponent_id, season='2024-25').get_data_frames()[0]

        game_logs['GAME_DATE'] = pd.to_datetime(game_logs['GAME_DATE'])

        past_games = game_logs[game_logs['GAME_DATE'] < game_date]

        if not past_games.empty:
            games = past_games.tail(num_games)
            avg_def_rating = games['DEF_RATING'].mean()
            return avg_def_rating
        else:
            return None

    def fetch_opponent_def_rating(self, row):
        """
        Calculate the opponent's average of their defensive rating in the last few games
        :param row: contains matchup information
        :return: calculated defensive rating or None if data is missing
        """
        return self.get_opponent_def_rating_avg(row['OPP_TEAM_ID'], row['GAME_DATE'])


    def create_player_dataset(self, player_name, num_games):
        """
        Creates dataset for model training and saves it in csv
        :param player_name is the player we're creating the data for
        :param num_games is the number of games to be used in rolling average
        :returns df of player data with class' features or None if some data is not available
        """
        player_id = self.get_player_id(player_name)
        games = playergamelog.PlayerGameLog(player_id=player_id, season=self.season).get_data_frames()[0]
        games['OPP_TEAM_ABBR'] = games.apply(self.extract_opponent, axis=1)
        games['TEAM_ABBR'] = games.apply(self.extract_home, axis=1)
        teams_dict = {team['abbreviation']: team['id'] for team in teams.get_teams()}
        games['TEAM_ID'] = games['TEAM_ABBR'].map(teams_dict)
        games['OPP_TEAM_ID'] = games['OPP_TEAM_ABBR'].map(teams_dict)

        # Ensure games are in ascending order
        games['GAME_DATE'] = pd.to_datetime(games['GAME_DATE'])
        games = games.sort_values('GAME_DATE').reset_index(drop=True)


        games['FORM_PTS'] = games['PTS'].shift(1).rolling(window=num_games).mean()
        games['FORM_FG3A'] = games['FG3A'].shift(1).rolling(window=num_games).mean()
        games['FORM_FG3M'] = games['FG3M'].shift(1).rolling(window=num_games).mean()
        games['FORM_FTA'] = games['FTA'].shift(1).rolling(window=num_games).mean()
        games['FORM_FTM'] = games['FTM'].shift(1).rolling(window=num_games).mean()
        games['FG2A'] = games['FGA'] - games['FG3A']
        games['FG2M'] = games['FGM'] - games['FG3M']
        games['FORM_FG2A'] = games['FG2A'].shift(1).rolling(window=num_games).mean()
        games['FORM_FG2M'] = games['FG2M'].shift(1).rolling(window=num_games).mean()
        games['FORM_MIN'] = games['MIN'].shift(1).rolling(window=num_games).mean()
        games['REST'] = games['GAME_DATE'].diff().dt.days

        games = games.dropna()
        games["FG2_PCT"] = games.apply(lambda row: (row["FORM_FG2M"] / row["FORM_FG2A"]) if row["FORM_FG2A"] != 0 else 0, axis=1)
        games["FG3_PCT"] = games.apply(lambda row: (row["FORM_FG3M"] / row["FORM_FG3A"]) if row["FORM_FG3A"] != 0 else 0, axis=1)
        games["FT_PCT"] = games.apply(lambda row: (row["FORM_FTM"] / row["FORM_FTA"]) if row["FORM_FTA"] != 0 else 0, axis=1)

        metrics_df = teamestimatedmetrics.TeamEstimatedMetrics(season=self.season).get_data_frames()[0]

        # Only focusing on opponent def rating and pace since pace will always be the same for player's team
        metrics_df_team = metrics_df[['TEAM_ID', 'E_DEF_RATING', 'E_PACE']]
        metrics_df_team = metrics_df_team.rename(columns={'TEAM_ID': 'OPP_TEAM_ID', 'E_DEF_RATING': 'OPP_DEF_RATING', 'E_PACE': 'OPP_PACE'})

        games = games.merge(metrics_df_team, on=['OPP_TEAM_ID' ], how='left')

        games['HOME'] = games['MATCHUP'].apply(lambda x: 1 if '@' not in x else 0)

        columns = self.FEATURES + ['PTS']
        games_final = games[columns]
        games_final.to_csv("player_data/" + player_name + '.csv', index=False)
        time.sleep(1)
        return games_final

    # private
    def get_event_odds(self, sport_key, event_id, markets="player_points", regions="us"):
        """
        Fetches odds for a specific event, including player props from OddsAPI
        :param sport_key refers to the sport we're interested in
        :param event_id is id of the event we're querying
        :param markets refers to the statistical category
        :param regions
        :returns json result of query
        """
        url = f"{self.BASE_URL}/sports/{sport_key}/events/{event_id}/odds"
        params = {
            "markets": markets,
            "regions": regions,
            "apiKey": self.ODDS_API_KEY
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching event odds: {response.status_code} {response.text}")
        return response.json()

    def get_team_estimated_metric(self, team_name):
        """
        Return estimated team metrics
        :param team_name: name of team to query for
        :return: df containing teams estimating metrics
        """
        metrics_df = teamestimatedmetrics.TeamEstimatedMetrics(season=self.season).get_data_frames()[0]
        time.sleep(1)
        return metrics_df[metrics_df['TEAM_NAME'] == team_name]

    def get_team_players(self, team_name):
        """
        Find the team ID from the team name
        :param team_name: team to query for
        :return: team id string or None
        """
        nba_teams = teams.get_teams()
        team = next((t for t in nba_teams if t['full_name'].lower() == team_name.lower()), None)

        if not team:
            print(f"Team '{team_name}' not found.")
            return None

        team_id = team['id']

        roster = CommonTeamRoster(team_id=team_id, season=self.season)
        players = roster.common_team_roster.get_dict()['data']

        player_names = [player[3] for player in players] # Column 3 contains names
        time.sleep(1)
        return player_names

    def get_players_to_team_playing_on_date(self, date):
        """
        Creates mapping from player to team on a given date
        :param date: to query for
        :return: dict of player name to team name
        """
        player_to_team_map = {}
        teams_playing = self.get_nba_teams_playing_on_date(date)
        for team in teams_playing:
            players = set(self.get_team_players(team))
            for player in players:
                player_to_team_map[player] = team
        time.sleep(1)
        return player_to_team_map

    def create_player_model_input(self, player_name, date, num_games=5):
        """
        Create an input for a machine learning model based on class' features
        :param player_name: player to query for
        :param date: used to get matchup information
        :param num_games: number of games to use in rolling averages
        :return: input for machinine learning model as df or None if data is not available
        """
        teams_playing = self.get_nba_teams_playing_on_date(date)
        home_teams = teams_playing[::2]
        player_to_team_map = self.get_players_to_team_playing_on_date(date)
        if player_name not in player_to_team_map:
            return None
        team = player_to_team_map[player_name]
        input_row = {}
        new_features = ['FORM_FGM', 'FORM_FGA', 'FORM_FG3M', 'FORM_FTM' ] + self.FEATURES
        for stat in new_features:
            # Calculate average
            if "FORM" in stat:
                split_stat = stat.split("_")
                if split_stat[-1] != "FG2A":
                    data = self.get_last_x_stats_in_category(player_name, stat=split_stat[-1], num_games=num_games)
                    if data is not None:
                        input_row[stat] = np.mean(data)
                    else:
                        return None
            elif stat == "HOME":
                input_row['HOME'] = 1 if team in home_teams else 0
            elif "OPP" in stat:
                index = teams_playing.index(team)
                if index % 2 == 0:
                    opp = teams_playing[index + 1]
                else:
                    opp = teams_playing[index - 1]
                metrics_df = self.get_team_estimated_metric(opp)
                def_rating = metrics_df['E_DEF_RATING'].iloc[0]
                pace = metrics_df['E_PACE'].iloc[0]
                input_row['OPP_PACE'] = pace
                input_row['OPP_DEF_RATING'] = def_rating
                break

        logs = self.get_last_x_game_logs(player_name, num_games=1, )
        if logs is not None:
            logs['GAME_DATE'] = pd.to_datetime(logs['GAME_DATE'])
            last_played = logs['GAME_DATE'].iloc[0]
            rest = datetime.strptime(date, "%m/%d/%Y") - last_played
            input_row['REST'] = rest.days
        else:
            return None
        df = pd.DataFrame([input_row])
        df["FORM_FG2A"] = df["FORM_FGA"] - df["FORM_FG3A"]
        df["FORM_FG2M"] =df["FORM_FGM"] - df["FORM_FG3M"]
        df["FG2_PCT"] = df.apply(lambda row: (row["FORM_FG2M"] / row["FORM_FG2A"]) if row["FORM_FG2A"] != 0 else 0, axis=1)
        df["FG_PCT"] = df.apply(lambda row: (row["FORM_FGM"] / row["FORM_FGA"]) if row["FORM_FGA"] != 0 else 0, axis=1)
        df["FG3_PCT"] = df.apply(lambda row: (row["FORM_FG3M"] / row["FORM_FG3A"]) if row["FORM_FG3A"] != 0 else 0, axis=1)
        df["FT_PCT"] = df.apply(lambda row: (row["FORM_FTM"] / row["FORM_FTA"]) if row["FORM_FTA"] != 0 else 0, axis=1)
        df = df[self.FEATURES]
        time.sleep(1)
        return df

    # private
    def fetch_player_props(self, odds, market_key="player_points"):
        """
        Fetches all props available for players with upcoming matches from betting exchanges
        :param odds: dict containing player odds
        :param market_key: statistical category we're interested in
        :return: dict containing players' prop information
        """
        lines = {}
        for bookmaker in odds.get("bookmakers", []):
            if bookmaker["key"] != "draftkings":
                continue
            for market in bookmaker.get("markets", []):
                if market["key"] != market_key:
                    continue
                for outcome in market.get("outcomes", []):
                    player = outcome.get("description")
                    name = outcome.get("name").lower()  # 'over' or 'under'
                    line = outcome.get("point")
                    price = outcome.get("price")
                    time = odds.get("commence_time")
                    event_date = (datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)).strftime("%m/%d/%Y")
                    if player not in lines:
                        lines[player] = {}
                        lines[player]["date"] = event_date
                    lines[player][name] = {
                        "line": line,
                        "price": price
                    }
        return lines

    def update_odds_file(self):
        """
        Update the file containing the player's odds to contain the most up-to-date odds
        """
        overall = {}
        events = self.get_upcoming_events()
        for event in events:
            event_id = event['id']
            odds = self.get_event_odds(sport_key="basketball_nba", event_id=event_id)
            lines = self.fetch_player_props(odds)
            overall = overall | lines
        # Write data to the file
        with open(self.ODDS_FILE, 'w') as json_file:
            json.dump(overall, json_file, indent=2)

    # private
    def check_last_odds_file_update(self):
        """
        Check the date of the last odds file update
        :return: bool indicating whether date of last update is the same as current date
        """
        today_date = today()
        today_date = today_date.strftime('%Y-%m-%d')

        # Get the last modification time
        last_modified_time = os.path.getmtime(self.ODDS_FILE)

        last_modified_date = time.strftime('%Y-%m-%d', time.localtime(last_modified_time))
        return last_modified_date != today_date

    def get_all_player_props(self):
        """
        Returns dict of all available player probs
        :return: dict of all player props in odds file
        """
        if self.check_last_odds_file_update():
            self.update_odds_file()
        with open(self.ODDS_FILE, 'r') as json_file:
            data = json.load(json_file)
            return data

    def get_player_props(self, player_name):
        """
        Get player's over/under information for his upcoming match
        :param player_name: player to query for
        :return: dict containing player's prop information or None
        """
        if self.check_last_odds_file_update():
            self.update_odds_file()

        with open(self.ODDS_FILE, 'r') as json_file:
            data = json.load(json_file)
            if player_name in data:
                return data[player_name]
            print(f"{player_name} currently has no odds listed.")
            return None