import { useState, useRef, useEffect } from 'react';
import { useStreamingChat } from '../hooks/useStreamingChat';
import { 
  SparklesIcon, 
  ArrowUpIcon,
  MicrophoneIcon,
  Bars3Icon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

export default function StreamingHRChat() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const { streamChat, isStreaming, streamedResponse, error } = useStreamingChat();
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    // Auto scroll to bottom when streaming
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [streamedResponse, messages]);

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage = {
      id: Date.now(),
      text: input,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    adjustTextareaHeight();

    try {
      const response = await streamChat(currentInput);
      
      if (response) {
        const assistantMessage = {
          id: Date.now() + 1,
          text: response,
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (err) {
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (text) => {
    if (!text) return null;
    
    const lines = text.split('\n');
    return lines.map((line, i) => {
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return (
          <div key={i} className="flex items-start gap-2 my-1">
            <span className="text-white font-bold text-sm mt-1">•</span>
            <span className="flex-1 text-white">{line.slice(2)}</span>
          </div>
        );
      } else if (line.startsWith('**') && line.endsWith('**')) {
        return (
          <div key={i} className="font-semibold my-2 text-white">
            {line.slice(2, -2)}
          </div>
        );
      } else if (line.trim() === '') {
        return <div key={i} className="h-2" />;
      } else {
        return (
          <div key={i} className="text-white">
            {line}
          </div>
        );
      }
    });
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold">Streaming HR Assistant</h1>
              <p className="text-xs text-gray-400">Real-time AI responses</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span className="text-sm text-gray-400">
              {isStreaming ? 'Streaming...' : 'Online'}
            </span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((message) => (
              <div key={message.id} className="group">
                <div className={`flex gap-3 ${message.sender === 'user' ? 'justify-end' : ''}`}>
                  {message.sender === 'assistant' && (
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                      <SparklesIcon className="w-4 h-4 text-white" />
                    </div>
                  )}
                  
                  <div className={`max-w-3xl ${message.sender === 'user' ? 'text-right' : ''}`}>
                    <div className={`${
                      message.sender === 'user' 
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-2xl inline-block' 
                        : 'text-white bg-gray-800/30 p-4 rounded-2xl'
                    }`}>
                      {formatMessage(message.text)}
                      
                      {message.sender === 'assistant' && (
                        <div className="flex items-center gap-2 mt-3 pt-2 border-t border-gray-700">
                          <CheckCircleIcon className="w-4 h-4 text-green-400" />
                          <span className="text-xs text-gray-400">{message.timestamp}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* Real-time Streaming Response */}
            {isStreaming && streamedResponse && (
              <div className="group">
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse">
                    <SparklesIcon className="w-4 h-4 text-white" />
                  </div>
                  
                  <div className="max-w-3xl">
                    <div className="text-white bg-gray-800/30 p-4 rounded-2xl">
                      {formatMessage(streamedResponse)}
                      <div className="inline-block w-2 h-5 bg-blue-400 animate-pulse ml-1"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Typing Indicator */}
            {isStreaming && !streamedResponse && (
              <div className="group">
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse">
                    <SparklesIcon className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex items-center gap-2 text-gray-400">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    </div>
                    <span className="text-sm">HR Assistant is processing...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} className="h-4" />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-800">
          <div className="max-w-4xl mx-auto">
            <div className="relative bg-gray-800 rounded-2xl border-2 border-gray-700 focus-within:border-blue-500 transition-colors">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  adjustTextareaHeight();
                }}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about HR... (Streaming enabled)"
                rows="1"
                className="w-full bg-transparent text-white placeholder-gray-400 border-none outline-none resize-none px-6 py-4 pr-24 max-h-48"
                disabled={isStreaming}
              />
              
              <div className="absolute right-3 bottom-3 flex items-center gap-2">
                <button
                  onClick={() => alert('Voice input coming soon!')}
                  className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-xl transition-colors"
                  disabled={isStreaming}
                >
                  <MicrophoneIcon className="w-5 h-5" />
                </button>
                
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || isStreaming}
                  className={`p-2 rounded-xl transition-colors ${
                    input.trim() && !isStreaming
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700'
                      : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  <ArrowUpIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
              <div>HR Assistant with real-time streaming responses</div>
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-blue-400 animate-pulse' : 'bg-green-400'}`}></div>
                <span>{isStreaming ? 'Streaming' : 'Ready'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}