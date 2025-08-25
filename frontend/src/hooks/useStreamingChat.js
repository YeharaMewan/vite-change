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
                                    setCurrentActivity('🔄 ' + data.message);
                                    break;
                                
                                case 'llm_start':
                                    setCurrentActivity('🤖 ' + data.message);
                                    break;
                                
                                case 'agent_start':
                                    setCurrentActivity('🔄 ' + data.message);
                                    break;
                                
                                case 'tool_start':
                                    setCurrentActivity(`🔧 Using tool: ${data.tool}`);
                                    break;
                                
                                case 'tool_end':
                                    setCurrentActivity(`✅ Tool ${data.tool} completed`);
                                    // Clear activity after a brief display
                                    setTimeout(() => setCurrentActivity(''), 1000);
                                    break;
                                
                                case 'agent_end':
                                    setCurrentActivity('✅ ' + data.message);
                                    // Clear activity after a brief display
                                    setTimeout(() => setCurrentActivity(''), 1000);
                                    break;
                                
                                case 'token':
                                    // Clear activity when tokens start flowing
                                    setCurrentActivity('');
                                    setStreamedResponse(prev => prev + data.content);
                                    break;
                                
                                case 'complete':
                                    console.log('Stream completed');
                                    setCurrentActivity('');
                                    setIsStreaming(false);
                                    return data.final_response;
                                
                                case 'error':
                                    throw new Error(data.message);
                                
                                default:
                                    console.log('Unhandled event type:', data.type, data);
                            }
                        } catch {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }
        } catch (err) {
            setError(err.message);
            setIsStreaming(false);
            setCurrentActivity('');
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