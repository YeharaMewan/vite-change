import { useState } from 'react';
import { 
  PlusIcon, 
  MagnifyingGlassIcon,
  ChevronLeftIcon,
  ChatBubbleLeftIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

export default function Sidebar({ isOpen, onToggle, onNewChat, chatHistory = [], onChatSelect, onDeleteChat, loading, error }) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredChats = chatHistory.filter(chat =>
    chat.title?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <div className={`${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } fixed inset-y-0 left-0 z-40 w-80 transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 flex flex-col sidebar-transition bg-gray-800`}>
        
        {/* Sidebar Header with Toggle */}
        <div className="flex items-center justify-between p-4">
          <h2 className="text-lg font-semibold text-white">
            HR Assistant
          </h2>
          <button
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-gray-800 transition-colors text-white lg:hidden"
            title="Close Sidebar"
          >
            <ChevronLeftIcon className="w-5 h-5" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-3 p-3 rounded-lg transition-colors hover:bg-gray-800 text-white"
          >
            <PlusIcon className="w-5 h-5" />
            <span>New chat</span>
          </button>
        </div>

        {/* Search Chats */}
        <div className="px-4 pb-4">
          <div className="relative">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search chats"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-white placeholder-gray-400"
            />
          </div>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto px-4 pb-4 sidebar-scrollbar">
          <div className="space-y-2">
            <h3 className="text-xs font-semibold mb-3 px-3 text-gray-400">
              Recent
            </h3>
            
            {loading ? (
              <div className="px-3 py-4 text-sm text-gray-400 flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                Loading conversations...
              </div>
            ) : error ? (
              <div className="px-3 py-4 text-sm text-red-400">
                Error loading conversations: {error}
              </div>
            ) : filteredChats.length > 0 ? (
              filteredChats.map((chat, index) => (
                <div key={chat.id || index} className="group relative">
                  <button
                    onClick={() => onChatSelect && onChatSelect(chat.id)}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors hover:bg-gray-800 text-white ${
                      index === 0 ? 'bg-gray-800' : ''
                    }`}
                  >
                    <ChatBubbleLeftIcon className="w-4 h-4 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm truncate">
                        {chat.title || 'New conversation'}
                      </div>
                      {chat.preview && (
                        <div className="text-xs text-gray-400 truncate mt-1">
                          {chat.preview}
                        </div>
                      )}
                    </div>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteChat && onDeleteChat(chat.id);
                    }}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 rounded opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 transition-all"
                    title="Delete conversation"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              <div className="px-3 py-4 text-sm text-gray-400">
                {searchQuery ? 'No matching conversations' : 'No conversations yet'}
              </div>
            )}

          </div>
        </div>
      </div>

      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden" 
          onClick={onToggle}
        />
      )}
    </>
  );
}