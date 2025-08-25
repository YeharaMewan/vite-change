import { useState, useCallback } from 'react';

export const useStreamingChat = () => {
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamedResponse, setStreamedResponse] = useState('');
    const [currentActivity, setCurrentActivity] = useState('');
    const [error, setError] = useState(null);

    const streamChat = useCallback(async (query, sessionId = null) => {
        setIsStreaming(true);
        setStreamedResponse('');
        setCurrentActivity('');
        setError(null);

        try {
            const response = await fetch('http://localhost:8000/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query, session_id: sessionId })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedResponse = '';

            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.content) {
                                accumulatedResponse += data.content;
                                setStreamedResponse(accumulatedResponse);
                            } else if (data.done) {
                                setIsStreaming(false);
                                setCurrentActivity('');
                                return accumulatedResponse;
                            }
                        } catch (parseError) {
                            console.warn('Failed to parse SSE data:', line, parseError);
                        }
                    }
                }
            }
            // Return the final response if streaming completes
            setIsStreaming(false);
            setCurrentActivity('');
            return accumulatedResponse;
        } catch (err) {
            console.error('Streaming failed, trying non-streaming API:', err);
            // Fallback to non-streaming API
            try {
                const response = await fetch('http://localhost:8000/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query, session_id: sessionId })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                setIsStreaming(false);
                setCurrentActivity('');
                return data.response;
            } catch (fallbackErr) {
                setError(fallbackErr.message);
                setIsStreaming(false);
                setCurrentActivity('');
                return null;
            }
        }
    }, []);

    return {
        streamChat,
        isStreaming,
        streamedResponse,
        currentActivity,
        error
    };
};