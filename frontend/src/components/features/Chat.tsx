import { useRef, useEffect, useState } from 'react';
import { Send, Bot, User, RefreshCw } from 'lucide-react';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../../store/useAppStore';
import { API_BASE_URL } from '../../config';

const Chat = () => {
  const { 
    sessionId, 
    messages, 
    isLoading, 
    addMessage, 
    startLoading, 
    stopLoading,
    startNewChat,
    triggerHistoryRefresh // Get the new trigger action from the store
  } = useAppStore();

  const [input, setInput] = useState('');
  const chatLogRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // A small timeout to allow the DOM to update before scrolling
    setTimeout(() => {
      chatLogRef.current?.scrollTo({ top: chatLogRef.current.scrollHeight, behavior: 'smooth' });
    }, 100);
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user' as const, text: input };
    addMessage(userMessage);
    const currentInput = input;
    setInput('');
    startLoading(); // Show the "Thinking..." UI

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, query: currentInput })
      });

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let botMessageInitialized = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n').filter(line => line.trim().startsWith('data:'));

        for (const line of lines) {
          const data = JSON.parse(line.substring(6));

          if (data.sources && !botMessageInitialized) {
            stopLoading(); // Hide "Thinking...", start streaming
            addMessage({ role: 'bot', text: '', sources: data.sources || [] });
            botMessageInitialized = true;
          }

          if (data.token) {
            if (!botMessageInitialized) {
              // Fallback in case sources arrive late or not at all
              stopLoading();
              addMessage({ role: 'bot', text: '', sources: [] });
              botMessageInitialized = true;
            }
            // Append the new token to the last message in the store
            useAppStore.setState(state => {
              const lastMessage = state.messages[state.messages.length - 1];
              if (lastMessage.role === 'bot') {
                lastMessage.text += data.token;
              }
              return { messages: [...state.messages] };
            });
          }
        }
      }
    } catch (error) {
      console.error("Streaming failed:", error);
      addMessage({ role: 'bot', text: 'Sorry, an error occurred during streaming.' });
    } finally {
      stopLoading(); // Ensure loading is always stopped
      // After the stream is finished and the conversation is saved,
      // we trigger a refresh for the history panel.
      triggerHistoryRefresh();
    }
  };

  const handleSourceClick = (source: any) => {
    if (source.doc_id && source.chunk_id) {
      navigate(`/library/${source.doc_id}?highlight=${source.chunk_id}`);
    }
  };

  return (
    <div className="h-full flex flex-col bg-card rounded-lg border border-muted">
      <div className="p-4 border-b border-muted flex justify-between items-center">
        <h2 className="text-lg font-semibold">Chat</h2>
        <Button variant="outline" size="sm" onClick={startNewChat}>
          <RefreshCw className="mr-2 h-4 w-4" />
          New Chat
        </Button>
      </div>

      <div ref={chatLogRef} className="flex-1 p-6 overflow-y-auto space-y-6">
        {messages.map((msg, i) => (
          <div key={i} className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'bot' && <Bot className="h-8 w-8 text-primary flex-shrink-0" />}
            <div className={`max-w-2xl p-4 rounded-lg ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
              <p className="whitespace-pre-wrap">{msg.text || ' '}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 text-xs border-t border-muted-foreground/20 pt-2">
                  <strong className="text-muted-foreground">Sources:</strong>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {msg.sources.map((s, idx) => (
                      <Button 
                        key={idx} 
                        variant="outline" 
                        size="sm" 
                        onClick={() => handleSourceClick(s)}
                      >
                        {s.filename}
                        {s.page ? ` (p. ${s.page})` : ''}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {msg.role === 'user' && <User className="h-8 w-8 text-muted-foreground flex-shrink-0" />}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start gap-4">
            <Bot className="h-8 w-8 text-primary flex-shrink-0" />
            <div className="max-w-lg p-4 rounded-lg bg-muted flex items-center">
              <span className="mr-2">Thinking</span>
              <span className="animate-bounce [animation-delay:-0.3s]">.</span>
              <span className="animate-bounce [animation-delay:-0.15s]">.</span>
              <span className="animate-bounce">.</span>
            </div>
          </div>
        )}
      </div>
      <div className="p-4 border-t border-muted">
        <div className="flex gap-4">
          <Input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !isLoading && handleSend()}
            placeholder="Ask a question about your documents..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={isLoading}>
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Chat;