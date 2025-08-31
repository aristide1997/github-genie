import { useState, useCallback, useRef } from 'react';
import { createA2ARequest, sendA2ARequest, processStreamingResponse } from '../utils/api';

export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'assistant';
    isLoading?: boolean;
}

// Custom hook for chat functionality
export const useChat = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const messagesRef = useRef<HTMLDivElement>(null);
    const progressMessageIdRef = useRef<string | null>(null);

    const scrollToBottom = useCallback(() => {
        if (messagesRef.current) {
            messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
        }
    }, []);

    const addMessage = useCallback((text: string, sender: 'user' | 'assistant', isLoading = false): string => {
        const messageId = `msg-${Date.now()}-${Math.random()}`;
        const newMessage: Message = {
            id: messageId,
            text,
            sender,
            isLoading
        };
        
        setMessages(prev => [...prev, newMessage]);
        
        // Scroll to bottom after message is added
        setTimeout(scrollToBottom, 50);
        
        return messageId;
    }, [scrollToBottom]);

    const updateMessage = useCallback((messageId: string, text: string) => {
        setMessages(prev => prev.map(msg => 
            msg.id === messageId ? { ...msg, text } : msg
        ));
        scrollToBottom();
    }, [scrollToBottom]);

    const removeMessage = useCallback((messageId: string) => {
        setMessages(prev => prev.filter(msg => msg.id !== messageId));
    }, []);

    const sendMessage = useCallback(async (message: string) => {
        if (!message.trim() || isLoading) return;
        
        try {
            setIsLoading(true);
            
            // Add user message
            addMessage(message, 'user');
            
            // Add loading message for assistant
            const progressMessageId = addMessage('Starting...', 'assistant', true);
            progressMessageIdRef.current = progressMessageId;
            
            // Get server URL
            const serverUrl = (window as any).GITHUB_GENIE_SERVER_URL || 'http://localhost:8000';
            
            // Create and send A2A request
            const a2aRequest = createA2ARequest(message);
            const response = await sendA2ARequest(serverUrl, a2aRequest);
            
            // Process streaming response
            await processStreamingResponse(
                response,
                // onProgress
                (progressText: string) => {
                    if (progressMessageIdRef.current) {
                        updateMessage(progressMessageIdRef.current, progressText);
                    }
                },
                // onComplete
                (finalText: string) => {
                    if (progressMessageIdRef.current) {
                        // Remove progress message and add final response
                        removeMessage(progressMessageIdRef.current);
                        progressMessageIdRef.current = null;
                    }
                    addMessage(finalText, 'assistant');
                },
                // onError
                (error: Error) => {
                    console.error('Chat error:', error);
                    
                    // Remove progress message
                    if (progressMessageIdRef.current) {
                        removeMessage(progressMessageIdRef.current);
                        progressMessageIdRef.current = null;
                    }
                    
                    // Show error message
                    addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
                }
            );
            
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Clean up progress message
            if (progressMessageIdRef.current) {
                removeMessage(progressMessageIdRef.current);
                progressMessageIdRef.current = null;
            }
            
            // Show error message
            addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        } finally {
            setIsLoading(false);
        }
    }, [isLoading, addMessage, updateMessage, removeMessage]);

    return {
        messages,
        isLoading,
        messagesRef,
        sendMessage,
        scrollToBottom
    };
};
