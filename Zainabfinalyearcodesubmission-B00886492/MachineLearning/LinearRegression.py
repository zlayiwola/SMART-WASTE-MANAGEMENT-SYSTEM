# Linear Regression
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.metrics import mean_squared_error

# Load the data
data = pd.read_csv('/Users/theuntold/Downloads/bin_dataaa.csv', parse_dates=['timestamp'])

# Handles missing values
data.fillna(method='ffill', inplace=True)

# Encode categorical variables
data['led_lights'] = data['led_lights'].map({'Green': 0, 'Red': 1, 'Blue': 2})
data['air_quality'] = data['air_quality'].map({'Poor': 1})

# Feature engineering
data['hour'] = data['timestamp'].dt.hour
data['dayofweek'] = data['timestamp'].dt.dayofweek
data['month'] = data['timestamp'].dt.month

# Scales numerical features
scaler = MinMaxScaler()
numerical_cols = ['bin_level', 'gps_lat', 'gps_lon', 'bin_distance']
data[numerical_cols] = scaler.fit_transform(data[numerical_cols])

# Prepares the data for modeling
X = data.drop(['bin_level', 'timestamp'], axis=1)
y = data['bin_level']

# Splits the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Creates a Linear Regression model
model = LinearRegression()

# Fit the model to the training data
model.fit(X_train, y_train)

# Make predictions on the test data
y_pred = model.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
print("Mean Squared Error on Test Data:", mse)

# Prepare new data for prediction
# Here I assume that I have a new dataset similar to the original one.
# For demonstration, I will use X_test as the new data.
X_new = X_test.copy() 

# Make predictions on new data
y_pred_new = model.predict(X_new)

# Reverse the scaling (e.g., to get predictions in the original scale of 'bin_level'):
y_pred_new_original_scale = scaler.inverse_transform(
    np.concatenate([y_pred_new.reshape(-1, 1), X_new[numerical_cols[1:]]], axis=1)
)[:, 0]

# Display predictions
print("Predictions on New Data (scaled):", y_pred_new)
print("Predictions on New Data (original scale):", y_pred_new_original_scale)








