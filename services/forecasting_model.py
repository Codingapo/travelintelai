import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

class DemandForecaster:
    def __init__(self, sales_df):
        self.sales_df = sales_df
        self.model = LinearRegression()

    def prepare_data(self):
        # Convert booking_date to datetime
        self.sales_df['booking_date'] = pd.to_datetime(self.sales_df['booking_date'])
        
        # Group by date and sum revenue
        daily_sales = self.sales_df.groupby('booking_date')['revenue'].sum().reset_index()
        
        # Create a numeric feature for time (days since start)
        start_date = daily_sales['booking_date'].min()
        daily_sales['days_since_start'] = (daily_sales['booking_date'] - start_date).dt.days
        
        return daily_sales, start_date

    def train_and_predict(self, days_to_forecast=30):
        daily_sales, start_date = self.prepare_data()
        
        if len(daily_sales) < 2:
            return []

        X = daily_sales[['days_since_start']]
        y = daily_sales['revenue']
        
        self.model.fit(X, y)
        
        # Predict for future days
        last_day = daily_sales['days_since_start'].max()
        future_days = np.array(range(last_day + 1, last_day + 1 + days_to_forecast)).reshape(-1, 1)
        predictions = self.model.predict(future_days)
        
        forecast_results = []
        for i, pred in enumerate(predictions):
            forecast_date = start_date + timedelta(days=int(future_days[i][0]))
            forecast_results.append({
                'date': forecast_date.strftime('%Y-%m-%d'),
                'predicted_revenue': max(0, float(pred))
            })
            
        return forecast_results
