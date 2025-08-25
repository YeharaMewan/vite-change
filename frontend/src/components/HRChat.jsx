import { useState, useRef, useEffect } from 'react';
import { useStreamingChat } from '../hooks/useStreamingChat';
import { useChatHistory } from '../hooks/useChatHistory';
import Sidebar from './Sidebar';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import WelcomeMessage from './WelcomeMessage';
import { 
  Bars3Icon,
  PencilSquareIcon
} from '@heroicons/react/24/outline';


export default function HRChat() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const { streamChat, isStreaming, streamedResponse, currentActivity } = useStreamingChat();
  const { sessions, loading, error, refetch, createNewSession, deleteSession, getSessionMessages } = useChatHistory();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [streamedResponse, messages]);

  const sendMessage = async () => {
    if (!input.trim() || isStreaming) return;

    // If no current session, create one
    let sessionId = currentSessionId;
    if (!sessionId) {
      sessionId = await createNewSession();
      if (!sessionId) {
        console.error('Failed to create new session');
        return;
      }
      setCurrentSessionId(sessionId);
    }

    const userMessage = {
      id: Date.now(),
      text: input,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');

    try {
      const response = await streamChat(currentInput, sessionId);
      
      // Use the final streamed response if available, otherwise use the returned response
      const finalResponse = streamedResponse || response;
      
      if (finalResponse) {
        let assistantMessage;
        try {
          const parsedResponse = JSON.parse(finalResponse);
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
            text: finalResponse,
            sender: 'HR Assistant',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          };
        }
        
        setMessages(prev => [...prev, assistantMessage]);
        
        // Refresh sessions to show updated chat in sidebar
        refetch();
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

  const handleNewChat = async () => {
    // Create a new session in the backend
    const newSessionId = await createNewSession();
    if (newSessionId) {
      setCurrentSessionId(newSessionId);
      setMessages([]);
      setInput('');
      refetch(); // Refresh the sessions list
    }
  };

  const loadChatSession = async (sessionId) => {
    const sessionMessages = await getSessionMessages(sessionId);
    if (sessionMessages && sessionMessages.length > 0) {
      // Convert backend message format to frontend format
      const convertedMessages = sessionMessages.map((msg, index) => ({
        id: `${sessionId}-${index}`,
        text: msg.content,
        sender: msg.role === 'user' ? 'user' : 'HR Assistant',
        timestamp: msg.ts ? new Date(msg.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''
      }));
      setMessages(convertedMessages);
    } else {
      setMessages([]);
    }
    setCurrentSessionId(sessionId);
    setSidebarOpen(false); // Close sidebar on mobile
  };

  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev);
  };

  const handleSidebarCollapseChange = (collapsed) => {
    setSidebarCollapsed(collapsed);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-gray-900">
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen}
        onToggle={toggleSidebar}
        onNewChat={handleNewChat}
        chatHistory={sessions}
        onChatSelect={loadChatSession}
        onDeleteChat={deleteSession}
        loading={loading}
        error={error}
        isCollapsed={sidebarCollapsed}
        onCollapseChange={handleSidebarCollapseChange}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gray-900">
          <div className="flex items-center gap-3">
            {/* Mobile Sidebar Toggle */}
            <button 
              onClick={toggleSidebar} 
              className="lg:hidden p-2 rounded-md hover:bg-gray-800 transition-colors text-white"
              title="Toggle Sidebar"
            >
              <Bars3Icon className="w-6 h-6" />
            </button>
            
            <div className="lg:hidden">
              <h1 className="text-lg font-semibold text-white">HR Assistant</h1>
            </div>
          </div>
          <button 
            onClick={handleNewChat}
            className="p-2 rounded-lg hover:bg-gray-800 transition-colors lg:hidden text-white"
            title="New chat"
          >
            <PencilSquareIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto chat-scrollbar">
          {messages.length === 0 ? (
            <WelcomeMessage />
          ) : (
            <div>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              
              {/* Real-time Streaming Response */}
              {isStreaming && streamedResponse && (
                <ChatMessage 
                  message={{
                    id: 'streaming',
                    text: streamedResponse,
                    sender: 'HR Assistant',
                    timestamp: ''
                  }}
                  isStreaming={true}
                />
              )}

              {/* Activity Indicator */}
              {isStreaming && currentActivity && !streamedResponse && (
                <div className="w-full bg-gray-900 py-4">
                  <div className="max-w-4xl mx-auto px-4">
                    <div className="flex justify-start mb-4">
                      <div className="max-w-2xl text-left">
                        <div className="inline-block p-4 rounded-2xl bg-gray-800 shadow-sm">
                          <div className="flex items-center gap-2 text-white">
                            <div className="flex gap-1">
                              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                            </div>
                            <span className="text-sm">{currentActivity.replace(/🔧|🤖|🔄|✅/g, '').trim()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <ChatInput 
          input={input}
          setInput={setInput}
          onSendMessage={sendMessage}
          isStreaming={isStreaming}
          placeholder="Ask Any HR Related Question..."
        />
      </div>
    </div>
  );
}