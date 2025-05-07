from dateutil.utils import today
import json

class Portfolio:
    DEFAULT_CUTOFF = '01/01/2025'

    # will eventually like this to be dynamic
    STARTERS = [
        "Trae Young", "Dyson Daniels", "Zaccharie Risacher", "Mouhamed Gueye", "Onyeka Okongwu",
        "Derrick White", "Jrue Holiday", "Jaylen Brown", "Jayson Tatum", "Kristaps Porzingis",
        "D'Angelo Russell", "Keita Johnson", "Cam Thomas", "Cameron Johnson", "Nic Claxton",
        "LaMelo Ball", "Nick Smith Jr.", "Josh Green", "Miles Bridges", "Mark Williams",
        "Josh Giddey", "Lonzo Ball", "Coby White", "Matas Buzelis", "Nikola Vucevic",
        "Darius Garland", "Donovan Mitchell", "Max Strus", "Evan Mobley", "Jarrett Allen",
        "Brandon Williams", "Max Christie", "Klay Thompson", "P.J. Washington", "Dwight Powell",
        "Jamal Murray", "Christian Braun", "Michael Porter Jr.", "Aaron Gordon", "Nikola Jokic",
        "Cade Cunningham", "Tim Hardaway Jr.", "Ausar Thompson", "Tobias Harris", "Jalen Duren",
        "Stephen Curry", "Brandin Podziemski", "John Butler III", "Jonathan Kuminga", "Draymond Green",
        "Fred VanVleet", "Jalen Green", "Amen Thompson", "Dillon Brooks", "Alperen Sengun",
        "Tyrese Haliburton", "Andrew Nembhard", "Aaron Nesmith", "Pascal Siakam", "Myles Turner",
        "James Harden", "Kris Dunn", "Norman Powell", "Kawhi Leonard", "Ivica Zubac",
        "Luka Doncic", "Austin Reaves", "Rui Hachimura", "LeBron James", "Jaxson Hayes",
        "Ja Morant", "Desmond Bane", "Jahmai Wells", "Jaren Jackson Jr.", "Zach Edey",
        "Tyler Herro", "Andrew Wiggins", "Bam Adebayo", "Kel'el Ware",
        "Damian Lillard", "Taurean Prince", "Kyle Kuzma", "Giannis Antetokounmpo", "Brook Lopez",
        "Mike Conley", "Anthony Edwards", "Jaden McDaniels", "Julius Randle", "Rudy Gobert",
        "CJ McCollum", "Trey Murphy III", "Zion Williamson", "Kelly Olynyk", "Yves Missi",
        "Jalen Brunson", "Mikal Bridges", "Josh Hart", "OG Anunoby", "Karl-Anthony Towns",
        "Shai Gilgeous-Alexander", "Luguentz Dort", "Jalen Williams", "Chet Holmgren", "Isaiah Hartenstein",
        "Cole Anthony", "Kentavious Caldwell-Pope", "Franz Wagner", "Paolo Banchero", "Wendell Carter Jr.",
        "Tyrese Maxey", "Quentin Grimes", "Kelly Oubre Jr.", "Paul George", "Andre Drummond",
        "Devin Booker", "Bradley Beal", "Kevin Durant", "Bol Bol", "Nick Richards",
        "Anfernee Simons", "Toumani Camara", "Deni Avdija", "Jerami Grant", "Donovan Clingan",
        "Malik Monk", "Zach LaVine", "DeMar DeRozan", "Keegan Murray", "Domantas Sabonis",
        "Chris Paul", "De'Aaron Fox", "Devin Vassell", "Harrison Barnes", "Bismack Biyombo",
        "Immanuel Quickley", "Gradey Dick", "RJ Barrett", "Scottie Barnes", "Jakob Poeltl",
        "Isaiah Collier", "Collin Sexton", "Lauri Markkanen", "John Collins", "Walker Kessler",
        "Jordan Poole", "Bilal Coulibaly", "Khris Middleton", "Keyonte George", "Alexandre Sarr"
    ]

    INITIAL_PORTFOLIO = [
        "Jaden McDaniels",
        "Stephen Curry",
        "Jaylen Brown",
        "Derrick White",
        "Shai Gilgeous-Alexander",
        "Nikola Jokic",
        "Michael Porter Jr.",
        "Jalen Brunson",
        "Karl-Anthony Towns",
        "Myles Turner",
        "Donovan Mitchell"
        "Evan Mobley",
        "Kawhi Leonard",
        "Jalen Green",
        "Anthony Edwards"
    ]

    def __init__(self, filename, data_fetcher, calculator, model):
        self.players = {}
        self.fetcher = data_fetcher
        self.calculator = calculator
        self.filename = filename
        self.load(filename)
        self.model = model

    def load(self, filename):
        """
        Loads the json in the given file into the player dictionary
        :param filename: file to load from
        """
        try:
            with open(filename, 'r') as f:
                # Check if the file is empty
                if f.read().strip():  # File contains data
                    f.seek(0)  # Move the cursor back to the start of the file
                    self.players = json.load(f)
                else:
                    self.players = {}  # Handle the empty file case
        except FileNotFoundError:
            self.players = {}  # Handle the case where the file doesn't exist
            self.save(self.players)

    def save(self, filename):
        """
        Saves player dictionary to file
        :param filename: where to save dictionary
        """
        with open(filename, 'w') as f:
            json.dump(self.players, f, indent=4)

    def add(self, player_name):
        """
        Add *player_name* to the portfolio
        :param player_name: player
        """
        self.load(self.filename)
        if player_name not in self.players:
            self.players[player_name] = {
                "ev": [],
                "actual": [],
                "predicted": [],
                "line": [],
                "date": []
            }
        self.save(self.filename)


    def remove(self, player_name):
        """
        Removes *player_name* from the portfolio
        :param player_name: player to remove
        """
        self.load(self.filename)
        if player_name in self.players:
            del self.players[player_name]
        self.save(self.filename)

    def get_player_next_event_date(self, player_name):
        """
        From the player dictionary, get the date of the next match
        :param player_name: player
        :return: date of next match or None
        """
        self.load(self.filename)
        if player_name in self.players:
            length = len(self.players[player_name]['date'])
            if length > 0:
                date = self.players[player_name]['date'][length - 1]
                return date
            return None
        return None

    def evaluate_player(self, player_name, category):
        """
        Evaluate a player's betting market based on predicted points for upcoming game
        :param player_name: player to evaluate
        :param category: statistical category
        """
        date = today().strftime("%m/%d/%Y")
        self.load(self.filename)


        # don't want to evaluate unless last event has passed
        next_event_date = self.get_player_next_event_date(player_name)
        if next_event_date:
            if next_event_date < date:
                stats = self.fetcher.get_player_stats_on_date(player_name, next_event_date)
                if stats is not None:
                    self.players[player_name]['actual'].append(stats[category])
                else:
                    # player did not play so lets remove predicted data to avoid confusion
                    self.players[player_name]['ev'].pop()
                    self.players[player_name]['predicted'].pop()
                    self.players[player_name]['line'].pop()
                    self.players[player_name]['date'].pop()
            else:
                return # already processed player for next event

        # get players line
        over_and_under = self.fetcher.get_player_props(player_name)

        if not over_and_under:
            print(f"{player_name} currently has no odds listed so can't be processed.")
            return

        # get row for player's input
        input = self.fetcher.create_player_model_input(player_name, over_and_under['date'])

        # make prediction
        prediction = self.model.predict(input)

        # calculate prob of hitting over and under
        p_over = self.calculator.probability_over(over_and_under['over']['line'], prediction, self.model.mae)
        p_under = self.calculator.probability_under(over_and_under['under']['line'], prediction, self.model.mae)

        # calculate ev
        if p_over > p_under:
            ev = self.calculator.expected_value(p_over, over_and_under['over']['price'])
        else:
            ev = self.calculator.expected_value(p_under, over_and_under['under']['price'])

        # update player's dictionary
        self.players[player_name]['ev'].append(ev)
        self.players[player_name]['predicted'].append(prediction)
        self.players[player_name]['line'].append(over_and_under['over']['line'])
        self.players[player_name]['date'].append(over_and_under['date'])
        self.save(self.filename)


    def evaluate_all(self, category):
        """
        Evaluate each player in dictionary
        :param category: statistical category
        """
        for player, info in self.players.items():
            self.evaluate_player(player, category)

    def get_most_consistent_players(self, cutoff_date=DEFAULT_CUTOFF, num_players=10, num_games=2,
                                    min_minutes=30, category='PTS', min_stat=0):
        """
        Finds the *num_players* most consistent players over the last *num_games* games based on
        a given category. Consistency is defined by standard deviation.
        :param num_players: top *num_players* most consistent players are considered
        :param num_games: number of games to track
        :param cutoff_date: all the player's last *num_games* games must be played after this date
        :param min_minutes: min number of minutes player must average
        :param category: statistical category
        :param min_stat: minimum player must average in given statistical category
        :return: player's top *num_players* most consistent players in given stat over time period
        """
        candidates = []
        for player in self.STARTERS:
            if player not in self.players:
                try:
                    stat_data = self.fetcher.get_last_x_stats_in_category(player, num_games, category, cutoff_date)
                    if stat_data:
                        minutes = self.fetcher.get_last_x_stats_in_category(player, num_games, 'MIN', cutoff_date)
                        stat_mean, stat_std = self.calculator.get_mean_std( stat_data )
                        minutes_mean, minutes_std = self.calculator.get_mean_std( minutes )
                        if stat_mean >= min_stat and minutes_mean >= min_minutes:
                            candidates.append((player, stat_mean, stat_std))

                except Exception as e:
                    print(e)

        candidates.sort(key=lambda x:x[2])
        return candidates[:num_players]


