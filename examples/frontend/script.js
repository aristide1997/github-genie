class ChatApp {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.isLoading = false;
        this.a2aServerUrl = window.GITHUB_GENIE_SERVER_URL || 'http://localhost:8000/';
        
        this.initializeEventListeners();
        this.adjustTextareaHeight();
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
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send (Shift+Enter for new line)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.adjustTextareaHeight());
    }
    
    adjustTextareaHeight() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 96) + 'px';
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input and reset height
        this.messageInput.value = '';
        this.adjustTextareaHeight();
        
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
        this.sendButton.disabled = loading;
        this.messageInput.disabled = loading;
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Initialize the chat app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
