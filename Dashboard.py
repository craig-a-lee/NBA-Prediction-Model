import numpy as np
import matplotlib.pyplot as plt

class Dashboard():
    def __init__(self):
        pass

    def plot_prediction_distribution(self, predictions, betting_line, title="Monte Carlo Simulation of Player Points"):
        """
        Plot the distribution of predicted points with shaded regions for over/under
        relative to the betting line.
        :param: predictions: array of predicted values
        :param: betting_line: betting line to compare predictions against.
        :param: title: title of the plot
        """
        predictions = np.array(predictions).flatten()
        over_prob = (predictions > betting_line).mean()
        under_prob = 1 - over_prob

        counts, bins, patches = plt.hist(predictions, bins=30, alpha=0.7,
                                         label='Simulated Points', edgecolor='black')

        # Shade histogram bars based on relation to betting line
        for bin_left, bin_right, patch in zip(bins[:-1], bins[1:], patches):
            if bin_right <= betting_line:
                patch.set_facecolor('skyblue')  # Under
            elif bin_left >= betting_line:
                patch.set_facecolor('salmon')  # Over
            else:
                patch.set_facecolor('gray')  # Crossing line

        plt.axvline(betting_line, color='red', linestyle='--', label=f'Betting Line: {betting_line}')
        plt.text(betting_line + 0.5, max(counts) * 0.9, f'Over: {over_prob:.1%}', color='darkred')
        plt.text(betting_line - 6, max(counts) * 0.9, f'Under: {under_prob:.1%}', color='darkblue')

        plt.title(title)
        plt.xlabel('Predicted Points')
        plt.ylabel('Frequency')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()