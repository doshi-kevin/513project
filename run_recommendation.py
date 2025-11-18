"""
Interactive CLI for getting medicine recommendations
Run as: python run_recommendation.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.recommendation_pipeline import RecommendationPipeline
import json

def get_user_input():
    """Get symptoms from user"""
    print('\nEnter symptoms (comma-separated):')
    print('Examples: fever,cough,cold  OR  headache,nausea')
    print('Type "quit" to exit\n')
    
    user_input = input('Symptoms: ').strip()
    
    if user_input.lower() == 'quit':
        return None
    
    symptoms = [s.strip().lower() for s in user_input.split(',')]
    return symptoms

def display_recommendations(recommendations):
    """Display recommendations in formatted way"""
    
    print('\n' + '='*70)
    print('RECOMMENDATIONS')
    print('='*70 + '\n')
    
    if not recommendations:
        print('No recommendations found. Please try different symptoms.')
        return
    
    for rec in recommendations:
        print(f"▼ {rec['rank']}. {rec['medicine_name'].upper()}")
        print(f"   Confidence: {rec['confidence']:.1%}")
        print(f"   Therapeutic Class: {rec['therapeutic_class']}")
        print(f"   Manufacturer: {rec['manufacturer']}")
        print(f"   \nWhy: {rec['explanation']}")
        
        if rec['side_effects']:
            print(f"\n   ⚠ Common Side Effects:")
            for se in rec['side_effects'][:3]:
                print(f"      • {se}")
        
        if rec['alternatives']:
            print(f"\n   💊 Alternative Medicines:")
            for alt in rec['alternatives'][:3]:
                print(f"      • {alt}")
        
        print()

def save_recommendations(recommendations, filename='recommendations.json'):
    """Save recommendations to file"""
    
    with open(filename, 'w') as f:
        json.dump(recommendations, f, indent=2, default=str)
    
    print(f'✓ Recommendations saved to {filename}')

def main():
    """Main interactive loop"""
    
    print('\n' + '='*70)
    print('🏥 MEDICINE RECOMMENDATION SYSTEM')
    print('='*70)
    
    # Initialize pipeline
    print('\nInitializing...')
    pipeline = RecommendationPipeline()
    
    try:
        pipeline.initialize()
        status = pipeline.get_pipeline_status()
        
        if status['data_loaded']:
            print(f'✓ Loaded {status["total_medicines"]:,} medicines')
        if status['gemini_available']:
            print('✓ Gemini AI available for ranking')
        if status['models_loaded']:
            print(f'✓ Loaded {len(pipeline.models)} ML models')
        
    except Exception as e:
        print(f'✗ Initialization error: {e}')
        print('Please ensure all Phase 1 files are in data/processed/')
        return
    
    # Interactive loop
    while True:
        try:
            symptoms = get_user_input()
            
            if symptoms is None:
                print('\nGoodbye! Stay healthy! 🏥')
                break
            
            # Get recommendations
            print('\nProcessing...')
            recommendations = pipeline.recommend(symptoms, top_k=2)
            
            # Display
            display_recommendations(recommendations)
            
            # Ask to save
            save = input('Save recommendations? (y/n): ').lower() == 'y'
            if save:
                save_recommendations(recommendations)
        
        except Exception as e:
            print(f'\n✗ Error: {e}')
            print('Please try again with different symptoms.')

if __name__ == '__main__':
    main()