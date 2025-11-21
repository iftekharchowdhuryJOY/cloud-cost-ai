"""LLM Chat Service - Conversational FinOps Assistant.

Provides chat-based cost analysis using LLM providers (Groq/OpenAI)
with service-specific metrics context and deterministic fallback.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional

from app.services.llm_explain import collect_spike_metrics, _fallback_explanation

# Configuration constants
DEFAULT_LLM_PROVIDER = "openai"
DEFAULT_LLM_MODEL = "gpt-4.1-mini"
MAX_CONVERSATION_HISTORY = 12  # Limit context window
LLM_TIMEOUT_SECONDS = 25
LLM_MAX_TOKENS = 550
LLM_TEMPERATURE = 0.2
RESPONSE_MAX_WORDS = 140

# Environment configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).lower()
LLM_MODEL = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
USE_LLM = os.getenv("USE_LLM", "true").lower() == "true" and bool(LLM_API_KEY or GROQ_API_KEY)

logger = logging.getLogger(__name__)


def _call_openai_chat(messages: List[Dict[str, str]]) -> Optional[str]:
    """Call OpenAI Chat API with response format.
    
    Args:
        messages: Conversation history with role/content dicts
        
    Returns:
        Assistant reply text or None if request fails
        
    Side effects:
        Makes HTTP request to OpenAI API
    """
    import requests
    
    body = {
        "model": LLM_MODEL,
        "input": messages,
        "max_output_tokens": LLM_MAX_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=body,
            timeout=LLM_TIMEOUT_SECONDS
        )
        
        if response.status_code >= 400:
            logger.warning(f"OpenAI API error: {response.status_code}")
            return None
            
        data = response.json()
        return data["output"][0]["content"][0]["text"]
    except (KeyError, IndexError) as e:
        logger.error(f"OpenAI response parsing failed: {e}")
        return None
    except requests.RequestException as e:
        logger.error(f"OpenAI request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling OpenAI: {e}")
        return None


def _call_groq_chat(messages: List[Dict[str, str]]) -> Optional[str]:
    """Call Groq Chat API.
    
    Args:
        messages: Conversation history with role/content dicts
        
    Returns:
        Assistant reply text or None if request fails
        
    Side effects:
        Makes HTTP request to Groq API via SDK
    """
    try:
        from groq import Groq
        
        api_key = GROQ_API_KEY or LLM_API_KEY
        if not api_key:
            logger.error("No Groq API key available")
            return None
            
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message["content"]
    except ImportError as e:
        logger.error(f"Groq SDK not installed: {e}")
        return None
    except Exception as e:
        logger.error(f"Groq request failed: {e}")
        return None


def _extract_last_user_message(messages: List[Dict[str, str]]) -> str:
    """Extract most recent user message from conversation history.
    
    Args:
        messages: Conversation history
        
    Returns:
        User's last message content or empty string
    """
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def _format_metrics_context(metrics: Dict[str, Any]) -> str:
    """Format service metrics into structured text for LLM context.
    
    Args:
        metrics: Service spike metrics dictionary
        
    Returns:
        Formatted metrics string for prompt injection
    """
    return (
        f"Service: {metrics['service']}\n"
        f"CostToday: {metrics['cost_today']}\n"
        f"Median7d: {metrics['median_7d']}\n"
        f"SpikeRatio: {metrics['spike_ratio']}\n"
        f"AccelerationRatio: {metrics['acceleration_ratio']}\n"
        f"AnomalyDensity: {metrics['anomaly_density']}\n"
        f"Volatility: {metrics['volatility']}\n"
        f"MA7: {metrics['ma7']}\n"
        f"MA30: {metrics['ma30']}\n"
        f"DeltaUSD: {metrics['spike_window']['cost_delta_usd']}\n"
        f"DeltaPct: {metrics['spike_window']['cost_delta_pct']}\n"
        f"BudgetPressure: {metrics.get('budget_pressure')}\n"
    )


def _build_conversation_context(
    messages: List[Dict[str, str]],
    metrics_text: Optional[str] = None
) -> List[Dict[str, str]]:
    """Build full conversation context with system prompt and metrics.
    
    Args:
        messages: User conversation history
        metrics_text: Optional formatted metrics for context injection
        
    Returns:
        Complete conversation array for LLM API
    """
    system_prompt = (
        "You are a FinOps cost optimization assistant. Use only provided metrics and user text. "
        "If metrics are provided, focus on explaining recent spend behavior and actionable steps. "
        f"Do not invent numbers or infrastructure details. Be concise (<={RESPONSE_MAX_WORDS} words)."
    )
    
    context = [{"role": "system", "content": system_prompt}]
    
    if metrics_text:
        context.append({"role": "system", "content": f"METRICS:\n{metrics_text}"})
    
    # Limit conversation history to prevent context overflow
    recent_messages = messages[-MAX_CONVERSATION_HISTORY:]
    for msg in recent_messages:
        context.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    
    return context


def generate_chat_reply(
    messages: List[Dict[str, str]],
    service: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """Generate AI chat reply with optional service metrics context.
    
    Args:
        messages: Conversation history (list of {role, content} dicts)
        service: Optional AWS service name for metrics injection
        days: Historical window for metrics (default: 30)
        
    Returns:
        Dict with updated messages array and optional metrics dict
        
    Side effects:
        - Fetches service metrics if service specified
        - Calls LLM API (Groq or OpenAI)
        - Logs errors and warnings
    """
    user_text = _extract_last_user_message(messages)
    
    # Fetch service metrics if service context requested
    metrics = None
    metrics_text = None
    if service:
        metrics = collect_spike_metrics(service, days=days)
        if not metrics.get("error"):
            metrics_text = _format_metrics_context(metrics)
    
    # Build conversation with system prompt and metrics
    conversation = _build_conversation_context(messages, metrics_text)
    
    # Attempt LLM call with provider routing
    reply_text = None
    if USE_LLM:
        if LLM_PROVIDER == "groq":
            reply_text = _call_groq_chat(conversation)
        else:
            reply_text = _call_openai_chat(conversation)
        
        if reply_text:
            logger.info(f"LLM reply generated via {LLM_PROVIDER}")
    
    # Fallback to deterministic response if LLM unavailable
    if not reply_text:
        logger.warning("LLM unavailable, using fallback response")
        if metrics and not metrics.get("error"):
            fallback = _fallback_explanation(metrics)
            reply_text = f"{fallback['summary']}\nRecommendation: {fallback['recommendation']}"
        else:
            reply_text = "I can explain cost spikes when you specify a service name."
            if user_text:
                reply_text += f" You asked: '{user_text[:80]}'"
    
    # Append assistant reply to conversation
    updated_messages = messages + [{"role": "assistant", "content": reply_text}]
    
    return {
        "messages": updated_messages,
        "metrics": metrics
    }
