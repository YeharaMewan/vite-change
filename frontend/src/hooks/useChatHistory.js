import { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:8000';

export function useChatHistory() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Fetch details for each session to get title and preview
      const sessionsWithDetails = await Promise.all(
        data.sessions.map(async (sessionId) => {
          try {
            const sessionResponse = await fetch(`${API_BASE_URL}/sessions/${sessionId}?limit=5`);
            if (!sessionResponse.ok) {
              return {
                id: sessionId,
                title: 'Conversation',
                messages: [],
                preview: 'No messages'
              };
            }
            const sessionData = await sessionResponse.json();
            
            // Get first user message as title
            const firstUserMessage = sessionData.messages.find(msg => msg.role === 'user');
            const title = firstUserMessage ? 
              firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '') :
              'New Conversation';
            
            // Get last message as preview
            const lastMessage = sessionData.messages[sessionData.messages.length - 1];
            const preview = lastMessage ? 
              `${lastMessage.role}: ${lastMessage.content.substring(0, 100)}${lastMessage.content.length > 100 ? '...' : ''}` :
              'No messages';

            return {
              id: sessionId,
              title,
              messages: sessionData.messages,
              preview,
              timestamp: sessionData.messages[0]?.ts || new Date().toISOString()
            };
          } catch (err) {
            console.error(`Error fetching session ${sessionId}:`, err);
            return {
              id: sessionId,
              title: 'Conversation',
              messages: [],
              preview: 'Error loading messages'
            };
          }
        })
      );
      
      // Sort by timestamp (newest first)
      sessionsWithDetails.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      setSessions(sessionsWithDetails);
      setError(null);
    } catch (err) {
      console.error('Error fetching sessions:', err);
      setError(err.message);
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  const createNewSession = async (sessionId = null) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.created) {
        await fetchSessions(); // Refresh the list
      }
      return data.session_id;
    } catch (err) {
      console.error('Error creating session:', err);
      setError(err.message);
      return null;
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Remove from local state
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      setError(null);
    } catch (err) {
      console.error('Error deleting session:', err);
      setError(err.message);
    }
  };

  const getSessionMessages = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.messages;
    } catch (err) {
      console.error('Error fetching session messages:', err);
      setError(err.message);
      return [];
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  return {
    sessions,
    loading,
    error,
    refetch: fetchSessions,
    createNewSession,
    deleteSession,
    getSessionMessages,
  };
}