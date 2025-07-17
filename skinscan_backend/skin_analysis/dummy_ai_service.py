import random
import time
from PIL import Image
import os


class DummySkinDiseasePredictor:
    """Dummy AI service that returns random predictions for testing"""

    def __init__(self):
        self.diseases = [
            'Acne',
            'Eczema',
            'Psoriasis',
            'Dermatitis',
            'Rosacea',
            'Seborrheic Dermatitis',
            'Hives',
            'Vitiligo',
            'Normal Skin'
        ]

        # Simulate model loading time
        print("Loading dummy AI model...")
        time.sleep(1)
        print("Dummy model loaded successfully!")

    def predict(self, image_path):
        """
        Simulate AI prediction with dummy data
        Returns: dict with prediction results
        """
        start_time = time.time()

        try:
            # Simulate processing time (1-3 seconds)
            processing_delay = random.uniform(1, 3)
            time.sleep(processing_delay)

            # Get image info for more realistic simulation
            image_info = self._get_image_info(image_path)

            # Generate dummy prediction based on image characteristics
            prediction = self._generate_prediction(image_info)

            processing_time = time.time() - start_time

            return {
                'predicted_disease': prediction['disease'],
                'confidence_score': prediction['confidence'],
                'processing_time': processing_time,
                'image_info': image_info,
                'status': 'success'
            }

        except Exception as e:
            return {
                'error': f'Prediction failed: {str(e)}',
                'status': 'error'
            }

    def _get_image_info(self, image_path):
        """Extract basic image information"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                format_type = img.format
                mode = img.mode

            file_size = os.path.getsize(image_path)

            return {
                'width': width,
                'height': height,
                'format': format_type,
                'mode': mode,
                'file_size': file_size,
                'dimensions': f"{width}x{height}"
            }
        except Exception as e:
            return {
                'error': f'Could not process image: {str(e)}'
            }

    def _generate_prediction(self, image_info):
        """Generate realistic dummy prediction"""

        # Simulate different confidence levels based on image quality
        if image_info.get('width', 0) < 500 or image_info.get('height', 0) < 500:
            # Lower confidence for small images
            confidence = random.uniform(0.4, 0.7)
        elif image_info.get('file_size', 0) < 100000:  # Less than 100KB
            # Lower confidence for very compressed images
            confidence = random.uniform(0.5, 0.75)
        else:
            # Higher confidence for good quality images
            confidence = random.uniform(0.7, 0.95)

        # Select random disease
        disease = random.choice(self.diseases)

        # Adjust confidence based on disease type
        if disease == 'Normal Skin':
            confidence = random.uniform(0.8, 0.95)
        elif disease in ['Acne', 'Eczema']:
            confidence = random.uniform(0.75, 0.92)

        return {
            'disease': disease,
            'confidence': round(confidence, 3)
        }

    def get_available_diseases(self):
        """Return list of diseases the model can predict"""
        return self.diseases.copy()


# Create global instance
dummy_predictor = DummySkinDiseasePredictor()