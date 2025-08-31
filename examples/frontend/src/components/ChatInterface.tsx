import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';
import type { Message as MessageType } from '../hooks/useChat';

interface ChatInterfaceProps {
    messages: MessageType[];
    isLoading: boolean;
    messagesRef: React.RefObject<HTMLDivElement | null>;
    sendMessage: (message: string) => Promise<void>;
    onShowAgentModal: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
    messages, 
    isLoading, 
    messagesRef,
    sendMessage,
    onShowAgentModal 
}) => {
    const [inputMessage, setInputMessage] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const adjustTextareaHeight = () => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 96) + 'px';
        }
    };

    useEffect(() => {
        adjustTextareaHeight();
    }, [inputMessage]);

    useEffect(() => {
        // Focus the input when chat interface loads
        if (textareaRef.current) {
            textareaRef.current.focus();
        }
    }, []);

    const handleSendMessage = async () => {
        if (!inputMessage.trim() || isLoading) return;
        
        const messageToSend = inputMessage.trim();
        setInputMessage('');
        
        // Reset textarea height
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
        
        await sendMessage(messageToSend);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <div className="chat-container">
            <div className="chat-header">
                <h1 className="vt-title">GitHub Genie</h1>
                <button 
                    className="get-agent-button vt-get-agent" 
                    onClick={onShowAgentModal}
                    title="Get agent URL for A2A integration"
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M13 3C13.6 3 14 3.4 14 4V12L15.5 10.5C15.9 10.1 16.4 10.1 16.8 10.5C17.2 10.9 17.2 11.4 16.8 11.8L13.4 15.2C13 15.6 12.6 15.6 12.2 15.2L8.8 11.8C8.4 11.4 8.4 10.9 8.8 10.5C9.2 10.1 9.7 10.1 10.1 10.5L11.6 12V4C11.6 3.4 12 3 12.6 3H13ZM6 14C6.6 14 7 14.4 7 15V19C7 19.6 7.4 20 8 20H16C16.6 20 17 19.6 17 19V15C17 14.4 17.4 14 18 14C18.6 14 19 14.4 19 15V19C19 20.7 17.7 22 16 22H8C6.3 22 5 20.7 5 19V15C5 14.4 5.4 14 6 14Z" fill="currentColor"/>
                    </svg>
                    Get Agent
                </button>
            </div>
            
            <div className="chat-messages" ref={messagesRef}>
                {messages.map(message => (
                    <Message key={message.id} message={message} />
                ))}
            </div>
            
            <div className="chat-input-container">
                <div className="chat-input vt-input">
                    <textarea 
                        ref={textareaRef}
                        className="message-input"
                        placeholder="Send a message..." 
                        rows={1}
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isLoading}
                    />
                    <button 
                        className="send-button" 
                        onClick={handleSendMessage}
                        disabled={isLoading || !inputMessage.trim()}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                            <path d="M7 11L12 6L17 11M12 18V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
