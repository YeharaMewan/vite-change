import { useState, useCallback } from 'react';

export const useStreamingChat = () => {
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamedResponse, setStreamedResponse] = useState('');
    const [error, setError] = useState(null);

    const streamChat = useCallback(async (query, sessionId = null) => {
        setIsStreaming(true);
        setStreamedResponse('');
        setError(null);

        try {
            const response = await fetch('/api/chat/stream', {
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

            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            switch (data.type) {
                                case 'start':
                                    console.log('Stream started:', data.message);
                                    break;
                                
                                case 'agent_thinking':
                                    setStreamedResponse(prev => prev + '\n🤖 ' + data.message + '\n\n');
                                    break;
                                
                                case 'token':
                                    setStreamedResponse(prev => prev + data.content);
                                    break;
                                
                                case 'complete':
                                    console.log('Stream completed');
                                    setIsStreaming(false);
                                    return data.final_response;
                                
                                case 'error':
                                    throw new Error(data.message);
                            }
                        } catch (parseError) {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }
        } catch (err) {
            setError(err.message);
            setIsStreaming(false);
        }
    }, []);

    return {
        streamChat,
        isStreaming,
        streamedResponse,
        error
    };
};