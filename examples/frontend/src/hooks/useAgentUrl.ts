import { useState, useEffect } from 'react';
import { copyToClipboard } from '../utils/clipboard';

// Custom hook for agent URL management
export const useAgentUrl = () => {
    const [agentUrl, setAgentUrl] = useState<string>('');
    const [copyStatus, setCopyStatus] = useState<'idle' | 'copying' | 'success' | 'error'>('idle');

    useEffect(() => {
        // Generate the agent card URL from the server URL
        const serverUrl = (window as any).GITHUB_GENIE_SERVER_URL || 'http://localhost:8000';
        const cleanServerUrl = serverUrl.endsWith('/') ? serverUrl.slice(0, -1) : serverUrl;
        const agentCardUrl = `${cleanServerUrl}/.well-known/agent.json`;
        
        setAgentUrl(agentCardUrl);
    }, []);

    const copyAgentUrl = async () => {
        if (copyStatus === 'copying') return;
        
        setCopyStatus('copying');
        
        try {
            const success = await copyToClipboard(agentUrl);
            setCopyStatus(success ? 'success' : 'error');
        } catch (error) {
            console.error('Failed to copy agent URL:', error);
            setCopyStatus('error');
        }
        
        // Reset status after 2 seconds
        setTimeout(() => {
            setCopyStatus('idle');
        }, 2000);
    };

    return {
        agentUrl,
        copyAgentUrl,
        copyStatus
    };
};
