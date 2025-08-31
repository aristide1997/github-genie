import { generateUUID } from './uuid';

export interface A2AMessage {
    message_id: string;
    role: 'user' | 'assistant';
    parts: Array<{
        kind: 'text';
        text: string;
    }>;
    kind: 'message';
}

export interface A2ARequest {
    jsonrpc: '2.0';
    id: string;
    method: 'message/stream';
    params: {
        message: A2AMessage;
    };
}

export interface A2AStreamEvent {
    kind: 'status-update' | 'artifact-update';
    status?: {
        message: {
            parts: Array<{
                kind: 'text';
                text: string;
            }>;
        };
    };
    artifact?: {
        parts: Array<{
            kind: 'text';
            text: string;
        }>;
    };
    final?: boolean;
}

export interface A2AResponse {
    jsonrpc: '2.0';
    id: string;
    result?: A2AStreamEvent;
    error?: {
        message: string;
    };
}

// Helper to extract text from A2A message parts
export const extractTextFromParts = (parts: Array<{ kind: string; text: string }> | undefined): string => {
    if (!parts || !Array.isArray(parts)) {
        return 'No response content';
    }
    
    return parts
        .filter(part => part.kind === 'text')
        .map(part => part.text)
        .join(' ') || 'No text response';
};

// Create A2A request
export const createA2ARequest = (message: string): A2ARequest => {
    return {
        jsonrpc: '2.0',
        id: generateUUID(),
        method: 'message/stream',
        params: {
            message: {
                message_id: generateUUID(),
                role: 'user',
                parts: [{
                    kind: 'text',
                    text: message
                }],
                kind: 'message'
            }
        }
    };
};

// Send A2A request to server
export const sendA2ARequest = async (serverUrl: string, request: A2ARequest): Promise<Response> => {
    const response = await fetch(serverUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response;
};

// Process streaming response from A2A server
export const processStreamingResponse = async (
    response: Response,
    onProgress: (text: string) => void,
    onComplete: (text: string) => void,
    onError: (error: Error) => void
): Promise<void> => {
    const reader = response.body?.getReader();
    if (!reader) {
        throw new Error('Response body is not readable');
    }
    
    const decoder = new TextDecoder();
    let buffer = '';
    let hasReceivedFinalResponse = false;
    
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            // Decode the chunk and add to buffer
            buffer += decoder.decode(value, { stream: true });
            
            // Process complete JSON lines
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer
            
            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine) continue;
                
                // Handle Server-Sent Events (SSE) format
                if (trimmedLine.startsWith(':')) {
                    // SSE comment/ping - skip
                    console.log('Received SSE ping:', trimmedLine);
                    continue;
                }
                
                if (trimmedLine.startsWith('data: ')) {
                    // Extract JSON from SSE data line
                    const jsonData = trimmedLine.substring(6); // Remove "data: " prefix
                    
                    try {
                        const jsonResponse: A2AResponse = JSON.parse(jsonData);
                        console.log('Received streaming event:', jsonResponse);
                        
                        if (jsonResponse.error) {
                            throw new Error(`A2A Stream Error: ${jsonResponse.error.message}`);
                        }
                        
                        if (jsonResponse.result) {
                            const eventData = jsonResponse.result;
                            
                            if (eventData.kind === 'status-update') {
                                // Progress update from the agent
                                if (eventData.status?.message?.parts) {
                                    const progressText = extractTextFromParts(eventData.status.message.parts);
                                    onProgress(progressText);
                                }
                                
                                // Check if this is the final status update
                                if (eventData.final === true) {
                                    hasReceivedFinalResponse = true;
                                }
                                
                            } else if (eventData.kind === 'artifact-update') {
                                // Final result artifact
                                if (eventData.artifact?.parts) {
                                    const finalResponse = extractTextFromParts(eventData.artifact.parts);
                                    onComplete(finalResponse);
                                    hasReceivedFinalResponse = true;
                                }
                            }
                        }
                    } catch (parseError) {
                        console.warn('Failed to parse streaming JSON:', parseError, 'Data:', jsonData);
                        // Continue processing other lines
                    }
                } else if (trimmedLine !== 'event: message' && trimmedLine !== 'event: error') {
                    // Unknown SSE line format
                    console.log('Unknown SSE line format:', trimmedLine);
                }
            }
        }
        
        // If we didn't receive a final response, show an error
        if (!hasReceivedFinalResponse) {
            onError(new Error('Response completed but no final result was received.'));
        }
        
    } catch (streamError) {
        console.error('Streaming error:', streamError);
        onError(streamError as Error);
    } finally {
        reader.releaseLock();
    }
};
