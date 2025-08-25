import ReactMarkdown from 'react-markdown';

const ActionMessage = ({ action }) => {
  if (action.action_type === 'download_report') {
    return (
      <a 
        href={action.url} 
        target="_blank" 
        rel="noopener noreferrer"
        className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors mt-3"
      >
        📄 Download Report
      </a>
    );
  }
  return null;
};

export default function ChatMessage({ message, isStreaming = false }) {
  const isUser = message.sender === 'user';

  return (
    <div className="group w-full bg-gray-900 py-4">
      <div className="max-w-4xl mx-auto px-4">
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
          {/* Message Content */}
          <div className={`max-w-2xl ${isUser ? 'text-right' : 'text-left'}`}>
            <div className={`inline-block p-4 rounded-2xl shadow-sm ${
              isUser 
                ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                : 'bg-gray-800 hover:bg-gray-700 text-white'
            } transition-colors duration-200`}>
              {/* Message Text */}
              {message.text && (
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p className="mb-2 last:mb-0 text-white">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc list-inside mb-2 text-white">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside mb-2 text-white">{children}</ol>,
                      li: ({ children }) => <li className="mb-1 text-white">{children}</li>,
                      strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                      em: ({ children }) => <em className="italic text-white">{children}</em>,
                      code: ({ children }) => <code className="bg-gray-700 px-1 py-0.5 rounded text-sm text-white">{children}</code>,
                      pre: ({ children }) => <pre className="bg-gray-700 p-3 rounded-lg overflow-x-auto text-sm text-white">{children}</pre>,
                      h1: ({ children }) => <h1 className="text-xl font-bold mb-2 text-white">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-lg font-bold mb-2 text-white">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-md font-bold mb-2 text-white">{children}</h3>,
                    }}
                  >
                    {message.text}
                  </ReactMarkdown>
                </div>
              )}
              
              {/* Action Messages (for download buttons, etc.) */}
              {message.action && <ActionMessage action={message.action} />}
              
              {/* Streaming indicator */}
              {isStreaming && (
                <div className="flex items-center mt-2">
                  <div className="inline-block w-2 h-5 bg-blue-400 animate-pulse rounded-sm"></div>
                </div>
              )}
            </div>

            {/* Timestamp */}
            {message.timestamp && (
              <div className={`text-xs text-gray-400 mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ${
                isUser ? 'text-right' : 'text-left'
              }`}>
                {message.timestamp}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}