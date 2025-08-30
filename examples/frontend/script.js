class ChatApp {
    constructor() {
        // State management
        this.isWelcomeState = true;
        this.isLoading = false;
        this.a2aServerUrl = window.GITHUB_GENIE_SERVER_URL || 'http://localhost:8000/';
        
        // Welcome state elements
        this.welcomeState = document.getElementById('welcomeState');
        this.welcomeMessageInput = document.getElementById('welcomeMessageInput');
        this.welcomeSendButton = document.getElementById('welcomeSendButton');
        this.getAgentButtonWelcome = document.getElementById('getAgentButtonWelcome');
        this.examplePrompts = document.querySelectorAll('.example-prompt');
        
        // Chat state elements
        this.chatInterface = document.getElementById('chatInterface');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.getAgentButton = document.getElementById('getAgentButton');
        
        // Modal elements
        this.agentUrlModal = document.getElementById('agentUrlModal');
        this.agentUrlInput = document.getElementById('agentUrlInput');
        this.copyAgentUrlButton = document.getElementById('copyAgentUrlButton');
        this.closeModalButton = document.getElementById('closeModalButton');
        
        this.initializeEventListeners();
        this.initializeAgentUrl();
        this.adjustWelcomeTextareaHeight();
    }
    
    // Generate a UUID v4
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    initializeEventListeners() {
        // Welcome state event listeners
        this.welcomeSendButton.addEventListener('click', () => this.sendWelcomeMessage());
        
        this.welcomeMessageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendWelcomeMessage();
            }
        });
        
        this.welcomeMessageInput.addEventListener('input', () => this.adjustWelcomeTextareaHeight());
        
        this.getAgentButtonWelcome.addEventListener('click', () => this.showAgentModal());
        
        // Example prompt clicks
        this.examplePrompts.forEach(prompt => {
            prompt.addEventListener('click', () => {
                const promptText = prompt.getAttribute('data-prompt');
                this.welcomeMessageInput.value = promptText;
                this.adjustWelcomeTextareaHeight();
                this.welcomeMessageInput.focus();
            });
        });
        
        // Chat state event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.messageInput.addEventListener('input', () => this.adjustTextareaHeight());
        
        this.getAgentButton.addEventListener('click', () => this.showAgentModal());
        
        // Modal event listeners
        this.closeModalButton.addEventListener('click', () => this.hideAgentModal());
        
        this.copyAgentUrlButton.addEventListener('click', () => this.copyAgentUrl());
        
        this.agentUrlModal.addEventListener('click', (e) => {
            if (e.target === this.agentUrlModal) {
                this.hideAgentModal();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.agentUrlModal.classList.contains('hidden')) {
                this.hideAgentModal();
            }
        });
    }
    
    showAgentModal() {
        this.agentUrlModal.classList.remove('hidden');
        // Focus the input field for easy copying
        setTimeout(() => {
            this.agentUrlInput.focus();
            this.agentUrlInput.select();
        }, 100);
    }
    
    hideAgentModal() {
        this.agentUrlModal.classList.add('hidden');
    }
    
    initializeAgentUrl() {
        // Generate the agent card URL from the server URL
        const serverUrl = this.a2aServerUrl.endsWith('/') ? this.a2aServerUrl.slice(0, -1) : this.a2aServerUrl;
        const agentCardUrl = `${serverUrl}/.well-known/agent.json`;
        
        // Set the agent URL in the input field
        this.agentUrlInput.value = agentCardUrl;
    }
    
    async copyAgentUrl() {
        try {
            const agentUrl = this.agentUrlInput.value;
            
            // Use the modern clipboard API if available
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(agentUrl);
            } else {
                // Fallback for older browsers
                this.agentUrlInput.select();
                this.agentUrlInput.setSelectionRange(0, 99999); // For mobile devices
                document.execCommand('copy');
                this.agentUrlInput.blur();
            }
            
            // Show visual feedback
            this.showCopyFeedback();
            
        } catch (error) {
            console.error('Failed to copy agent URL:', error);
            // Still show feedback even if copy failed
            this.showCopyFeedback(false);
        }
    }
    
    showCopyFeedback(success = true) {
        const button = this.copyAgentUrlButton;
        const originalClass = button.className;
        
        // Add success/error class
        if (success) {
            button.classList.add('copied');
        }
        
        // Remove the class after 2 seconds
        setTimeout(() => {
            button.className = originalClass;
        }, 2000);
    }
    
    adjustTextareaHeight() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 96) + 'px';
    }
    
    adjustWelcomeTextareaHeight() {
        this.welcomeMessageInput.style.height = 'auto';
        this.welcomeMessageInput.style.height = Math.min(this.welcomeMessageInput.scrollHeight, 96) + 'px';
    }
    
    async sendWelcomeMessage() {
        const message = this.welcomeMessageInput.value.trim();
        if (!message || this.isLoading) return;
        
        try {
            // Set loading state to prevent double-clicks
            this.setLoading(true);
            
            // Transition to chat interface
            await this.transitionToChatInterface();
            
            // Continue with sending the message
            await this.sendMessageCore(message);
            
        } catch (error) {
            console.error('Error during welcome message flow:', error);
            this.setLoading(false);
        }
    }
    
    async transitionToChatInterface() {
        const performSwitch = () => {
            this.welcomeState.classList.add('hidden');
            this.welcomeState.classList.remove('transitioning');
            this.chatInterface.classList.remove('hidden');
            this.isWelcomeState = false;
            setTimeout(() => {
                this.messageInput.focus();
            }, 50);
        };

        // Use View Transitions API when available and motion is allowed
        const supportsVT = typeof document.startViewTransition === 'function' &&
            !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        if (supportsVT) {
            try {
                await document.startViewTransition(() => {
                    performSwitch();
                })?.finished;
                return;
            } catch (e) {
                // fall back below
            }
        }

        // Fallback: keep existing fade for older browsers/reduced motion
        return new Promise((resolve, reject) => {
            try {
                this.welcomeState.classList.add('transitioning');
                setTimeout(() => {
                    performSwitch();
                    resolve();
                }, 300);
            } catch (error) {
                reject(error);
            }
        });
    }
    
    async sendMessageCore(message) {
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Show loading state
        this.setLoading(true);
        const progressElement = this.addMessage('Starting...', 'assistant', true);
        
        try {
            // Create A2A JSON-RPC streaming request
            const a2aRequest = {
                jsonrpc: '2.0',
                id: this.generateUUID(),
                method: 'message/stream',
                params: {
                    message: {
                        message_id: this.generateUUID(),
                        role: 'user',
                        parts: [{
                            kind: 'text',
                            text: message
                        }],
                        kind: 'message'
                    }
                }
            };
            
            // Send streaming request to A2A server
            const response = await fetch(this.a2aServerUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(a2aRequest),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Process streaming response
            await this.processStreamingResponse(response, progressElement);
            
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Remove progress message
            if (progressElement && progressElement.parentNode) {
                progressElement.remove();
            }
            
            // Show error message
            this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        } finally {
            this.setLoading(false);
        }
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;
        
        // Clear input and reset height
        this.messageInput.value = '';
        this.adjustTextareaHeight();
        
        // Use the shared core logic
        await this.sendMessageCore(message);
    }

    async processStreamingResponse(response, progressElement) {
        const reader = response.body.getReader();
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
                            const jsonResponse = JSON.parse(jsonData);
                            console.log('Received streaming event:', jsonResponse);
                            
                            if (jsonResponse.error) {
                                throw new Error(`A2A Stream Error: ${jsonResponse.error.message}`);
                            }
                            
                            if (jsonResponse.result) {
                                const handled = this.handleStreamingEvent(jsonResponse.result, progressElement);
                                if (handled === 'final') {
                                    hasReceivedFinalResponse = true;
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
            if (!hasReceivedFinalResponse && progressElement.parentNode) {
                progressElement.remove();
                this.addMessage('Response completed but no final result was received.', 'assistant');
            }
            
        } catch (streamError) {
            console.error('Streaming error:', streamError);
            // Clean up and show error
            if (progressElement.parentNode) {
                progressElement.remove();
            }
            throw streamError;
        } finally {
            reader.releaseLock();
        }
    }

    handleStreamingEvent(eventData, progressElement) {
        console.log('Processing event:', eventData);
        
        if (eventData.kind === 'status-update') {
            // Progress update from the agent
            if (eventData.status && eventData.status.message && eventData.status.message.parts) {
                const progressText = this.extractTextFromParts(eventData.status.message.parts);
                this.updateProgressMessage(progressElement, progressText);
            }
            
            // Check if this is the final status update
            if (eventData.final === true) {
                return 'final';
            }
            return 'progress';
            
        } else if (eventData.kind === 'artifact-update') {
            // Final result artifact
            if (eventData.artifact && eventData.artifact.parts) {
                const finalResponse = this.extractTextFromParts(eventData.artifact.parts);
                
                // Remove progress message and add final response
                if (progressElement.parentNode) {
                    progressElement.remove();
                }
                this.addMessage(finalResponse, 'assistant');
                return 'final';
            }
            return 'artifact';
        }
        
        return 'unknown';
    }

    updateProgressMessage(progressElement, text) {
        if (progressElement && progressElement.parentNode) {
            const contentDiv = progressElement.querySelector('.message-content');
            if (contentDiv) {
                contentDiv.textContent = text;
                this.scrollToBottom();
            }
        }
    }
    
    // Helper method to extract text from A2A message parts
    extractTextFromParts(parts) {
        if (!parts || !Array.isArray(parts)) {
            return 'No response content';
        }
        
        return parts
            .filter(part => part.kind === 'text')
            .map(part => part.text)
            .join(' ') || 'No text response';
    }
    
    addMessage(text, sender, isLoading = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}${isLoading ? ' loading' : ''}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.scrollToBottom();
        
        return messageDiv;
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        
        // Disable chat interface elements
        this.sendButton.disabled = loading;
        this.messageInput.disabled = loading;
        
        // Disable welcome interface elements
        this.welcomeSendButton.disabled = loading;
        this.welcomeMessageInput.disabled = loading;
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize the chat app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
