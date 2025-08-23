'use client';

import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';

import { 
  Bars3Icon, 
  XMarkIcon, 
  PlusIcon, 
  PaperAirplaneIcon,
  EllipsisVerticalIcon,
  TrashIcon,
  PencilIcon,
  ArrowUpIcon,
  MicrophoneIcon,
  PaperClipIcon,
  SparklesIcon,
  DocumentTextIcon,
  UserGroupIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

// HR agent ප්‍රාරම්භ පණිවිඩයන්
const initialGreetings = [
    "What can I help with?",
    "What's on your mind today?",
    "Where should we begin?",
    "Ready when you are.",
    "How can I help you today?",
    "I'm here to assist. What's your question?",
];

// Enhanced suggestions based on HR context
const smartSuggestions = [
  {
    icon: DocumentTextIcon,
    title: "Leave Request",
    description: "Apply for time off or check leave balance",
    prompt: "I want to request leave for next week. Can you help me with the process?"
  },
  {
    icon: UserGroupIcon,
    title: "Employee Directory", 
    description: "Find team members and contact info",
    prompt: "Who works in the IT department? I need to contact someone from there."
  },
  {
    icon: InformationCircleIcon,
    title: "HR Policies",
    description: "Learn about company policies and procedures", 
    prompt: "What's our work from home policy? How many days can I work remotely?"
  },
  {
    icon: ClockIcon,
    title: "Attendance",
    description: "Check attendance records and history",
    prompt: "Show me the attendance records for this month"
  }
];

export default function EnhancedHRChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // අහඹු ආරම්භක පණිවිඩය ගබඩා කිරීම සඳහා නව state එකක්
  const [randomGreeting, setRandomGreeting] = useState('');

  useEffect(() => {
    // Component එක පටවන විට අහඹු පණිවිඩයක් තෝරාගන්න
    const greeting = initialGreetings[Math.floor(Math.random() * initialGreetings.length)];
    setRandomGreeting(greeting);

    // loadSessions() ශ්‍රිතය ඇමතුම සඳහා පෙර සේවාදායකයක් සොයා ගන්නා ප්‍රශ්න
    // මෙය "Failed to fetch" error එක නවතා ඇත
    if (typeof window !== 'undefined' && window.location.origin) {
      loadSessions();
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  };

  const loadSessions = async () => {
    try {
      // Backend සම්බන්ධතා පරීක්ෂා කරමින් API call එක
      const response = await fetch('/api/sessions');
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      // Mock sessions for development
      const mockSessions = ['session-12345678', 'session-abcdefgh'];
      setSessions(mockSessions);
    }
  };

  const createNewSession = async () => {
    try {
      // Backend API call
      const response = await fetch('/api/sessions', { method: 'POST' });
      const data = await response.json();
      const newSessionId = data.session_id || `session-${uuidv4().substring(0, 8)}`;
      
      setCurrentSessionId(newSessionId);
      setMessages([]);
      setShowSuggestions(true);
      setSessions(prevSessions => [newSessionId, ...prevSessions]);
      setSidebarOpen(false);
    } catch (error) {
      console.error('Failed to create session:', error);
      // Fallback to local session creation
      const newSessionId = `session-${uuidv4().substring(0, 8)}`;
      setCurrentSessionId(newSessionId);
      setMessages([]);
      setShowSuggestions(true);
      setSessions(prevSessions => [newSessionId, ...prevSessions]);
      setSidebarOpen(false);
    }
  };

  const resumeSession = async (sessionId) => {
    try {
      // Backend API call
      const response = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}`);
      const data = await response.json();
      
      // Transform backend message format to frontend format
      const transformedMessages = (data.messages || []).map((msg, index) => ({
        id: Date.now() + index,
        text: msg.content || '', // Ensure text is never undefined
        sender: msg.role === 'user' ? 'user' : 'assistant',
        timestamp: msg.ts ? new Date(msg.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
        status: msg.role === 'user' ? 'sent' : 'received'
      }));
      
      setCurrentSessionId(sessionId);
      setMessages(transformedMessages);
      setShowSuggestions(transformedMessages.length === 0);
      setSidebarOpen(false);
    } catch (error) {
      console.error('Failed to resume session:', error);
      // Mock messages for development
      const mockMessages = [
        { id: 1, text: "Hello, I have a question about my leave balance.", sender: "user", timestamp: "09:30 AM", status: "sent" },
        { id: 2, text: "Certainly. Please provide your employee ID, and I can check that for you.", sender: "assistant", timestamp: "09:31 AM", status: "received" }
      ];
      setCurrentSessionId(sessionId);
      setMessages(mockMessages);
      setShowSuggestions(false);
      setSidebarOpen(false);
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      // Backend API call
      await fetch(`/api/sessions/${encodeURIComponent(sessionId)}`, { 
        method: 'DELETE' 
      });
      
      setSessions(prevSessions => prevSessions.filter(id => id !== sessionId));
      if (sessionId === currentSessionId) {
        setCurrentSessionId(null);
        setMessages([]);
        setShowSuggestions(true);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      // Still remove locally even if backend fails
      setSessions(prevSessions => prevSessions.filter(id => id !== sessionId));
      if (sessionId === currentSessionId) {
        setCurrentSessionId(null);
        setMessages([]);
        setShowSuggestions(true);
      }
    }
  };

  // Enhanced message sending with streaming simulation
  const sendMessage = async (messageText = null) => {
    const textToSend = messageText || input;
    if (!textToSend.trim() || isTyping) return;

    const userMessage = {
      id: Date.now(),
      text: textToSend,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      status: 'sent'
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    setShowSuggestions(false);
    setStreamingText('');
    adjustTextareaHeight();

    try {
      // Backend API call
      const sidParam = currentSessionId ? `&session_id=${encodeURIComponent(currentSessionId)}` : '';
      const response = await fetch(`/api/chat?query=${encodeURIComponent(textToSend)}${sidParam}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      const aiResponse = data.response || "I'm sorry, I couldn't process your request.";
      
      // Simulate streaming effect
      let currentText = '';
      for (let i = 0; i <= aiResponse.length; i++) {
        currentText = aiResponse.slice(0, i);
        setStreamingText(currentText);
        await new Promise(resolve => setTimeout(resolve, Math.random() * 30 + 10));
      }
      
      const assistantMessage = {
        id: Date.now() + 1,
        text: aiResponse,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'received'
      };

      setMessages(prev => [...prev, assistantMessage]);
      setStreamingText('');
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again later.',
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'error'
      };
      setMessages(prev => [...prev, errorMessage]);
      setStreamingText('');
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion.prompt);
  };

  const formatMessage = (text) => {
    // Safety check for undefined text
    if (!text || typeof text !== 'string') {
      return <div>No message content</div>;
    }
    
    // Enhanced message formatting with better markdown support
    const lines = text.split('\n');
    return lines.map((line, i) => {
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return (
          <div key={i} className="flex items-start gap-2 my-1">
            <span className="text-blue-400 font-bold text-sm mt-1">•</span>
            <span className="flex-1">{line.slice(2)}</span>
          </div>
        );
      } else if (line.startsWith('## ')) {
        return (
          <h3 key={i} className="text-lg font-semibold mt-4 mb-2 text-blue-300">
            {line.slice(3)}
          </h3>
        );
      } else if (line.startsWith('**') && line.endsWith('**')) {
        return (
          <div key={i} className="font-semibold my-2">
            {line.slice(2, -2)}
          </div>
        );
      } else if (line.trim() === '') {
        return <div key={i} className="h-2" />;
      } else {
        return (
          <div key={i} className={i > 0 ? 'mt-2' : ''}>
            {line}
          </div>
        );
      }
    });
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {/* Enhanced Sidebar */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} fixed inset-y-0 left-0 z-50 w-80 bg-gray-950 transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 flex flex-col border-r border-gray-800`}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-lg">HR Assistant</h1>
              <p className="text-xs text-gray-400">Powered by AI</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 hover:bg-gray-800 rounded-lg"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 border-b border-gray-800">
          <button
            onClick={createNewSession}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-xl transition-all duration-200 font-medium"
          >
            <PlusIcon className="w-4 h-4" />
            New Conversation
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-2">
          <div className="space-y-1">
            {sessions.length > 0 ? (
              sessions.map((sessionId) => (
                <div
                  key={sessionId}
                  className={`group flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200 ${
                    sessionId === currentSessionId
                      ? 'bg-gray-800 text-white border border-gray-700'
                      : 'hover:bg-gray-800/50 text-gray-300 hover:text-white'
                  }`}
                  onClick={() => resumeSession(sessionId)}
                >
                  <div className="w-8 h-8 bg-gray-700 rounded-lg flex items-center justify-center flex-shrink-0">
                    <DocumentTextIcon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">
                      Chat {sessionId.substring(5, 13)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Recent conversation
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(sessionId);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-600 rounded-lg transition-all duration-200"
                  >
                    <TrashIcon className="w-3 h-3" />
                  </button>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 text-sm p-4">
                No conversations yet
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Mobile Header */}
        <div className="lg:hidden flex items-center justify-between p-4 border-b border-gray-800">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 hover:bg-gray-800 rounded-lg"
          >
            <Bars3Icon className="w-6 h-6" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <SparklesIcon className="w-5 h-5" />
            </div>
            <h1 className="text-lg font-semibold">HR Assistant</h1>
          </div>
        </div>

        {/* Messages Container */}
        <div className="flex-1 flex flex-col">
          {messages.length === 0 && showSuggestions ? (
            /* Enhanced Welcome Screen */
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
              <h1 className="text-5xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent pb-2">
                {randomGreeting}
              </h1>
              
              {/* Enhanced Smart Suggestions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl w-full mb-8">
                {smartSuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="group p-6 bg-gray-800/50 hover:bg-gray-800 rounded-2xl text-left transition-all duration-300 border border-gray-700 hover:border-gray-600 hover:scale-105"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                        <suggestion.icon className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="text-lg font-semibold mb-2 text-white group-hover:text-blue-300 transition-colors">
                          {suggestion.title}
                        </div>
                        <div className="text-sm text-gray-400 group-hover:text-gray-300 transition-colors">
                          {suggestion.description}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Enhanced Messages Display */
            <div className="flex-1 overflow-y-auto">
              <div className="max-w-4xl mx-auto px-4 py-8">
                <div className="space-y-6">
                  {messages.map((message) => (
                    <div key={message.id} className="group">
                      <div className={`flex gap-4 ${message.sender === 'user' ? 'justify-end' : ''}`}>
                        {message.sender === 'assistant' && (
                          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                            <SparklesIcon className="w-5 h-5 text-white" />
                          </div>
                        )}
                        
                        <div className={`flex-1 max-w-3xl ${message.sender === 'user' ? 'text-right' : ''}`}>
                          {message.sender === 'user' && (
                            <div className="text-gray-400 text-sm mb-2 font-medium flex items-center gap-2 justify-end">
                              <span>You</span>
                              <div className="w-6 h-6 bg-gray-700 rounded-full flex items-center justify-center">
                                <span className="text-xs font-semibold">Y</span>
                              </div>
                            </div>
                          )}
                          <div className={`relative ${
                            message.sender === 'user' 
                              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-2xl rounded-tr-sm inline-block max-w-lg shadow-lg' 
                              : 'text-gray-100 bg-gray-800/30 p-4 rounded-2xl'
                          }`}>
                            <div className="prose prose-invert max-w-none">
                              {formatMessage(message.text)}
                            </div>
                            {message.sender === 'assistant' && (
                              <div className="flex items-center gap-2 mt-3 pt-2 border-t border-gray-700">
                                <CheckCircleIcon className="w-4 h-4 text-green-400" />
                                <span className="text-xs text-gray-400">{message.timestamp}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {message.sender === 'user' && (
                          <div className="flex flex-col items-center gap-1">
                            <div className="text-xs text-gray-500">{message.timestamp}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {/* Enhanced Typing Indicator */}
                  {(isTyping || streamingText) && (
                    <div className="group">
                      <div className="flex gap-4">
                        <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse">
                          <SparklesIcon className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1 max-w-3xl">
                          {streamingText ? (
                            <div className="text-gray-100 bg-gray-800/30 p-4 rounded-2xl">
                              <div className="prose prose-invert max-w-none">
                                {formatMessage(streamingText)}
                              </div>
                              <div className="inline-block w-2 h-5 bg-blue-400 animate-pulse ml-1"></div>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 text-gray-400">
                              <div className="flex gap-1">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                              </div>
                              <span className="text-sm">HR Assistant is thinking...</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Enhanced Input Area */}
          <div className="p-4 border-t border-gray-800">
            <div className="max-w-4xl mx-auto">
              <div className="relative bg-gray-800 rounded-2xl border-2 border-gray-700 focus-within:border-blue-500 transition-all duration-200 shadow-lg">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value);
                    adjustTextareaHeight();
                  }}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about HR policies, leave requests, employees..."
                  rows="1"
                  className="w-full bg-transparent text-white placeholder-gray-400 border-none outline-none resize-none px-6 py-4 pr-16 max-h-48 text-base"
                  disabled={isTyping}
                />
                
                {/* Enhanced Input Actions */}
                <div className="absolute right-3 bottom-3 flex items-center gap-2">
                  <button
                    onClick={() => alert('Voice input coming soon!')}
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-xl transition-all duration-200"
                    disabled={isTyping}
                  >
                    <MicrophoneIcon className="w-5 h-5" />
                  </button>
                  <button
                    onClick={sendMessage}
                    disabled={!input.trim() || isTyping}
                    className={`p-2 rounded-xl transition-all duration-200 ${
                      input.trim() && !isTyping
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700 shadow-lg hover:scale-105'
                        : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <ArrowUpIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>
              
              <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                <div>
                  HR Assistant can make mistakes. Please verify important information.
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span>Online</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}