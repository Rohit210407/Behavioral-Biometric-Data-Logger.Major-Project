#!/usr/bin/env python3
"""
Test ML integration with behavioral monitor
"""

import sys
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))

def test_ml_models():
    """Test ML model integration."""
    print("Testing ML Model Integration...")
    print("=" * 40)
    
    try:
        # Test importing ML components
        from src.ml import MLManager
        from src.ml.behavior_models import BehaviorClassifier, AnomalyDetector
        print("✅ ML components imported successfully")
        
        # Test creating ML manager
        config = {
            'ml': {
                'model_path': 'saved_models/',
                'training': {
                    'min_samples': 50,
                    'retrain_interval_hours': 24
                },
                'anomaly_detection': {
                    'contamination': 0.1,
                    'threshold': 0.7
                }
            },
            'authentication': {
                'confidence_levels': {
                    'high': 0.9,
                    'medium': 0.7,
                    'low': 0.5
                }
            }
        }
        
        ml_manager = MLManager(config)
        print("✅ ML Manager created successfully")
        print(f"   Behavior Classifier trained: {ml_manager.behavior_classifier.is_trained}")
        print(f"   Anomaly Detector trained: {ml_manager.anomaly_detector.is_trained}")
        
        # Test sample features
        sample_features = {
            'dwell_mean': 0.15,
            'dwell_std': 0.05,
            'flight_mean': 0.25,
            'flight_std': 0.1,
            'typing_speed': 60.0,
            'velocity_mean': 1200.0,
            'velocity_std': 300.0,
            'mouse_click_rate': 2.5
        }
        
        # Test ML analysis
        result = ml_manager.analyze_behavior(sample_features, 'test_context')
        print("✅ ML Analysis completed successfully")
        print(f"   Combined Confidence: {result['combined_confidence']:.3f}")
        print(f"   Decision: {result['decision']}")
        print(f"   Auth Confidence: {result['auth_confidence']:.3f}")
        print(f"   Anomaly Score: {result['anomaly_score']:.3f}")
        
        print("\n🎉 ML Integration Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"❌ ML Integration Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_ml_models()