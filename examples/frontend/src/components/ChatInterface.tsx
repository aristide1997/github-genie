import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';
import type { Message as MessageType } from '../hooks/useChat';

interface ChatInterfaceProps {
    messages: MessageType[];
    isLoading: boolean;
    messagesRef: React.RefObject<HTMLDivElement | null>;
    sendMessage: (message: string) => Promise<void>;
    onShowAgentModal: () => void;
    onReturnToWelcome: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
    messages, 
    isLoading, 
    messagesRef,
    sendMessage,
    onShowAgentModal,
    onReturnToWelcome 
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
                <h1 
                    className="vt-title clickable-title" 
                    onClick={onReturnToWelcome}
                    title="Return to home"
                >
                    GitHub Genie
                </h1>
                <div className="header-buttons">
                    <a 
                        href="https://github.com/aristide1997/github-genie" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="github-button"
                        title="View on GitHub"
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
                        </svg>
                    </a>
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
