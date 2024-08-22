# ARIMA FORECAST
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings('ignore')

# Load data
data = pd.read_csv('/Users/theuntold/Downloads/bin_dataaa.csv', parse_dates=['timestamp'])

# Resampled data to daily frequency and fill missing values
data.set_index('timestamp', inplace=True)
data = data['bin_level'].resample('D').mean().fillna(method='ffill')

# Checked for stationarity using the Augmented Dickey-Fuller test
result = adfuller(data)
print(f'ADF Statistic: {result[0]}')
print(f'p-value: {result[1]}')

# Since the data is not stationary, i differenced it. 
differenced_data = data.diff().dropna()

# Checked stationarity again
result_diff = adfuller(differenced_data)
print(f'ADF Statistic after differencing: {result_diff[0]}')
print(f'p-value after differencing: {result_diff[1]}')

# Fit the ARIMA model 
model = ARIMA(data, order=(1, 1, 1))
model_fit = model.fit()

# Summary of the model
print(model_fit.summary())

# Forecasted future values for 5 years (5 years = 365 * 5 = 1825 days)
forecast_steps = 365 * 5
forecast = model_fit.get_forecast(steps=forecast_steps)
forecast_index = pd.date_range(start=data.index[-1], periods=forecast_steps + 1, freq='D')[1:]
forecast_values = forecast.predicted_mean
forecast_ci = forecast.conf_int()

# Plot the data and the forecast
plt.figure(figsize=(14, 7))
plt.plot(data.index, data, label='Historical Bin Level')
plt.plot(forecast_index, forecast_values, color='red', label='Forecasted Bin Level')
plt.fill_between(forecast_index, forecast_ci.iloc[:, 0], forecast_ci.iloc[:, 1], color='pink', alpha=0.3)
plt.title('ARIMA Model Forecast of Waste Bin Levels Over 5 Years')
plt.xlabel('Date')
plt.ylabel('Bin Level')
plt.legend()
plt.grid(True)
plt.show()







