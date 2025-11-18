"""
Main entry point for the medicine recommendation system
Test the pipeline locally before deploying
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import Config
from src.recommendation_pipeline import RecommendationPipeline

def main():
    """Main function to run the recommendation pipeline"""
    
    print('\n' + '='*70)
    print('MEDICINE RECOMMENDATION SYSTEM - LOCAL TEST')
    print('='*70 + '\n')
    
    # Initialize configuration
    Config.create_dirs()
    
    # Initialize pipeline
    pipeline = RecommendationPipeline()
    
    try:
        pipeline.initialize()
    except Exception as e:
        print(f'✗ Initialization failed: {e}')
        return
    
    # Check status
    status = pipeline.get_pipeline_status()
    print('\nPipeline Status:')
    for key, value in status.items():
        print(f'  {key}: {value}')
    
    # Try to load models (optional)
    try:
        pipeline.load_trained_models()
    except:
        print('\n⚠ No trained models found. Will use symptom-based matching only.')
    
    # Example: Get recommendations
    print('\n' + '='*70)
    print('EXAMPLE: Getting Recommendations')
    print('='*70 + '\n')
    
    # Test symptoms
    test_symptoms = ['fever', 'cough', 'cold']
    
    print(f'Patient symptoms: {test_symptoms}')
    
    try:
        recommendations = pipeline.recommend(test_symptoms, top_k=2)
        
        print(f'\nTop {len(recommendations)} Recommendations:\n')
        
        for rec in recommendations:
            print(f"{rec['rank']}. {rec['medicine_name']}")
            print(f"   Confidence: {rec['confidence']:.2%}")
            print(f"   Class: {rec['therapeutic_class']}")
            print(f"   Manufacturer: {rec['manufacturer']}")
            print(f"   Explanation: {rec['explanation']}")
            
            if rec['side_effects']:
                print(f"   Side Effects: {', '.join(rec['side_effects'][:2])}")
            
            if rec['alternatives']:
                print(f"   Alternatives: {', '.join(rec['alternatives'][:2])}")
            print()
        
    except Exception as e:
        print(f'✗ Error getting recommendations: {e}')
        import traceback
        traceback.print_exc()
    
    # Test contraindications check
    print('='*70)
    print('EXAMPLE: Checking Contraindications')
    print('='*70 + '\n')
    
    patient_info = {
        'medicines': ['Aspirin', 'Ibuprofen'],
        'allergies': ['Penicillin'],
        'conditions': ['Hypertension']
    }
    
    print(f'Patient info: {patient_info}')
    
    try:
        result = pipeline.check_contraindications(patient_info)
        print(f'\nContraindication Check Result:')
        print(f'  Status: {result.get("status", "unknown")}')
        if 'warnings' in result:
            print(f'  Warnings: {result["warnings"]}')
        print(f'  Safe: {result.get("safe", "unknown")}')
    except Exception as e:
        print(f'⚠ Could not check contraindications: {e}')

if __name__ == '__main__':
    main()