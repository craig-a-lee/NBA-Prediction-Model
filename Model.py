import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

class Model:
    def __init__(self, features, test_size=0.2, random_state=42):
        self.features = features
        self.test_size = test_size
        self.random_state = random_state
        self.model = CatBoostRegressor(
            iterations=300,
            learning_rate=0.04,
            depth=6,
            l2_leaf_reg=3,
            loss_function='MAE',
            random_seed=self.random_state,
            verbose=0
        )
        self.mae = None
        self.stds = {}

    def train(self, df, target_col='PTS'):
        """
        Train the model
        :param df: dataframe to use for training
        :param target_col: column we'd like to predict
        :return: mean absolute error of trained model
        """
        X = df[self.features]
        y = df[target_col]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state
        )

        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        self.mae = mean_absolute_error(y_test, y_pred)
        binary_features = self.get_binary_features(df)
        numeric_features = [f for f in self.features if f not in binary_features]
        for feature in numeric_features:
            self.stds[feature] = X_train[feature].std()
        return self.mae

    def predict(self, row_df):
        """
        Predict from a single row (must match feature names).
        :param row_df: row to perform prediction with
        :return: prediction
        """
        prediction = self.model.predict(row_df[self.features])
        return prediction

    def is_binary(self, series):
        """
        Determines if a given feature is binary
        :param series: series to consider
        :return: bool representing whether feature is binary
        """
        unique_vals = series.dropna().unique()
        return len(unique_vals) == 2 and all(val in [0, 1] for val in unique_vals)

    def get_binary_features(self, df):
        """
        Finds all binary features
        :param df: dataframe to consider
        :return: list of binary features
        """
        binary_features = [col for col in self.features if self.is_binary(df[col])]
        return binary_features

    def simulate(self, row_df, constant_features=[], n = 100):
        """
        Perform a monte carlo simulation by making n predictions where varying levels of noise is added
        to the input
        :param row_df: contains
        :param constant_features: features we do not want to add noise to
        :param n: number of simulations
        :return: list of predictions
        """
        simulations = []
        for _ in range(n):
            noisy_input = row_df.copy()
            for feature in self.stds:
                if feature not in constant_features:
                    std = self.stds[feature]
                    noisy_input[feature] += np.random.normal(0, std)
            pred = self.model.predict(noisy_input)
            simulations.append(pred)
        return simulations