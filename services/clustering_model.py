import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

class CustomerSegmenter:
    def __init__(self, customer_df):
        self.customer_df = customer_df
        self.model = KMeans(n_clusters=3, random_state=42)

    def segment_customers(self):
        if len(self.customer_df) < 3:
            return []

        # Features for clustering: age and spending
        features = self.customer_df[['age', 'spending']]
        
        # Standardize features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)
        
        # Fit KMeans
        self.customer_df['cluster'] = self.model.fit_predict(scaled_features)
        
        # Map clusters to meaningful names
        cluster_names = {
            0: 'Budget Travelers',
            1: 'Premium Travelers',
            2: 'Luxury Travelers'
        }
        
        # Sort clusters by average spending to assign names consistently
        cluster_spending = self.customer_df.groupby('cluster')['spending'].mean().sort_values()
        cluster_mapping = {old: new for new, old in enumerate(cluster_spending.index)}
        
        self.customer_df['cluster'] = self.customer_df['cluster'].map(cluster_mapping)
        self.customer_df['segment_name'] = self.customer_df['cluster'].map(cluster_names)
        
        return self.customer_df.to_dict(orient='records')
