import React, { useEffect, useRef } from 'react';
import { useAgentUrl } from '../hooks/useAgentUrl';

interface AgentUrlModalProps {
    onClose: () => void;
}

const AgentUrlModal: React.FC<AgentUrlModalProps> = ({ onClose }) => {
    const { agentUrl, copyAgentUrl, copyStatus } = useAgentUrl();
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        // Focus the input field for easy copying
        const timer = setTimeout(() => {
            if (inputRef.current) {
                inputRef.current.focus();
                inputRef.current.select();
            }
        }, 100);

        return () => clearTimeout(timer);
    }, []);

    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [onClose]);

    const handleBackdropClick = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <div className="agent-url-modal" onClick={handleBackdropClick}>
            <div className="modal-content">
                <div className="modal-header">
                    <h3>Agent URL</h3>
                    <button className="close-button" onClick={onClose}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                    </button>
                </div>
                <div className="modal-body">
                    <p className="modal-description">
                        Use this URL to integrate GitHub Genie with A2A-compatible clients:
                    </p>
                    <div className="url-input-container">
                        <input 
                            ref={inputRef}
                            type="text" 
                            className="agent-url-input" 
                            value={agentUrl}
                            readOnly
                        />
                        <button 
                            className={`copy-button${copyStatus === 'success' ? ' copied' : ''}`}
                            onClick={copyAgentUrl}
                            title="Copy agent URL"
                            disabled={copyStatus === 'copying'}
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path d="M16 1H4C2.9 1 2 1.9 2 3V17H4V3H16V1ZM19 5H8C6.9 5 6 5.9 6 7V21C6 22.1 6.9 23 8 23H19C20.1 23 21 22.1 21 21V7C21 5.9 20.1 5 19 5ZM19 21H8V7H19V21Z" fill="currentColor"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AgentUrlModal;
