import pandas as pd
import numpy as np

class AnomalyDetector:
    def __init__(self, sales_df):
        self.sales_df = sales_df

    def detect_anomalies(self, threshold=2.0):
        if len(self.sales_df) < 5:
            return []

        # Group by date and sum revenue
        self.sales_df["booking_date"] = pd.to_datetime(self.sales_df["booking_date"])
        daily_sales = self.sales_df.groupby("booking_date")["revenue"].sum().reset_index()
        
        # Calculate Z-score for revenue
        mean_revenue = daily_sales['revenue'].mean()
        std_revenue = daily_sales['revenue'].std()
        
        if std_revenue == 0:
            return []

        daily_sales['z_score'] = (daily_sales['revenue'] - mean_revenue) / std_revenue
        
        # Detect anomalies where |z_score| > threshold
        anomalies = daily_sales[np.abs(daily_sales['z_score']) > threshold]
        
        anomaly_results = []
        for _, row in anomalies.iterrows():
            anomaly_results.append({
                'date': row['booking_date'].strftime('%Y-%m-%d'),
                'revenue': float(row['revenue']),
                'z_score': float(row['z_score']),
                'type': 'Spike' if row['z_score'] > 0 else 'Drop'
            })
            
        return anomaly_results
