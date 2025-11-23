#!/usr/bin/env python3
"""
Simple Groq API test - minimal dependencies.
Tests if your GROQ_API_KEY works and can generate responses.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_groq_simple():
    """Simple test of Groq API with minimal dependencies."""
    print("🧪 Testing Groq API Key...")
    
    # Check environment variables
    api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('LLM_MODEL', 'llama3-8b-8192')  # Use a reliable model
    provider = os.getenv('LLM_PROVIDER')
    
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment")
        return False
    
    if provider != 'groq':
        print(f"⚠️  LLM_PROVIDER is '{provider}', expected 'groq'")
    
    print(f"✅ API Key: {api_key[:8]}...")
    print(f"✅ Model: {model}")
    
    # Test API call
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'user', 
                    'content': 'Hello! Please respond with exactly: "Groq API test successful"'
                }
            ],
            'max_tokens': 20,
            'temperature': 0
        }
        
        print("🌐 Making API call to Groq...")
        
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content']
            tokens_used = data.get('usage', {}).get('total_tokens', 'unknown')
            
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Response: {message}")
            print(f"✅ Tokens used: {tokens_used}")
            
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            except:
                print(f"❌ Raw response: {response.text}")
            return False
            
    except ImportError:
        print("❌ 'requests' library not available")
        print("💡 Install with: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_cost_analysis_prompt():
    """Test with a cost analysis prompt."""
    print("\n💰 Testing Cost Analysis Prompt...")
    
    api_key = os.getenv('GROQ_API_KEY')
    model = os.getenv('LLM_MODEL', 'llama3-8b-8192')
    
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        cost_prompt = """Analyze this AWS cost data:
- EC2: $120/month (increased 25% from last month)
- S3: $45/month (decreased 10% from last month) 
- RDS: $80/month (new service this month)

Provide 2-3 sentence explanation of the cost changes."""
        
        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': cost_prompt}],
            'max_tokens': 150,
            'temperature': 0.3
        }
        
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            explanation = data['choices'][0]['message']['content']
            tokens = data.get('usage', {}).get('total_tokens', 'unknown')
            
            print(f"✅ Cost Analysis Generated:")
            print(f"📝 {explanation}")
            print(f"🔢 Tokens: {tokens}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Simple Groq API Test")
    print("=" * 40)
    
    # Run tests
    basic_test = test_groq_simple()
    cost_test = test_cost_analysis_prompt() if basic_test else False
    
    # Summary
    print("\n" + "=" * 40)
    if basic_test and cost_test:
        print("🎉 SUCCESS! Your Groq API is working perfectly!")
        print("✅ Basic connectivity: OK")
        print("✅ Cost analysis: OK") 
        print("\n💡 Your API key can handle cost optimization prompts.")
    elif basic_test:
        print("✅ Basic API works, but cost analysis had issues")
    else:
        print("❌ API test failed - check your GROQ_API_KEY")
        
    sys.exit(0 if basic_test else 1)