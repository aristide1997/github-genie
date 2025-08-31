import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { initViewport } from './utils/viewport'

// Initialize viewport handler for mobile optimization
initViewport()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
