import statistics
import numpy as np

from scipy import misc
from scipy.interpolate import InterpolatedUnivariateSpline, CubicSpline
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from patsy.highlevel import dmatrix
import statsmodels.api as sm
import matplotlib.pyplot as plt


def plot_with_f(x, y, f):
    plt.plot(x, y, '-')
    plt.plot(x, f(x), '--')
    plt.show()


def mean(values):
    return statistics.mean(values)


def stddev(values):
    return statistics.stdev(values)


def variance(values):
    return statistics.variance(values)


def get_linear_regression_slope(x, y):
    if type(x) == list:
        x = np.array(x)
    if type(y) == list:
        y = np.array(y)
    if x.shape != (len(x), 1):
        x = x.reshape(-1, 1)
    if y.shape != (len(y), 1):
        y = y.reshape(-1, 1)
    model = LinearRegression()
    model.fit(x, y)
    return model.coef_[0][0]


def derivative(f, x, n=1):
    return misc.derivative(f, x, n=n, dx=1e-6)


def get_univariate_spline_function(x, y):
    f = InterpolatedUnivariateSpline(x, y, check_finite=True)
    return f


def get_polynomial_regression_function(x, y, degree=3):
    polynomial_features = PolynomialFeatures(degree=degree)
    x_poly = polynomial_features.fit_transform(x)
    pol_reg = LinearRegression()
    pol_reg.fit(x_poly, y)
    return lambda X: pol_reg.predict(polynomial_features.transform(X))


def cubic_splines_function(x=None, y=None, number_of_knots=60):
    max_x = np.max(x).astype(np.float64)
    min_x = np.min(x).astype(np.float64)
    knot_size = (max_x - min_x) / number_of_knots
    knots = [str(min_x + (n * knot_size)) for n in range(number_of_knots)]
    str_knots = ','.join(knots)

    def dmatrix_lambda(x_parameter):
        return dmatrix(
            'bs(x, knots=({str_knots}), degree=3, include_intercept=False)'.format(str_knots=str_knots),
            {'x': x_parameter},
            return_type='dataframe'
        )

    fitted_model = sm.GLM(y, dmatrix_lambda(x)).fit()
    return CubicSpline(x.flatten(), fitted_model.predict(dmatrix_lambda(x))), [float(n) for n in knots]


"""
Now
"""


def profit_difference_percentage(origin, destination):
    return ((destination - origin) / origin) * 100


def to_profit(prices):
    profit = []
    last = None
    for price in prices:
        if last is None:
            profit.append(0)
        else:
            profit.append(profit_difference_percentage(last, price))
        last = price
    return profit
