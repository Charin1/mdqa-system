import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

// Define the shape of a chat message
type Message = {
  role: 'user' | 'bot';
  text: string;
  sources?: any[];
};

// Define the shape of our global state
interface AppState {
  // Chat State
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  
  // Chat Actions (functions to modify the state)
  addMessage: (message: Message) => void;
  startLoading: () => void;
  stopLoading: () => void;
  startNewChat: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial State
  sessionId: uuidv4(),
  messages: [
    { role: 'bot', text: "Hello! How can I help you with your documents today?" }
  ],
  isLoading: false,
  
  // Actions
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  startLoading: () => set({ isLoading: true }),
  
  stopLoading: () => set({ isLoading: false }),
  
  startNewChat: () => set({
    sessionId: uuidv4(), // Get a new ID for the new session
    messages: [ // Reset to the initial welcome message
      { role: 'bot', text: "New chat started. How can I assist you?" }
    ],
    isLoading: false,
  }),
}));