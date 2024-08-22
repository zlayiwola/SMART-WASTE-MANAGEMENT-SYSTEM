# Random Forest
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

# Handled missing values 
data.fillna(method='ffill', inplace=True)

# Feature scaling
scaler = MinMaxScaler()
numerical_cols = ['bin_level', 'gps_lat', 'gps_lon', 'air_quality', 'bin_distance']
data[numerical_cols] = scaler.fit_transform(data[numerical_cols])

# Created lagged features
# Considered creating multiple lags based on your data frequency and domain knowledge
data['bin_level_lag1'] = data['bin_level'].shift(1)
data['bin_level_lag2'] = data['bin_level'].shift(2)

# Created feature interactions
data['gps_lat_lon'] = data['gps_lat'] * data['gps_lon']

# Droped rows with missing values after creating lagged features
data.dropna(inplace=True)

# Split data into features and target
X = data.drop(['bin_level', 'timestamp'], axis=1)
y = data['bin_level']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model training
model = RandomForestRegressor(n_estimators=100, random_state=42)  # Replace with other models
model.fit(X_train, y_train)

# Model evaluation
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print('Mean Squared Error:', mse)


# Get feature importances
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]
feature_names = X.columns

# Plot feature importances
plt.figure(figsize=(12, 6))
plt.title("Feature Importances")
plt.bar(range(X.shape[1]), importances[indices], align="center")
plt.xticks(range(X.shape[1]), feature_names[indices], rotation=45)
plt.tight_layout()
plt.show()


# Predict future waste levels
future_data = X_test  # Replace with actual new data when available
future_predictions = model.predict(future_data)

# Ensure predictions are within percentage range
future_predictions = np.clip(future_predictions, 0, 100)

# Display predictions
print('Future Predictions: ', future_predictions)

# Convert predictions to percentages since that is what was used in my IoT
future_predictions_percentage = future_predictions * 100

# Display predictions
print('Future Predictions: ', future_predictions_percentage)

