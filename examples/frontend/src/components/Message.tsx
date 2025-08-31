import React from 'react';
import type { Message as MessageType } from '../hooks/useChat';

interface MessageProps {
    message: MessageType;
}

const Message: React.FC<MessageProps> = ({ message }) => {
    return (
        <div className={`message ${message.sender}${message.isLoading ? ' loading' : ''}`}>
            <div className="message-content">
                {message.text}
            </div>
        </div>
    );
};

export default Message;
