import { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, MicrophoneIcon } from '@heroicons/react/24/outline';

export default function ChatInput({ 
  input, 
  setInput, 
  onSendMessage, 
  isStreaming = false,
  placeholder = "Ask anything..." 
}) {
  const textareaRef = useRef(null);
  const [isKeyboardOpen, setIsKeyboardOpen] = useState(false);

  // Auto-resize textarea
  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  };

  // Handle mobile keyboard
  useEffect(() => {
    const handleResize = () => {
      if (window.innerHeight < window.screen.height * 0.75) {
        setIsKeyboardOpen(true);
        document.body.classList.add('keyboard-open');
      } else {
        setIsKeyboardOpen(false);
        document.body.classList.remove('keyboard-open');
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      document.body.classList.remove('keyboard-open');
    };
  }, []);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    onSendMessage();
    // Reset textarea height after sending
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }, 0);
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
    adjustTextareaHeight();
  };

  return (
    <div className={`bg-gray-900 ${isKeyboardOpen ? 'chat-input' : ''}`}>
      <div className="mx-auto max-w-3xl px-4 py-6">
        <div className="relative">
          {/* Main input container */}
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder={placeholder}
              rows={1}
              className="w-full resize-none bg-gray-800 rounded-xl px-4 py-3 pr-20 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-50 disabled:cursor-not-allowed max-h-48"
              disabled={isStreaming}
              style={{ minHeight: '52px' }}
            />
            
            {/* Button container - positioned absolutely to center vertically */}
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
              {/* Microphone button */}
              <button
                className="flex items-center justify-center p-2 text-white/60 hover:text-white transition-colors rounded-lg hover:bg-gray-700"
                title="Voice input (coming soon)"
                type="button"
              >
                <MicrophoneIcon className="w-5 h-5" />
              </button>
              
              {/* Send button */}
              <button
                onClick={handleSend}
                disabled={!input.trim() || isStreaming}
                type="button"
                className={`flex items-center justify-center p-2 rounded-lg transition-all ${
                  input.trim() && !isStreaming 
                    ? 'bg-blue-600 text-white hover:bg-blue-700' 
                    : 'text-white/40 cursor-not-allowed'
                }`}
              >
                <PaperAirplaneIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Footer text */}
        <div className="mt-3 text-center text-xs text-white/50">
          HR Assistant can make mistakes. Please verify important information.
        </div>
      </div>
    </div>
  );
}