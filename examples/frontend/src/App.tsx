import { useState } from 'react';
import WelcomeState from './components/WelcomeState';
import ChatInterface from './components/ChatInterface';
import AgentUrlModal from './components/AgentUrlModal';
import { useChat } from './hooks/useChat';
import { useViewTransition } from './hooks/useViewTransition';
import './styles/index.css';

function App() {
  const [isWelcomeState, setIsWelcomeState] = useState(true);
  const [showAgentModal, setShowAgentModal] = useState(false);
  
  const chat = useChat();
  const { startTransition } = useViewTransition();

  const handleWelcomeMessage = async (message: string) => {
    // Transition to chat interface using View Transitions API
    await startTransition(() => {
      setIsWelcomeState(false);
    });
    
    // Send the message after the transition
    await chat.sendMessage(message);
  };

  const handleShowAgentModal = () => {
    setShowAgentModal(true);
  };

  const handleCloseAgentModal = () => {
    setShowAgentModal(false);
  };

  const handleReturnToWelcome = () => {
    setIsWelcomeState(true);
    chat.clearMessages();
  };

  return (
    <>
      {isWelcomeState ? (
        <WelcomeState 
          onSendMessage={handleWelcomeMessage}
          onShowAgentModal={handleShowAgentModal}
          isLoading={chat.isLoading}
        />
      ) : (
        <ChatInterface 
          messages={chat.messages}
          isLoading={chat.isLoading}
          messagesRef={chat.messagesRef}
          sendMessage={chat.sendMessage}
          onShowAgentModal={handleShowAgentModal}
          onReturnToWelcome={handleReturnToWelcome}
        />
      )}
      
      {showAgentModal && (
        <AgentUrlModal 
          onClose={handleCloseAgentModal}
        />
      )}
    </>
  );
}

export default App;
