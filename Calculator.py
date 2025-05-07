import numpy as np
from scipy.stats import norm

class Calculator:
    def get_mean_std(self, values):
        """
        Returns mean and standard deviation of a list of numbers
        :param values: series of numbers
        :return: mean and std as tuple
        """
        mean = np.mean(values)
        std = np.std(values, ddof=1)
        return mean, std

    def probability_over(self, line, mean, std):
        """
        P(X > line) using normal distribution
        :param line: betting line
        :param mean: given average
        :param std: given standard deviation
        :return: probability of hitting over
        """
        if std == 0:
            return 1.0 if mean > line else 0.0
        return 1 - norm.cdf(line, loc=mean, scale=std)

    def probability_under(self, line, mean, std):
        """
        P(X > line) using normal distribution
        :param line: betting line
        :param mean: given average
        :param std: given standard deviation
        :return: probability of hitting under
        """
        return norm.cdf(line, loc=mean, scale=std)

    def expected_value(self, prob_win, odds_decimal):
        """
        EV = (prob_win * odds) - (1 - prob_win)
        :param prob_win: probability of outcome
        :param odds_decimal: decimal multiplier of winning outcome
        :return: expected value
        """
        return (prob_win * odds_decimal) - 1

    def expected_payout(self, ev, stake=1.0):
        """
        EV * stake
        :param ev: expected value
        :param stake: amount wagered
        :return: expected payout
        """
        return stake + (ev * stake)