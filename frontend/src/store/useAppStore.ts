import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

type Message = {
  role: 'user' | 'bot';
  text: string;
  sources?: any[];
};

interface AppState {
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  // CORRECTED: Add a refresh trigger
  historyRefreshTrigger: number;
  // Voice mode toggle
  voiceEnabled: boolean;
  selectedVoice: string;
  
  addMessage: (message: Message) => void;
  startLoading: () => void;
  stopLoading: () => void;
  startNewChat: () => void;
  loadConversation: (sessionId: string, messages: Message[]) => void;
  // CORRECTED: Add an action to increment the trigger
  triggerHistoryRefresh: () => void;
  // Voice actions
  toggleVoice: () => void;
  setSelectedVoice: (id: string) => void;
  // Session metadata
  sessionTitle: string;
  setSessionTitle: (title: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: uuidv4(),
  messages: [
    { role: 'bot', text: "Hello! How can I help you with your documents today?" }
  ],
  isLoading: false,
  // CORRECTED: Initialize the trigger
  historyRefreshTrigger: 0,
  // Voice mode starts disabled
  voiceEnabled: false,
  selectedVoice: 'af_heart',
  sessionTitle: 'New Chat',
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  startLoading: () => set({ isLoading: true }),
  stopLoading: () => set({ isLoading: false }),
  startNewChat: () => set({
    sessionId: uuidv4(),
    messages: [
      { role: 'bot', text: "New chat started. How can I assist you?" }
    ],
    sessionTitle: 'New Chat',
    isLoading: false,
  }),
  loadConversation: (sessionId, messages, title) => set({
    sessionId: sessionId,
    messages: messages || [],
    sessionTitle: title || 'Past Chat',
    isLoading: false,
  }),
  // CORRECTED: Implement the trigger action
  triggerHistoryRefresh: () => set((state) => ({
    historyRefreshTrigger: state.historyRefreshTrigger + 1
  })),
  // Voice actions
  toggleVoice: () => set((state) => ({
    voiceEnabled: !state.voiceEnabled
  })),
  setSelectedVoice: (id) => set({ selectedVoice: id }),
  setSessionTitle: (title) => set({ sessionTitle: title }),
}));