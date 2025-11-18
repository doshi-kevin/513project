import pandas as pd
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*70)
print("MEDICINE RECOMMENDATION SYSTEM - FULL PIPELINE")
print("="*70)
print("With: ML Models + Clustering + Gemini AI\n")

# Load all components
print("LOADING COMPONENTS...")
print("-"*70)

try:
    xgb = pickle.load(open('models/xgboost_model.pkl', 'rb'))
    scaler = pickle.load(open('models/scaler.pkl', 'rb'))
    pca = pickle.load(open('models/pca.pkl', 'rb'))
    le = pickle.load(open('models/label_encoder.pkl', 'rb'))
    print("✓ ML Model (XGBoost) loaded")
    print("✓ Scaler loaded")
    print("✓ PCA loaded")
    print("✓ Label encoder loaded")
except Exception as e:
    print(f"✗ Error loading models: {e}")
    exit()

# Load data
df = pd.read_csv('data/processed/medicines_merged.csv', low_memory=False)
X_full = pd.read_csv('data/processed/medicine_features.csv')
clusters = pd.read_csv('cluster_results.csv')

print("✓ Medicine data loaded")
print("✓ Clustering data loaded")

# Load Gemini
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        print("✓ Gemini AI loaded")
        has_gemini = True
    except Exception as e:
        print(f"⚠️  Gemini error: {e}")
        has_gemini = False
else:
    print("⚠️  GEMINI_API_KEY not set")
    has_gemini = False

print("\n" + "="*70)
print("SYSTEM READY - ENTER SYMPTOMS")
print("="*70 + "\n")

while True:
    symptom_input = input("Enter symptom(s) or 'quit': ").strip()
    
    if symptom_input.lower() == 'quit':
        print("\nGoodbye!")
        break
    
    print("\n" + "="*70)
    print(f"ANALYZING: {symptom_input.upper()}")
    print("="*70 + "\n")
    
    # STEP 1: Find matching medicines
    print("STEP 1: SYMPTOM MATCHING")
    print("-"*70)
    
    df['match_score'] = df['use0'].fillna('').str.lower().apply(
        lambda x: sum(1 for word in symptom_input.lower().split() if word in x)
    )
    
    matching_meds = df[df['match_score'] > 0].nlargest(20, 'match_score')
    
    if len(matching_meds) == 0:
        print("❌ No medicines found for those symptoms")
        print("Try: fever, cough, pain, cold, headache\n")
        continue
    
    print(f"✓ Found {len(matching_meds)} matching medicines")
    print(f"✓ Top match score: {matching_meds['match_score'].max()}\n")
    
    # STEP 2: ML Model Predictions
    print("STEP 2: ML MODEL PREDICTIONS (XGBoost)")
    print("-"*70)
    
    # Get features for matching medicines
    matching_indices = matching_meds.index.tolist()
    X_matched = X_full.iloc[matching_indices].values
    
    # Transform
    X_pca = pca.transform(X_matched)
    X_scaled = scaler.transform(X_pca)
    
    # Predict with confidence
    predictions = xgb.predict(X_scaled)
    confidences = xgb.predict_proba(X_scaled).max(axis=1)
    
    # Get top 3
    top_3_idx = np.argsort(-confidences)[:3]
    
    print("Top 3 ML Predictions:")
    for rank, idx in enumerate(top_3_idx, 1):
        med_idx = matching_indices[idx]
        medicine = df.iloc[med_idx]
        pred_class = le.inverse_transform([predictions[idx]])[0]
        conf = confidences[idx]
        
        print(f"  {rank}. {medicine['name_248k'][:40]}")
        print(f"     Class: {pred_class}")
        print(f"     ML Confidence: {conf:.1%}")
        print(f"     Manufacturer: {medicine.get('manufacturer', 'Unknown')[:40]}")
    
    # STEP 3: Clustering Context
    print("\nSTEP 3: CLUSTERING CONTEXT")
    print("-"*70)
    
    # Find which cluster this medicine belongs to
    top_medicine_idx = matching_indices[top_3_idx[0]]
    top_medicine_class = df.iloc[top_medicine_idx]['therapeutic_class_248k']
    
    cluster_info = clusters[clusters['primary_class'] == top_medicine_class].head(1)
    if not cluster_info.empty:
        cluster = cluster_info.iloc[0]
        print(f"✓ Cluster ID: {cluster['cluster_id']}")
        print(f"✓ Cluster size: {cluster['size']} medicines")
        print(f"✓ Class purity: {cluster['primary_class']}")
        print(f"✓ Similar medicines in cluster: {cluster['n_classes']} types")
    
    # STEP 4: Gemini AI Enhancement
    if has_gemini:
        print("\nSTEP 4: GEMINI AI ANALYSIS")
        print("-"*70)
        
        try:
            prompt = f"""
            Based on symptoms: {symptom_input}
            
            Top recommended medicine: {df.iloc[top_medicine_idx]['name_248k']}
            Class: {top_medicine_class}
            Uses: {df.iloc[top_medicine_idx].get('use0', 'Not specified')[:100]}
            
            Provide a brief medical explanation (2-3 sentences) why this is recommended.
            """
            
            response = gemini_model.generate_content(prompt)
            print("✓ Gemini AI Explanation:")
            print(f"  {response.text[:200]}...")
        except Exception as e:
            print(f"⚠️  Gemini analysis failed: {e}")
    else:
        print("\nSTEP 4: GEMINI AI")
        print("-"*70)
        print("⚠️  Gemini not available (set GEMINI_API_KEY in .env)")
    
    # STEP 5: Final Recommendations
    print("\n" + "="*70)
    print("FINAL RECOMMENDATIONS")
    print("="*70 + "\n")
    
    for rank, idx in enumerate(top_3_idx, 1):
        med_idx = matching_indices[idx]
        medicine = df.iloc[med_idx]
        pred_class = le.inverse_transform([predictions[idx]])[0]
        conf = confidences[idx]
        
        print(f"{rank}. {medicine['name_248k'].upper()}")
        print(f"   Therapeutic Class: {pred_class}")
        print(f"   ML Confidence: {conf:.1%}")
        print(f"   Manufacturer: {medicine.get('manufacturer', 'Unknown')}")
        print(f"   Uses: {str(medicine.get('use0', 'Not specified'))[:80]}...")
        if pd.notna(medicine.get('sideeffect0')):
            print(f"   Side Effects: {medicine.get('sideeffect0')}")
        print()
    
    print("="*70 + "\n")