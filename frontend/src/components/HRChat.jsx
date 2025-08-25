import { useState, useRef, useEffect } from 'react';
import { useStreamingChat } from '../hooks/useStreamingChat';
import ReactMarkdown from 'react-markdown';
import { 
  Bars3Icon, 
  XMarkIcon, 
  PaperAirplaneIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const ActionMessage = ({ action }) => {
  if (action.action_type === 'download_report') {
    return (
      <a 
        href={action.url} 
        target="_blank" 
        rel="noopener noreferrer"
        className="inline-block bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-colors mt-3 shadow-lg"
      >
        📄 Download Report
      </a>
    );
  }
  return null;
};

export default function HRChat() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { streamChat, isStreaming, streamedResponse, currentActivity } = useStreamingChat();
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [streamedResponse, messages]);

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
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
        let assistantMessage;
        try {
          const parsedResponse = JSON.parse(response);
          if (parsedResponse.action_type) {
            assistantMessage = {
              id: Date.now() + 1,
              action: parsedResponse,
              sender: 'HR Assistant',
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            };
          } else {
            throw new Error('Not an action');
          }
        } catch {
          assistantMessage = {
            id: Date.now() + 1,
            text: response,
            sender: 'HR Assistant',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          };
        }
        
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch {
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'HR Assistant',
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

  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} fixed inset-y-0 left-0 z-40 w-80 bg-gray-950 transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 flex flex-col border-r border-gray-800 sidebar-scrollbar`}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold">HR Assistant</h2>
              <p className="text-sm text-gray-400">AI-Powered HR Support</p>
            </div>
          </div>
          <button 
            onClick={() => setSidebarOpen(false)} 
            className="lg:hidden p-2 hover:bg-gray-800 rounded-md transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Sidebar Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          <div className="space-y-4">
            <div className="text-sm text-gray-400">
              <h3 className="font-semibold text-gray-300 mb-2">Quick Actions</h3>
              <ul className="space-y-2">
                <li>• Check employee information</li>
                <li>• Submit leave requests</li>
                <li>• View attendance records</li>
                <li>• Generate HR reports</li>
                <li>• Performance management</li>
                <li>• Training and development</li>
              </ul>
            </div>
            
            <div className="pt-4 border-t border-gray-800">
              <h3 className="font-semibold text-gray-300 mb-2 text-sm">System Status</h3>
              <div className="flex items-center gap-2 text-sm">
                <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-blue-400 animate-pulse' : 'bg-green-400'}`}></div>
                <span className="text-gray-400">
                  {isStreaming ? 'Processing...' : 'Ready'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setSidebarOpen(true)} 
              className="lg:hidden p-2 hover:bg-gray-800 rounded-md transition-colors"
            >
              <Bars3Icon className="w-6 h-6" />
            </button>
            <div className="lg:hidden">
              <h1 className="text-lg font-semibold">HR Assistant</h1>
              <p className="text-xs text-gray-400">AI-Powered Support</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-blue-400 animate-pulse' : 'bg-green-400'}`}></div>
            <span className="text-sm text-gray-400 hidden sm:inline">
              {isStreaming 
                ? (currentActivity ? currentActivity.replace(/🔧|🤖|🔄|✅/g, '').trim() : 'Streaming...') 
                : 'Online'
              }
            </span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 chat-scrollbar bg-gray-900">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <div className="w-20 h-20 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <SparklesIcon className="w-10 h-10 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-300 mb-2">Welcome to HR Assistant</h3>
                <p className="text-gray-400 max-w-md mx-auto">
                  I'm here to help with employee information, leave requests, attendance tracking, performance management, and more. Ask me anything!
                </p>
              </div>
            )}
            
            {messages.map((message) => (
              <div key={message.id} className={`flex gap-3 ${message.sender === 'user' ? 'justify-end' : ''}`}>
                {message.sender !== 'user' && (
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <SparklesIcon className="w-5 h-5 text-white" />
                  </div>
                )}
                <div className={`max-w-3xl ${message.sender === 'user' ? 'text-right' : ''}`}>
                  <div className={`${
                    message.sender === 'user' 
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-2xl inline-block' 
                      : 'text-white bg-gray-800/30 p-4 rounded-2xl backdrop-blur-sm'
                  }`}>
                    {message.text && (
                      <div className="prose prose-invert max-w-none">
                        <ReactMarkdown>{message.text}</ReactMarkdown>
                      </div>
                    )}
                    {message.action && <ActionMessage action={message.action} />}
                  </div>
                  <div className="text-xs text-gray-500 mt-1 px-2">
                    {message.timestamp}
                  </div>
                </div>
              </div>
            ))}

            {/* Real-time Streaming Response */}
            {isStreaming && streamedResponse && (
              <div className="flex gap-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse">
                  <SparklesIcon className="w-5 h-5 text-white" />
                </div>
                <div className="max-w-3xl">
                  <div className="text-white bg-gray-800/30 p-4 rounded-2xl backdrop-blur-sm">
                    <div className="prose prose-invert max-w-none">
                      <ReactMarkdown>{streamedResponse}</ReactMarkdown>
                    </div>
                    <div className="inline-block w-2 h-5 bg-blue-400 animate-pulse ml-1"></div>
                  </div>
                </div>
              </div>
            )}

            {/* Activity Indicator - Shows agent/tool activity */}
            {isStreaming && currentActivity && !streamedResponse && (
              <div className="flex gap-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse">
                  <SparklesIcon className="w-5 h-5 text-white" />
                </div>
                <div className="flex items-center gap-2 text-gray-300">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                  </div>
                  <span className="text-sm font-medium">{currentActivity}</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-800 bg-gray-900">
          <div className="max-w-4xl mx-auto">
            <div className="relative bg-gray-800 rounded-2xl border-2 border-gray-700 focus-within:border-blue-500 transition-colors shadow-lg">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  adjustTextareaHeight();
                }}
                onKeyPress={handleKeyPress}
                placeholder="Ask the HR Assistant anything..."
                rows="1"
                className="w-full bg-transparent text-white placeholder-gray-400 border-none outline-none resize-none px-6 py-4 pr-16 max-h-32"
                disabled={isStreaming}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isStreaming}
                className={`absolute right-3 top-1/2 -translate-y-1/2 p-3 rounded-full transition-all duration-200 ${
                  input.trim() && !isStreaming 
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-lg scale-100' 
                    : 'bg-gray-600 text-gray-400 cursor-not-allowed scale-95'
                }`}
              >
                <PaperAirplaneIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
              <span>HR Assistant powered by AI • Real-time responses</span>
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-blue-400 animate-pulse' : 'bg-green-400'}`}></div>
                <span>{isStreaming ? 'Processing' : 'Ready'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm" 
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}