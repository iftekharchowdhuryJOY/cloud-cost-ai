#!/usr/bin/env python3
"""
Test Groq API with the actual available models from the API response.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_available_models():
    """Test with models that are actually available."""
    # Models from the API response that look suitable for chat
    test_models = [
        'llama-3.1-8b-instant',
        'llama-3.3-70b-versatile', 
        'openai/gpt-oss-20b',  # Your current model
        'openai/gpt-oss-120b',
        'qwen/qwen3-32b'
    ]
    
    print(f"🧪 Testing Available Groq Models...")
    
    api_key = os.getenv('GROQ_API_KEY')
    
    for model in test_models:
        print(f"\n🔄 Testing {model}...")
        
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': model,
                'messages': [
                    {'role': 'user', 'content': 'Hello! Please respond with "API test successful" to confirm you are working.'}
                ],
                'max_tokens': 20,
                'temperature': 0
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data['choices'][0]['message']['content']
                tokens = data.get('usage', {}).get('total_tokens', '?')
                print(f"  ✅ SUCCESS: {message.strip()}")
                print(f"  📊 Tokens used: {tokens}")
                
                # Test cost analysis with this working model
                return test_cost_analysis(model)
                
            else:
                error_msg = "Unknown error"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                except:
                    error_msg = f'HTTP {response.status_code}'
                print(f"  ❌ FAILED: {error_msg}")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    return False

def test_cost_analysis(working_model):
    """Test cost analysis with a working model."""
    print(f"\n💰 Testing Cost Analysis with {working_model}...")
    
    api_key = os.getenv('GROQ_API_KEY')
    
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        cost_prompt = """Analyze this AWS cost change:
EC2 instances: $150 this month (was $100 last month)
What could cause this 50% increase? Give 2 brief reasons."""
        
        payload = {
            'model': working_model,
            'messages': [{'role': 'user', 'content': cost_prompt}],
            'max_tokens': 100,
            'temperature': 0.3
        }
        
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            explanation = data['choices'][0]['message']['content']
            tokens = data.get('usage', {}).get('total_tokens', '?')
            
            print(f"  ✅ Cost Analysis Response:")
            print(f"  📝 {explanation}")
            print(f"  🔢 Tokens: {tokens}")
            
            print(f"\n🎉 SUCCESS! Your Groq API is working!")
            print(f"✅ Working model: {working_model}")
            print(f"✅ Can generate cost explanations")
            
            return True
        else:
            print(f"  ❌ Cost analysis failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Cost analysis error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Groq API Final Test")
    print("=" * 50)
    
    success = test_available_models()
    
    if not success:
        print("\n❌ All tests failed")
        print("💡 Possible issues:")
        print("  - Invalid GROQ_API_KEY")
        print("  - Network connectivity issues") 
        print("  - Account/billing issues with Groq")
        sys.exit(1)
    
    sys.exit(0)