import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
data = pd.read_csv('/Users/theuntold/Downloads/bin_dataaa.csv', parse_dates=['timestamp'])

# Handle missing values
data.fillna(method='ffill', inplace=True)  

# Convert categorical features
data['led_lights'] = data['led_lights'].map({'Green': 0, 'Red': 1, 'Blue': 2})
data['air_quality'] = data['air_quality'].map({'Poor': 1})

# Create time-based features
data['hour'] = data['timestamp'].dt.hour
data['dayofweek'] = data['timestamp'].dt.dayofweek
data['month'] = data['timestamp'].dt.month

# Exploratory Data Analysis (EDA)
plt.figure(figsize=(12, 6))
sns.lineplot(x='timestamp', y='bin_level', data=data)
plt.title('Bin Level Over Time')
plt.show()

# Bin level by hour of day
sns.lineplot(x='hour', y='bin_level', data=data)
plt.title('Bin Level by Hour of Day')
plt.show()


# Bin level by day of the week
sns.boxplot(x='dayofweek', y='bin_level', showmeans=True, data=data)
plt.title('Bin Level by Day of Week')
plt.show()


# Bin level by led lights indicators
sns.barplot(x='led_lights', y='bin_level', data=data)
plt.title('Bin Level by LED Light Color')
plt.show()

# Define a threshold for a full bin (e.g., 80% full)
full_bin_threshold = .80  # Adjust according to your data scale (e.g., 80% for percentages)

# Create a new column to identify full bins
data['is_full_bin'] = data['bin_level'] >= full_bin_threshold

# Count full bins per month
monthly_full_bins = data.groupby('month')['is_full_bin'].sum()

# Find the month with the highest number of full bins
month_with_max_full_bins = monthly_full_bins.idxmax()
max_full_bins_count = monthly_full_bins.max()

# Display the results
print("Month with the highest count of full bins:", month_with_max_full_bins)
print("Number of full bins in that month:", max_full_bins_count)

# Number of full bins per month
plt.figure(figsize=(10, 6))
sns.barplot(x=monthly_full_bins.index, y=monthly_full_bins.values)
plt.title('Number of Full Bins per Month')
plt.xlabel('Month')
plt.ylabel('Full Bin Count')
plt.xticks(range(12), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
plt.show()

# Correlation matrix
corr = data.corr()
sns.heatmap(corr, annot=True)
plt.title('Correlation Matrix')
plt.show()


