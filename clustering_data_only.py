import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering

project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root / 'src'))

print("CLUSTERING - DATA ONLY\n")

# Load
df = pd.read_csv('data/processed/medicines_merged.csv', low_memory=False)
X = pd.read_csv('data/processed/medicine_features.csv')

print(f"✓ Data: {df.shape}")
print(f"✓ Features: {X.shape}\n")

# Cluster
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X.values)

print("Clustering (K=60)...")
clustering = AgglomerativeClustering(n_clusters=60, linkage='ward')
labels = clustering.fit_predict(X_scaled)

print("✓ Done\n")

# Save results
results = []
for cluster_id in range(60):
    mask = labels == cluster_id
    cluster_df = df[mask]
    
    results.append({
        'cluster_id': cluster_id,
        'size': mask.sum(),
        'primary_class': cluster_df['therapeutic_class_248k'].mode()[0] if len(cluster_df) > 0 else 'Unknown',
        'n_classes': cluster_df['therapeutic_class_248k'].nunique(),
        'top_medicines': ' | '.join(cluster_df['name_248k'].head(3).tolist())
    })

results_df = pd.DataFrame(results).sort_values('size', ascending=False)
results_df.to_csv('cluster_results.csv', index=False)

print("✓ Saved cluster_results.csv")
print(f"\nCluster summary:")
print(results_df.head(10))