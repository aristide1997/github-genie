// Viewport utility for handling mobile keyboard behavior and dynamic viewport height
export class ViewportHandler {
  private static instance: ViewportHandler;
  private initialHeight: number;
  private isKeyboardOpen = false;
  private observers: Array<(isKeyboardOpen: boolean) => void> = [];

  private constructor() {
    this.initialHeight = window.visualViewport?.height || window.innerHeight;
    this.init();
  }

  public static getInstance(): ViewportHandler {
    if (!ViewportHandler.instance) {
      ViewportHandler.instance = new ViewportHandler();
    }
    return ViewportHandler.instance;
  }

  private init() {
    // Set initial CSS custom properties
    this.updateViewportProperties();

    // Handle visual viewport changes (mobile keyboard)
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', this.handleViewportResize);
    }

    // Fallback for older browsers
    window.addEventListener('resize', this.handleWindowResize);

    // Handle orientation changes
    window.addEventListener('orientationchange', () => {
      setTimeout(() => {
        this.updateViewportProperties();
      }, 100);
    });

    // Prevent bounce scrolling on iOS
    document.addEventListener('touchmove', this.preventBounce, { passive: false });
  }

  private handleViewportResize = () => {
    this.updateViewportProperties();
    this.detectKeyboard();
  };

  private handleWindowResize = () => {
    // Only update if visual viewport is not supported
    if (!window.visualViewport) {
      this.updateViewportProperties();
      this.detectKeyboard();
    }
  };

  private updateViewportProperties() {
    const vh = window.visualViewport?.height || window.innerHeight;
    const vw = window.visualViewport?.width || window.innerWidth;

    // Update CSS custom properties
    document.documentElement.style.setProperty('--vh', `${vh * 0.01}px`);
    document.documentElement.style.setProperty('--vw', `${vw * 0.01}px`);
    document.documentElement.style.setProperty('--viewport-height', `${vh}px`);
  }

  private detectKeyboard() {
    const currentHeight = window.visualViewport?.height || window.innerHeight;
    const heightDifference = this.initialHeight - currentHeight;
    const wasKeyboardOpen = this.isKeyboardOpen;

    // Consider keyboard open if height decreased by more than 150px
    this.isKeyboardOpen = heightDifference > 150;

    // Update body class for keyboard state
    if (this.isKeyboardOpen) {
      document.body.classList.add('keyboard-open');
    } else {
      document.body.classList.remove('keyboard-open');
    }

    // Notify observers if state changed
    if (wasKeyboardOpen !== this.isKeyboardOpen) {
      this.notifyObservers();
    }
  }

  private preventBounce = (e: TouchEvent) => {
    // Allow scrolling in scrollable containers
    const target = e.target as Element;
    const scrollableParent = target.closest('.chat-messages, .modal-content');
    
    if (!scrollableParent) {
      e.preventDefault();
    }
  };

  private notifyObservers() {
    this.observers.forEach(callback => callback(this.isKeyboardOpen));
  }

  public onKeyboardToggle(callback: (isKeyboardOpen: boolean) => void) {
    this.observers.push(callback);
    return () => {
      const index = this.observers.indexOf(callback);
      if (index > -1) {
        this.observers.splice(index, 1);
      }
    };
  }

  public getIsKeyboardOpen(): boolean {
    return this.isKeyboardOpen;
  }

  public destroy() {
    if (window.visualViewport) {
      window.visualViewport.removeEventListener('resize', this.handleViewportResize);
    }
    window.removeEventListener('resize', this.handleWindowResize);
    document.removeEventListener('touchmove', this.preventBounce);
    this.observers = [];
  }
}

// Initialize viewport handler
export const initViewport = () => {
  return ViewportHandler.getInstance();
};
