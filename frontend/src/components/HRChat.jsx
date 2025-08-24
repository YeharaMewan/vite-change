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
    // Auto scroll to bottom when new messages arrive or streaming text updates
    const scrollToBottom = () => {
      if (messagesEndRef.current) {
        // Use scrollIntoView with end alignment for better mobile behavior
        messagesEndRef.current.scrollIntoView({ 
          behavior: 'smooth',
          block: 'end'
        });
      }
    };

    // Delay scroll slightly to ensure DOM has updated
    const timeoutId = setTimeout(scrollToBottom, 100);
    
    return () => clearTimeout(timeoutId);
  }, [messages, streamingText, isTyping]);

  // Prevent body scroll when sidebar is open on mobile
  useEffect(() => {
    if (sidebarOpen) {
      document.body.classList.add('sidebar-open');
    } else {
      document.body.classList.remove('sidebar-open');
    }

    // Cleanup on unmount
    return () => {
      document.body.classList.remove('sidebar-open');
    };
  }, [sidebarOpen]);

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

    // Force scroll to bottom after adding user message
    setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }
    }, 50);

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
        
        // Scroll during streaming to keep up with text
        if (i % 50 === 0 && messagesEndRef.current) { // Every 50 characters
          messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
        
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
      
      // Final scroll to bottom after message is complete
      setTimeout(() => {
        if (messagesEndRef.current) {
          messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
      }, 100);
      
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
      return <div className="text-white">No message content</div>;
    }
    
    // Enhanced message formatting with better markdown support
    const lines = text.split('\n');
    return lines.map((line, i) => {
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return (
          <div key={i} className="flex items-start gap-2 my-1">
            <span className="text-white font-bold text-sm mt-1">•</span>
            <span className="flex-1 text-white">{line.slice(2)}</span>
          </div>
        );
      } else if (line.startsWith('## ')) {
        return (
          <h3 key={i} className="text-lg font-semibold mt-4 mb-2 text-white">
            {line.slice(3)}
          </h3>
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
          <div key={i} className={`text-white ${i > 0 ? 'mt-2' : ''}`}>
            {line}
          </div>
        );
      }
    });
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      {/* Enhanced Sidebar with better mobile responsiveness */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} fixed inset-y-0 left-0 z-50 w-full sm:w-80 bg-gray-950 transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 flex flex-col border-r border-gray-800 sidebar-scrollbar`}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-3 sm:p-4 border-b border-gray-800">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <SparklesIcon className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-base sm:text-lg">HR Assistant</h1>
              <p className="text-xs text-gray-400">Powered by AI</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1.5 sm:p-2 hover:bg-gray-800 rounded-lg flex items-center justify-center icon-center"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="p-3 sm:p-4 border-b border-gray-800">
          <button
            onClick={createNewSession}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 sm:px-4 sm:py-3 text-sm bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-xl transition-all duration-200 font-medium"
          >
            <PlusIcon className="w-4 h-4" />
            <span className="hidden xs:inline">New Conversation</span>
            <span className="xs:hidden">New Chat</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-1 sm:p-2 sidebar-scrollbar">
          <div className="space-y-1">
            {sessions.length > 0 ? (
              sessions.map((sessionId) => (
                <div
                  key={sessionId}
                  className={`group flex items-center gap-2 sm:gap-3 p-2.5 sm:p-3 rounded-xl cursor-pointer transition-all duration-200 touch-target ${
                    sessionId === currentSessionId
                      ? 'bg-gray-800 text-white border border-gray-700'
                      : 'hover:bg-gray-800/50 text-gray-300 hover:text-white active:bg-gray-800/70'
                  }`}
                  onClick={() => resumeSession(sessionId)}
                >
                  <div className="w-7 h-7 sm:w-8 sm:h-8 bg-gray-700 rounded-lg flex items-center justify-center flex-shrink-0">
                    <DocumentTextIcon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">
                      <span className="hidden sm:inline">Chat {sessionId.substring(5, 13)}</span>
                      <span className="sm:hidden">{sessionId.substring(5, 9)}</span>
                    </div>
                    <div className="text-xs text-gray-500 hidden sm:block">
                      Recent conversation
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(sessionId);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 sm:p-1.5 hover:bg-red-600 active:bg-red-700 rounded-lg transition-all duration-200 touch-target flex items-center justify-center icon-center"
                  >
                    <TrashIcon className="w-3 h-3" />
                  </button>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 text-sm p-4">
                <div className="hidden sm:block">No conversations yet</div>
                <div className="sm:hidden">No chats</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content with improved mobile responsiveness */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Mobile Header */}
        <div className="lg:hidden flex items-center justify-between p-3 sm:p-4 border-b border-gray-800">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-1.5 sm:p-2 hover:bg-gray-800 rounded-lg flex items-center justify-center icon-center"
          >
            <Bars3Icon className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 sm:w-8 sm:h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <SparklesIcon className="w-4 h-4 sm:w-5 sm:h-5" />
            </div>
            <h1 className="text-base sm:text-lg font-semibold">HR Assistant</h1>
          </div>
          <div className="w-8 sm:w-10"></div> {/* Spacer for centering */}
        </div>

        {/* Messages Container */}
        <div className="flex-1 flex flex-col min-h-0">
          {messages.length === 0 && showSuggestions ? (
            /* Enhanced Welcome Screen with mobile optimization */
            <div className="flex-1 flex flex-col items-center justify-center p-4 sm:p-6 lg:p-8 text-center overflow-y-auto">
              <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6 lg:mb-8 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent pb-2 px-2">
                {randomGreeting}
              </h1>
              
              {/* Enhanced Smart Suggestions with mobile-first grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 max-w-4xl w-full mb-4 sm:mb-6 lg:mb-8">
                {smartSuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="group p-4 sm:p-5 lg:p-6 bg-gray-800/50 hover:bg-gray-800 active:bg-gray-800/70 rounded-xl sm:rounded-2xl text-left transition-all duration-300 border border-gray-700 hover:border-gray-600 active:scale-95 sm:hover:scale-105 touch-target"
                  >
                    <div className="flex items-start gap-3 sm:gap-4">
                      <div className="w-8 h-8 sm:w-9 sm:h-9 lg:w-10 lg:h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg sm:rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                        <suggestion.icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-base sm:text-lg font-semibold mb-1 sm:mb-2 text-white group-hover:text-blue-300 transition-colors">
                          {suggestion.title}
                        </div>
                        <div className="text-xs sm:text-sm text-gray-400 group-hover:text-gray-300 transition-colors line-clamp-2">
                          {suggestion.description}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Enhanced Messages Display with mobile optimization */
            <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden chat-scrollbar messages-container auto-scroll-bottom" 
                 style={{ scrollBehavior: 'smooth' }}>
              <div className="max-w-4xl mx-auto px-3 sm:px-4 py-4 sm:py-6 lg:py-8 pb-8 flex flex-col">
                <div className="space-y-4 sm:space-y-6 flex-1">
                  {messages.map((message) => (
                    <div key={message.id} className="group">
                      <div className={`flex gap-2 sm:gap-3 lg:gap-4 ${message.sender === 'user' ? 'justify-end' : ''}`}>
                        {message.sender === 'assistant' && (
                          <div className="w-8 h-8 sm:w-9 sm:h-9 lg:w-10 lg:h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                            <SparklesIcon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                          </div>
                        )}
                        
                        <div className={`flex-1 max-w-[280px] sm:max-w-md lg:max-w-3xl ${message.sender === 'user' ? 'text-right' : ''}`}>
                          {message.sender === 'user' && (
                            <div className="text-gray-400 text-xs sm:text-sm mb-1 sm:mb-2 font-medium flex items-center gap-1 sm:gap-2 justify-end">
                              <span>You</span>
                              <div className="w-5 h-5 sm:w-6 sm:h-6 bg-gray-700 rounded-full flex items-center justify-center">
                                <span className="text-xs font-semibold">Y</span>
                              </div>
                            </div>
                          )}
                          <div className={`relative ${
                            message.sender === 'user' 
                              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3 sm:p-4 rounded-2xl rounded-tr-sm inline-block shadow-lg' 
                              : 'text-white bg-gray-800/30 p-3 sm:p-4 rounded-2xl'
                          }`}>
                            <div className="prose prose-invert prose-sm sm:prose max-w-none text-sm sm:text-base text-white chat-message">
                              {formatMessage(message.text)}
                            </div>
                            {message.sender === 'assistant' && (
                              <div className="flex items-center gap-1 sm:gap-2 mt-2 sm:mt-3 pt-2 border-t border-gray-700">
                                <CheckCircleIcon className="w-3 h-3 sm:w-4 sm:h-4 text-green-400" />
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

                  {/* Enhanced Typing Indicator with mobile optimization */}
                  {(isTyping || streamingText) && (
                    <div className="group">
                      <div className="flex gap-2 sm:gap-3 lg:gap-4">
                        <div className="w-8 h-8 sm:w-9 sm:h-9 lg:w-10 lg:h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse">
                          <SparklesIcon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                        </div>
                        <div className="flex-1 max-w-[280px] sm:max-w-md lg:max-w-3xl">
                          {streamingText ? (
                            <div className="text-white bg-gray-800/30 p-3 sm:p-4 rounded-2xl">
                              <div className="prose prose-invert prose-sm sm:prose max-w-none text-sm sm:text-base text-white chat-message">
                                {formatMessage(streamingText)}
                              </div>
                              <div className="inline-block w-2 h-4 sm:h-5 bg-blue-400 animate-pulse ml-1"></div>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 text-gray-400">
                              <div className="flex gap-1">
                                <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-gray-400 rounded-full animate-bounce"></div>
                              </div>
                              <span className="text-xs sm:text-sm">HR Assistant is thinking...</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                {/* Scroll anchor - increased height for better mobile behavior */}
                <div ref={messagesEndRef} className="h-8 scroll-anchor" />
              </div>
            </div>
          )}

          {/* Enhanced Input Area with mobile optimization */}
          <div className="p-3 sm:p-4 border-t border-gray-800 bg-gray-900">
            <div className="max-w-4xl mx-auto">
              <div className="relative bg-gray-800 rounded-xl sm:rounded-2xl border-2 border-gray-700 focus-within:border-blue-500 transition-all duration-200 shadow-lg">
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
                  className="w-full bg-transparent text-white placeholder-gray-400 border-none outline-none resize-none px-4 sm:px-6 py-3 sm:py-4 pr-20 sm:pr-24 max-h-32 sm:max-h-48 text-sm sm:text-base"
                  disabled={isTyping}
                />
                
                {/* Enhanced Input Actions with mobile optimization */}
                <div className="absolute right-2 sm:right-3 bottom-2 sm:bottom-3 flex items-center gap-1 sm:gap-2">
                  <button
                    onClick={() => alert('Voice input coming soon!')}
                    className="p-1.5 sm:p-2 text-gray-400 hover:text-white hover:bg-gray-700 active:bg-gray-600 rounded-lg sm:rounded-xl transition-all duration-200 active:scale-95 touch-target flex items-center justify-center icon-center"
                    disabled={isTyping}
                  >
                    <MicrophoneIcon className="w-4 h-4 sm:w-5 sm:h-5" />
                  </button>
                  <button
                    onClick={sendMessage}
                    disabled={!input.trim() || isTyping}
                    className={`p-1.5 sm:p-2 rounded-lg sm:rounded-xl transition-all duration-200 active:scale-95 touch-target flex items-center justify-center icon-center ${
                      input.trim() && !isTyping
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700 active:from-blue-700 active:to-purple-800 shadow-lg'
                        : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    <ArrowUpIcon className="w-4 h-4 sm:w-5 sm:h-5" />
                  </button>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mt-2 sm:mt-3 text-xs text-gray-500 gap-1 sm:gap-0">
                <div className="line-clamp-2 sm:line-clamp-1">
                  HR Assistant can make mistakes. Please verify important information.
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
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