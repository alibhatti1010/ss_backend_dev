import random
import time
import re
from typing import Dict, List, Optional


class DummyMedicalChatbot:
    """Dummy AI chatbot service for skin-related medical consultation"""

    def __init__(self):
        self.load_medical_knowledge()
        print("Loading dummy medical chatbot...")
        time.sleep(0.5)
        print("Dummy medical chatbot loaded successfully!")

    def load_medical_knowledge(self):
        """Load dummy medical knowledge base"""

        # Common skin conditions and responses
        self.skin_conditions = {
            'acne': {
                'keywords': ['acne', 'pimples', 'blackheads', 'whiteheads', 'breakouts'],
                'responses': [
                    "Acne is a common skin condition. Keep your skin clean with gentle cleansers, avoid touching your face, and consider using non-comedogenic products.",
                    "For acne management, maintain a consistent skincare routine with mild cleansers. Avoid picking at blemishes as this can cause scarring.",
                    "Acne can be managed with proper skincare. Use gentle, oil-free products and consider consulting a dermatologist for persistent cases."
                ],
                'precautions': [
                    "Avoid harsh scrubbing which can irritate the skin",
                    "Use non-comedogenic moisturizers and sunscreen",
                    "Don't pick or squeeze pimples"
                ]
            },
            'eczema': {
                'keywords': ['eczema', 'dermatitis', 'itchy', 'dry skin', 'rash'],
                'responses': [
                    "Eczema often involves dry, itchy skin. Keep your skin moisturized, avoid known triggers, and use gentle, fragrance-free products.",
                    "For eczema management, focus on maintaining skin hydration with gentle moisturizers and identifying potential triggers.",
                    "Eczema requires consistent moisture barrier protection. Use mild soaps and apply moisturizer while skin is still damp."
                ],
                'precautions': [
                    "Avoid hot showers which can dry out the skin",
                    "Use fragrance-free, hypoallergenic products",
                    "Keep fingernails short to prevent scratching"
                ]
            },
            'psoriasis': {
                'keywords': ['psoriasis', 'scaly', 'plaques', 'thick skin', 'silvery'],
                'responses': [
                    "Psoriasis is an autoimmune condition causing thick, scaly patches. Gentle moisturizing and stress management can help.",
                    "For psoriasis, maintain skin hydration and consider lifestyle factors like stress and diet that may trigger flares.",
                    "Psoriasis management involves consistent skincare and identifying personal triggers. UV light therapy may be beneficial under medical supervision."
                ],
                'precautions': [
                    "Avoid skin trauma which can trigger new patches",
                    "Manage stress levels as stress can worsen psoriasis",
                    "Use thick, occlusive moisturizers"
                ]
            },
            'rosacea': {
                'keywords': ['rosacea', 'redness', 'flushing', 'sensitive skin', 'burning'],
                'responses': [
                    "Rosacea involves facial redness and sensitivity. Identify and avoid triggers, use gentle skincare, and protect from sun exposure.",
                    "For rosacea management, focus on gentle skincare routines and sun protection while avoiding known triggers like spicy foods or alcohol.",
                    "Rosacea requires careful trigger identification and gentle skincare. Use mineral sunscreens and fragrance-free products."
                ],
                'precautions': [
                    "Avoid spicy foods, alcohol, and extreme temperatures",
                    "Use gentle, fragrance-free skincare products",
                    "Always wear broad-spectrum sunscreen"
                ]
            }
        }

        # General skincare advice
        self.general_advice = [
            "Always patch test new skincare products before full application.",
            "Consistency in skincare routines often yields better results than frequent changes.",
            "Sun protection is crucial for all skin types and conditions.",
            "A gentle approach to skincare is usually more effective than aggressive treatments.",
            "Diet, stress, and sleep can all impact skin health."
        ]

        # Medical disclaimers
        self.disclaimers = [
            "This is educational information only and not a substitute for professional medical advice.",
            "Please consult a dermatologist for proper diagnosis and treatment.",
            "If symptoms persist or worsen, seek immediate medical attention.",
            "Individual results may vary, and what works for others may not work for you."
        ]

        # Emergency keywords that need immediate medical attention
        self.emergency_keywords = [
            'severe pain', 'fever', 'spreading rapidly', 'bleeding', 'infection',
            'pus', 'severe swelling', 'difficulty breathing', 'emergency'
        ]

    def generate_response(self, user_message: str, user_context: Optional[Dict] = None) -> Dict:
        """Generate chatbot response to user message"""
        start_time = time.time()

        # Simulate processing time
        processing_delay = random.uniform(1, 3)
        time.sleep(processing_delay)

        try:
            # Clean and analyze user message
            message_lower = user_message.lower().strip()

            # Check for emergency keywords
            if self._contains_emergency_keywords(message_lower):
                response = self._generate_emergency_response()
            # Check for greeting
            elif self._is_greeting(message_lower):
                response = self._generate_greeting_response(user_context)
            # Check for specific skin condition
            elif condition := self._identify_skin_condition(message_lower):
                response = self._generate_condition_response(condition, user_context)
            # General skin advice
            elif self._is_skincare_question(message_lower):
                response = self._generate_general_skincare_response()
            # Fallback response
            else:
                response = self._generate_fallback_response()

            processing_time = time.time() - start_time

            return {
                'response': response['content'],
                'confidence_score': response['confidence'],
                'response_time': processing_time,
                'response_type': response['type'],
                'suggestions': response.get('suggestions', []),
                'status': 'success'
            }

        except Exception as e:
            return {
                'error': f'Failed to generate response: {str(e)}',
                'status': 'error'
            }

    def _contains_emergency_keywords(self, message: str) -> bool:
        """Check if message contains emergency keywords"""
        return any(keyword in message for keyword in self.emergency_keywords)

    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting"""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        return any(greeting in message for greeting in greetings)

    def _is_skincare_question(self, message: str) -> bool:
        """Check if message is about general skincare"""
        skincare_keywords = ['skincare', 'routine', 'moisturizer', 'cleanser', 'sunscreen', 'skin care']
        return any(keyword in message for keyword in skincare_keywords)

    def _identify_skin_condition(self, message: str) -> Optional[str]:
        """Identify skin condition mentioned in message"""
        for condition, data in self.skin_conditions.items():
            if any(keyword in message for keyword in data['keywords']):
                return condition
        return None

    def _generate_emergency_response(self) -> Dict:
        """Generate emergency response"""
        return {
            'content': "⚠️ **IMPORTANT**: If you're experiencing severe symptoms, pain, fever, or signs of infection, please seek immediate medical attention or contact emergency services. This chatbot cannot handle medical emergencies.\n\nPlease consult a healthcare professional or dermatologist as soon as possible for proper evaluation and treatment.",
            'confidence': 1.0,
            'type': 'emergency',
            'suggestions': [
                "Contact emergency services if symptoms are severe",
                "Visit nearest urgent care or emergency room",
                "Call your dermatologist's emergency line"
            ]
        }

    def _generate_greeting_response(self, user_context: Optional[Dict]) -> Dict:
        """Generate greeting response"""
        greetings = [
            "Hello! I'm here to help with your skin health questions. How can I assist you today?",
            "Hi there! I can provide general information about skin conditions and skincare. What would you like to know?",
            "Welcome! I'm your skin health assistant. Feel free to ask me about skincare routines, common skin conditions, or general skin health advice.",
        ]

        base_response = random.choice(greetings)

        # Add context if user has recent analysis
        if user_context and user_context.get('recent_analysis'):
            analysis = user_context['recent_analysis']
            base_response += f"\n\nI see you recently had an analysis for {analysis.get('predicted_disease')}. I'd be happy to provide general information about this condition or answer any related questions."

        base_response += f"\n\n*{random.choice(self.disclaimers)}*"

        return {
            'content': base_response,
            'confidence': 0.95,
            'type': 'greeting',
            'suggestions': [
                "Ask about skincare routines",
                "Learn about specific skin conditions",
                "Get general skin health advice"
            ]
        }

    def _generate_condition_response(self, condition: str, user_context: Optional[Dict]) -> Dict:
        """Generate response for specific skin condition"""
        condition_data = self.skin_conditions[condition]

        # Select random response
        base_response = random.choice(condition_data['responses'])

        # Add precautions
        if condition_data['precautions']:
            precautions = random.sample(condition_data['precautions'], min(2, len(condition_data['precautions'])))
            base_response += "\n\n**Key Precautions:**\n"
            for precaution in precautions:
                base_response += f"• {precaution}\n"

        # Add context if relevant
        if user_context and user_context.get('recent_analysis'):
            analysis = user_context['recent_analysis']
            if condition.lower() in analysis.get('predicted_disease', '').lower():
                base_response += f"\n\nI notice this relates to your recent analysis. The AI detected {analysis.get('predicted_disease')} with {analysis.get('confidence_percentage')}% confidence."

        base_response += f"\n\n*{random.choice(self.disclaimers)}*"

        return {
            'content': base_response,
            'confidence': random.uniform(0.8, 0.95),
            'type': 'condition_advice',
            'suggestions': [
                f"Learn more about {condition} management",
                "Ask about skincare products",
                "Discuss treatment options"
            ]
        }

    def _generate_general_skincare_response(self) -> Dict:
        """Generate general skincare advice"""
        advice = random.choice(self.general_advice)

        additional_tips = [
            "Use a gentle cleanser suitable for your skin type.",
            "Moisturize daily, especially after cleansing.",
            "Apply sunscreen with at least SPF 30 daily.",
            "Introduce new products gradually to avoid irritation.",
            "Stay hydrated and maintain a balanced diet."
        ]

        selected_tips = random.sample(additional_tips, 2)

        response = f"{advice}\n\n**Additional Tips:**\n"
        for tip in selected_tips:
            response += f"• {tip}\n"

        response += f"\n*{random.choice(self.disclaimers)}*"

        return {
            'content': response,
            'confidence': random.uniform(0.7, 0.9),
            'type': 'general_advice',
            'suggestions': [
                "Ask about specific skin concerns",
                "Learn about product recommendations",
                "Discuss skincare routine steps"
            ]
        }

    def _generate_fallback_response(self) -> Dict:
        """Generate fallback response for unclear queries"""
        fallback_responses = [
            "I'd be happy to help with your skin-related questions. Could you please provide more specific details about your concern?",
            "I specialize in skin health and skincare advice. What specific aspect of skin care would you like to discuss?",
            "I can provide information about common skin conditions, skincare routines, and general skin health. What would you like to know more about?",
        ]

        base_response = random.choice(fallback_responses)
        base_response += "\n\n**I can help with:**\n"
        base_response += "• Common skin conditions (acne, eczema, psoriasis, etc.)\n"
        base_response += "• Skincare routine advice\n"
        base_response += "• General skin health information\n"
        base_response += "• Product usage guidance\n"

        base_response += f"\n*{random.choice(self.disclaimers)}*"

        return {
            'content': base_response,
            'confidence': random.uniform(0.6, 0.8),
            'type': 'fallback',
            'suggestions': [
                "Ask about a specific skin condition",
                "Request skincare routine advice",
                "Inquire about skin symptoms"
            ]
        }

    def get_conversation_context(self, messages: List[Dict]) -> Dict:
        """Analyze conversation context for better responses"""
        context = {
            'topics_discussed': [],
            'user_concerns': [],
            'conversation_length': len(messages)
        }

        # Analyze previous messages for context
        for message in messages[-5:]:  # Last 5 messages
            if message.get('message_type') == 'user':
                content = message.get('content', '').lower()
                for condition in self.skin_conditions.keys():
                    if any(keyword in content for keyword in self.skin_conditions[condition]['keywords']):
                        if condition not in context['topics_discussed']:
                            context['topics_discussed'].append(condition)

        return context


# Create global instance
dummy_medical_chatbot = DummyMedicalChatbot()