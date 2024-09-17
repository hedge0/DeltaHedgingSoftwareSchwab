from math import log, sqrt, exp
from numba import njit

@njit
def calculate_delta(S, K, T, r, sigma, option_type='calls'):
    """
    Calculate the delta of an option using the Black-Scholes formula with custom normal_cdf.

    Parameters:
    - S (float): Current stock price.
    - K (float): Strike price.
    - T (float): Time to maturity (in years).
    - r (float): Risk-free interest rate (as a decimal).
    - sigma (float): Volatility of the underlying asset.
    - option_type (str, optional): 'calls' or 'puts'.

    Returns:
    - float: The delta of the option.
    """
    d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))

    if option_type == 'calls':
        delta = normal_cdf(d1)
    elif option_type == 'puts':
        delta = normal_cdf(d1) - 1
    else:
        raise ValueError("option_type must be 'calls' or 'puts'.")

    return delta

@njit
def calculate_gamma(S, K, T, r, sigma, option_type='calls'):
    """
    Calculate the gamma of an option using numerical differentiation.

    Parameters:
    - S (float): Current stock price.
    - K (float): Strike price.
    - T (float): Time to maturity (in years).
    - r (float): Risk-free interest rate (as a decimal).
    - sigma (float): Volatility of the underlying asset.
    - option_type (str, optional): 'calls' or 'puts'.

    Returns:
    - float: The gamma of the option.
    """
    h = 1e-4

    price_plus = barone_adesi_whaley_american_option_price(S + h, K, T, r, sigma, option_type)
    price = barone_adesi_whaley_american_option_price(S, K, T, r, sigma, option_type)
    price_minus = barone_adesi_whaley_american_option_price(S - h, K, T, r, sigma, option_type)

    gamma = (price_plus - 2 * price + price_minus) / (h * h)

    return gamma

@njit
def calculate_vega(S, K, T, r, sigma, option_type='calls'):
    """
    Calculate the vega of an option using numerical differentiation.

    Parameters:
    - S (float): Current stock price.
    - K (float): Strike price.
    - T (float): Time to maturity (in years).
    - r (float): Risk-free interest rate (as a decimal).
    - sigma (float): Volatility of the underlying asset.
    - option_type (str, optional): 'calls' or 'puts'.

    Returns:
    - float: The vega of the option.
    """
    h = 1e-4

    price_plus = barone_adesi_whaley_american_option_price(S, K, T, r, sigma + h, option_type)
    price_minus = barone_adesi_whaley_american_option_price(S, K, T, r, sigma - h, option_type)

    vega = (price_plus - price_minus) / (2 * h)

    return vega

@njit
def calculate_theta(S, K, T, r, sigma, option_type='calls'):
    """
    Calculate the theta of an option using numerical differentiation.

    Parameters:
    - S (float): Current stock price.
    - K (float): Strike price.
    - T (float): Time to maturity (in years).
    - r (float): Risk-free interest rate (as a decimal).
    - sigma (float): Volatility of the underlying asset.
    - option_type (str, optional): 'calls' or 'puts'.

    Returns:
    - float: The theta of the option.
    """
    h = 1e-5

    if T <= h:
        h = T / 2

    price_plus = barone_adesi_whaley_american_option_price(S, K, T + h, r, sigma, option_type)
    price_minus = barone_adesi_whaley_american_option_price(S, K, T - h, r, sigma, option_type)

    theta = (price_plus - price_minus) / (2 * h)

    return -theta

@njit
def calculate_rho(S, K, T, r, sigma, option_type='calls'):
    """
    Calculate the rho of an option using numerical differentiation.

    Parameters:
    - S (float): Current stock price.
    - K (float): Strike price.
    - T (float): Time to maturity (in years).
    - r (float): Risk-free interest rate (as a decimal).
    - sigma (float): Volatility of the underlying asset.
    - option_type (str, optional): 'calls' or 'puts'.

    Returns:
    - float: The rho of the option.
    """
    h = 1e-5

    price_plus = barone_adesi_whaley_american_option_price(S, K, T, r + h, sigma, option_type)
    price_minus = barone_adesi_whaley_american_option_price(S, K, T, r - h, sigma, option_type)

    rho = (price_plus - price_minus) / (2 * h)

    return rho

@njit
def erf(x):
    """
    Approximation of the error function (erf).

    Parameters:
    - x (float): The input value.

    Returns:
    - float: The calculated error function value.
    """
    a1, a2, a3, a4, a5 = (
        0.254829592,
        -0.284496736,
        1.421413741,
        -1.453152027,
        1.061405429,
    )
    p = 0.3275911

    x = abs(x)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * exp(-x * x))

    sign = 1 if x >= 0 else -1

    return sign * y

@njit
def normal_cdf(x):
    """
    Approximation of the cumulative distribution function (CDF) for a standard normal distribution.

    Parameters:
    - x (float): The input value.

    Returns:
    - float: The CDF value.
    """
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))

@njit
def barone_adesi_whaley_american_option_price(S, K, T, r, sigma, option_type='calls'):
    """
    Calculate the price of an American option using the Barone-Adesi Whaley model.

    Parameters:
    - S (float): Current stock price.
    - K (float): Strike price of the option.
    - T (float): Time to expiration in years.
    - r (float): Risk-free interest rate.
    - sigma (float): Implied volatility.
    - option_type (str, optional): Type of option ('calls' or 'puts'). Defaults to 'calls'.

    Returns:
    - float: The calculated option price.
    """
    M = 2 * r / sigma**2
    n = 2 * (r - 0.5 * sigma**2) / sigma**2
    q2 = (-(n - 1) - sqrt((n - 1)**2 + 4 * M)) / 2

    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

    if option_type == 'calls':
        BAW = S * normal_cdf(d1) - K * exp(-r * T) * normal_cdf(d2)
        if q2 < 0:
            return BAW
        S_critical = K / (1 - 1 / q2)
        if S >= S_critical:
            return S - K
        else:
            A2 = (S_critical - K) * (S_critical ** -q2)
            return BAW + A2 * (S / S_critical) ** q2
    elif option_type == 'puts':
        BAW = K * exp(-r * T) * normal_cdf(-d2) - S * normal_cdf(-d1)
        if q2 < 0:
            return BAW
        S_critical = K / (1 - 1 / q2)
        if S <= S_critical:
            return K - S
        else:
            A2 = (K - S_critical) * (S_critical ** -q2)
            return BAW + A2 * (S / S_critical) ** q2
    else:
        raise ValueError("option_type must be 'calls' or 'puts'.")

@njit
def calculate_implied_volatility_baw(option_price, S, K, r, T, option_type='calls', max_iterations=100, tolerance=1e-8):
    """
    Calculate the implied volatility using the Barone-Adesi Whaley model.

    Parameters:
    - option_price (float): Observed option price.
    - S (float): Current stock price.
    - K (float): Strike price of the option.
    - r (float): Risk-free interest rate.
    - T (float): Time to expiration in years.
    - option_type (str, optional): Type of option ('calls' or 'puts'). Defaults to 'calls'.
    - max_iterations (int, optional): Maximum number of iterations for the bisection method. Defaults to 100.
    - tolerance (float, optional): Convergence tolerance. Defaults to 1e-8.

    Returns:
    - float: The implied volatility.
    """
    lower_vol = 0.0001
    upper_vol = 2.0

    for _ in range(max_iterations):
        mid_vol = (lower_vol + upper_vol) / 2
        price = barone_adesi_whaley_american_option_price(S, K, T, r, mid_vol, option_type)

        if abs(price - option_price) < tolerance:
            return mid_vol

        if price > option_price:
            upper_vol = mid_vol
        else:
            lower_vol = mid_vol

        if upper_vol - lower_vol < tolerance and upper_vol >= 2.0:
            upper_vol *= 2.0

    return mid_vol
