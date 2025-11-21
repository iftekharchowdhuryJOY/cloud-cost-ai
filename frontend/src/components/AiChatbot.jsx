/**
 * AI Chatbot Component
 * 
 * Floating chat widget for FinOps cost analysis powered by LLM.
 * Provides conversational interface for cost spike explanations
 * with service-specific metrics context.
 * 
 * Features:
 * - Service dropdown for quick analysis
 * - Real-time chat with conversation history
 * - Auto-scroll to latest messages
 * - Metrics display panel
 * - Loading states and error handling
 */
import { useState, useRef, useEffect } from 'react';
import { chatAi, explainService } from '../api/aiService';
import { 
  CHATBOT_CONFIG, 
  COMMON_AWS_SERVICES, 
  MESSAGE_TEMPLATES,
  COLORS 
} from '../config/constants';

/**
 * AiChatbot - Main chatbot component
 * 
 * @returns {JSX.Element} Floating chat button and panel
 */
function AiChatbot() {
  const [open, setOpen] = useState(false);
  const [service, setService] = useState('');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: MESSAGE_TEMPLATES.welcome }
  ]);
  const [metrics, setMetrics] = useState(null);
  const messagesEndRef = useRef(null);

  /**
   * Scroll to bottom of message list
   * Used after new messages or panel open
   */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ 
      behavior: CHATBOT_CONFIG.AUTO_SCROLL_BEHAVIOR 
    });
  };

  useEffect(() => {
    console.log('AiChatbot mounted!');
    scrollToBottom();
  }, [messages]);

  /**
   * Send user message to chat API
   * 
   * Side effects:
   * - Updates message history
   * - Makes API call to backend
   * - Updates loading state
   * - Handles errors with user-facing messages
   */
  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { role: 'user', content: input.trim() };
    const updatedMessages = [...messages, userMessage];
    
    setMessages(updatedMessages);
    setInput('');
    setLoading(true);
    
    try {
      const data = await chatAi(
        updatedMessages, 
        service || null, 
        CHATBOT_CONFIG.DEFAULT_DAYS_LOOKBACK
      );
      setMessages(data.messages);
      setMetrics(data.metrics || null);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [
        ...prev, 
        { role: 'assistant', content: MESSAGE_TEMPLATES.apiError }
      ]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Quick explain - Fetch cost spike analysis for selected service
   * 
   * Side effects:
   * - Validates service selection
   * - Fetches explanation from backend
   * - Updates message history with formatted analysis
   * - Handles errors gracefully
   */
  const quickExplain = async () => {
    if (!service) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: MESSAGE_TEMPLATES.selectService }
      ]);
      return;
    }
    
    setLoading(true);
    setMessages(prev => [
      ...prev,
      { role: 'user', content: `Explain cost spike for ${service}` }
    ]);
    
    try {
      const data = await explainService(
        service, 
        CHATBOT_CONFIG.DEFAULT_DAYS_LOOKBACK, 
        false
      );
      
      const { explanation: exp } = data;
      const formattedResponse = formatExplanation(service, exp);
      
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: formattedResponse }
      ]);
      setMetrics(data.metrics);
    } catch (error) {
      console.error('Explain error:', error);
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: MESSAGE_TEMPLATES.serviceNotFound(service) }
      ]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Format explanation into readable message
   * 
   * @param {string} serviceName - AWS service name
   * @param {Object} explanation - Explanation object from API
   * @returns {string} Formatted markdown-style message
   */
  const formatExplanation = (serviceName, explanation) => {
    const confidence = (explanation.confidence * 100).toFixed(0);
    return `📊 **${serviceName} Cost Analysis**\n\n${explanation.summary}\n\n💡 **Recommendation:**\n${explanation.recommendation}\n\n🎯 Confidence: ${confidence}%`;
  };

  return (
    <>
      {/* Floating Button */}
      {!open && (
        <button
          onClick={() => {
            console.log('Button clicked!');
            setOpen(true);
          }}
          style={{ 
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            zIndex: 99999,
            background: 'linear-gradient(to right, #2563eb, #1d4ed8)',
            color: 'white',
            padding: '16px 24px',
            borderRadius: '9999px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
            fontWeight: '600',
            fontSize: '14px',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
          onMouseEnter={(e) => e.target.style.transform = 'scale(1.05)'}
          onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          AI Assistant
        </button>
      )}

      {/* Chat Panel */}
      {open && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '384px',
          height: '600px',
          background: 'white',
          borderRadius: '16px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          display: 'flex',
          flexDirection: 'column',
          border: '1px solid #e5e7eb',
          overflow: 'hidden',
          zIndex: 99999
        }}>
          {/* Header */}
          <div style={{
            background: 'linear-gradient(to right, #2563eb, #1d4ed8)',
            color: 'white',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '8px',
                height: '8px',
                backgroundColor: '#10b981',
                borderRadius: '50%',
                animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
              }}></div>
              <span style={{ fontWeight: '600' }}>FinOps AI Assistant</span>
            </div>
            <button 
              onClick={() => setOpen(false)} 
              style={{
                color: 'white',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                border: 'none',
                borderRadius: '4px',
                padding: '4px 8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: 'bold'
              }}
              onMouseEnter={e => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'}
              onMouseLeave={e => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'}
            >
              ✕
            </button>
          </div>

          {/* Service Selector */}
          <div style={{
            padding: '12px 16px',
            backgroundColor: '#f9fafb',
            borderBottom: '1px solid #e5e7eb'
          }}>
            <label style={{
              fontSize: '12px',
              fontWeight: '500',
              color: '#374151',
              marginBottom: '4px',
              display: 'block'
            }}>Select Service</label>
            <div 
              className="service-selector-container"
              style={{ 
                display: 'flex', 
                gap: '8px',
                flexWrap: 'wrap',
                alignItems: 'stretch'
              }}>
              <select
                value={service}
                onChange={e => setService(e.target.value)}
                style={{
                  flex: '1 1 200px',
                  minWidth: '200px',
                  maxWidth: '100%',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  fontSize: '14px',
                  backgroundColor: 'white',
                  boxSizing: 'border-box'
                }}
              >
                <option value="">Choose a service...</option>
                {COMMON_AWS_SERVICES.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <button 
                onClick={quickExplain} 
                disabled={!service || loading} 
                style={{
                  backgroundColor: !service || loading ? '#9ca3af' : '#2563eb',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '8px 16px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: !service || loading ? 'not-allowed' : 'pointer',
                  whiteSpace: 'nowrap',
                  minWidth: 'fit-content',
                  flexShrink: 0,
                  boxSizing: 'border-box'
                }}
                onMouseEnter={e => {
                  if (!service || loading) return;
                  e.target.style.backgroundColor = '#1d4ed8';
                }}
                onMouseLeave={e => {
                  if (!service || loading) return;
                  e.target.style.backgroundColor = '#2563eb';
                }}
              >
                {loading ? '⏳' : '⚡ Analyze'}
              </button>
            </div>
            
            {/* Media query alternative for very small screens */}
            <style>{`
              @media (max-width: 320px) {
                .service-selector-container {
                  flex-direction: column !important;
                }
                .service-selector-container select {
                  flex: none !important;
                  width: 100% !important;
                  margin-bottom: 8px;
                }
                .service-selector-container button {
                  width: 100% !important;
                  justify-self: center;
                }
              }
            `}</style>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '12px 16px',
            backgroundColor: '#f9fafb',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            {messages.map((m, i) => (
              <div key={i} style={{
                display: 'flex',
                justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start'
              }}>
                <div style={{
                  maxWidth: '85%',
                  borderRadius: '16px',
                  padding: '12px 16px',
                  backgroundColor: m.role === 'user' ? '#2563eb' : 'white',
                  color: m.role === 'user' ? 'white' : '#1f2937',
                  border: m.role === 'user' ? 'none' : '1px solid #e5e7eb',
                  boxShadow: m.role === 'assistant' ? '0 1px 3px rgba(0, 0, 0, 0.1)' : 'none'
                }}>
                  <div style={{
                    fontSize: '14px',
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.5'
                  }}>{m.content}</div>
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{
                  backgroundColor: 'white',
                  borderRadius: '16px',
                  padding: '12px 16px',
                  border: '1px solid #e5e7eb',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
                }}>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      backgroundColor: '#9ca3af',
                      borderRadius: '50%',
                      animation: 'bounce 1s infinite'
                    }}></div>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      backgroundColor: '#9ca3af',
                      borderRadius: '50%',
                      animation: 'bounce 1s infinite 0.15s'
                    }}></div>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      backgroundColor: '#9ca3af',
                      borderRadius: '50%',
                      animation: 'bounce 1s infinite 0.3s'
                    }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Metrics Display */}
          {metrics && !metrics.error && (
            <div style={{
              padding: '8px 16px',
              backgroundColor: '#eff6ff',
              borderTop: '1px solid #bfdbfe',
              fontSize: '12px',
              color: '#374151',
              display: 'flex',
              gap: '12px'
            }}>
              <span>💰 ${metrics.cost_today}</span>
              <span>📈 {metrics.spike_window?.cost_delta_pct}%</span>
              <span>📊 Vol: {metrics.volatility?.toFixed(2)}</span>
            </div>
          )}

          {/* Input */}
          <div style={{
            padding: '12px 16px',
            backgroundColor: 'white',
            borderTop: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Ask about costs, trends, or recommendations..."
                style={{
                  flex: 1,
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  fontSize: '14px',
                  backgroundColor: loading ? '#f9fafb' : 'white',
                  color: loading ? '#9ca3af' : '#1f2937'
                }}
                onKeyDown={e => { 
                  if (e.key === 'Enter' && !e.shiftKey) { 
                    e.preventDefault(); 
                    sendMessage(); 
                  } 
                }}
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                style={{
                  backgroundColor: (loading || !input.trim()) ? '#9ca3af' : '#2563eb',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '8px 12px',
                  cursor: (loading || !input.trim()) ? 'not-allowed' : 'pointer',
                  fontSize: '16px'
                }}
                onMouseEnter={e => {
                  if (loading || !input.trim()) return;
                  e.target.style.backgroundColor = '#1d4ed8';
                }}
                onMouseLeave={e => {
                  if (loading || !input.trim()) return;
                  e.target.style.backgroundColor = '#2563eb';
                }}
              >
                {loading ? '⏳' : '➤'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default AiChatbot;
