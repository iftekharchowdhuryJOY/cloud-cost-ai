#!/usr/bin/env python3
"""
Test script to verify Groq API key and LLM functionality.

This script validates:
- Environment variables are loaded correctly
- Groq API key is valid and accessible
- LLM service can generate responses
- Basic cost explanation functionality works

Usage:
    python test_groq.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_setup():
    """Verify required environment variables are set."""
    print("🔍 Testing Environment Setup...")
    
    required_vars = {
        'GROQ_API_KEY': 'Groq API key for LLM functionality',
        'LLM_PROVIDER': 'Should be set to "groq"',
        'LLM_MODEL': 'Model name for Groq API'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"  ❌ {var}: {description}")
            print(f"  ❌ {var}: Not set")
        else:
            # Mask API key for security
            display_value = value[:8] + "..." if var == 'GROQ_API_KEY' else value
            print(f"  ✅ {var}: {display_value}")
    
    if missing_vars:
        print("\n⚠️  Missing environment variables:")
        for var in missing_vars:
            print(var)
        return False
    
    print("✅ Environment setup complete!\n")
    return True

def test_groq_api_direct():
    """Test Groq API connection directly using requests."""
    print("🌐 Testing Direct Groq API Connection...")
    
    try:
        import requests
        
        api_key = os.getenv('GROQ_API_KEY')
        model = os.getenv('LLM_MODEL', 'gpt-oss-20b')
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': 'Hello! Please respond with "Groq API is working" to confirm the connection.'}
            ],
            'max_tokens': 50,
            'temperature': 0.1
        }
        
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"  ✅ API Response: {message.strip()}")
            print(f"  ✅ Model: {result.get('model', 'unknown')}")
            return True
        else:
            print(f"  ❌ API Error: {response.status_code}")
            print(f"  ❌ Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Network Error: {e}")
        return False
    except KeyError as e:
        print(f"  ❌ Response Format Error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected Error: {e}")
        return False

def test_llm_service():
    """Test the LLM service from the project."""
    print("🤖 Testing Project LLM Service...")
    
    try:
        # Import the LLM service from your project
        from app.services.llm_explain import generate_cost_explanation
        
        # Test data
        test_cost_data = [
            {'service': 'EC2-Instance', 'cost': 45.67, 'change': 15.2},
            {'service': 'S3', 'cost': 12.34, 'change': -2.1}
        ]
        
        # Generate explanation
        explanation = generate_cost_explanation(test_cost_data)
        
        if explanation and len(explanation) > 10:
            print(f"  ✅ Generated explanation ({len(explanation)} chars)")
            print(f"  📝 Sample: {explanation[:100]}...")
            return True
        else:
            print(f"  ❌ Empty or short response: {explanation}")
            return False
            
    except ImportError as e:
        print(f"  ❌ Import Error: {e}")
        print("  💡 Make sure you're in the project directory")
        return False
    except Exception as e:
        print(f"  ❌ Service Error: {e}")
        return False

def test_llm_chat():
    """Test the LLM chat service."""
    print("💬 Testing LLM Chat Service...")
    
    try:
        from app.services.llm_chat import get_llm_response
        
        test_prompt = "What are the main factors that can cause AWS EC2 costs to spike suddenly?"
        
        response = get_llm_response(test_prompt)
        
        if response and len(response) > 20:
            print(f"  ✅ Chat response generated ({len(response)} chars)")
            print(f"  📝 Sample: {response[:100]}...")
            return True
        else:
            print(f"  ❌ Empty or short chat response: {response}")
            return False
            
    except ImportError as e:
        print(f"  ❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Chat Error: {e}")
        return False

def main():
    """Run all Groq API tests."""
    print("🚀 Cloud Cost AI - Groq API Test Suite")
    print("=" * 50)
    
    # Track test results
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Direct API Connection", test_groq_api_direct),
        ("LLM Explanation Service", test_llm_service),
        ("LLM Chat Service", test_llm_chat)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((test_name, False))
        
        print()  # Add spacing between tests
    
    # Summary
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Groq API setup is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)