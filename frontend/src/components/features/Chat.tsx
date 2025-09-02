import { useRef, useEffect, useState } from 'react';
import { Send, Bot, User, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../../store/useAppStore';

const Chat = () => {
  // ... (all the existing state and functions remain the same) ...
  const { 
    sessionId, 
    messages, 
    isLoading, 
    addMessage, 
    startLoading, 
    stopLoading,
    startNewChat
  } = useAppStore();

  const [input, setInput] = useState('');
  const chatLogRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    chatLogRef.current?.scrollTo(0, chatLogRef.current.scrollHeight);
  }, [messages]);

  const handleSend = async () => {
    // ... (this function remains the same) ...
    if (!input.trim()) return;
    const userMessage = { role: 'user' as const, text: input };
    addMessage(userMessage);
    const currentInput = input;
    setInput('');
    startLoading();

    try {
      const res = await api.post('/chat/query', { session_id: sessionId, query: currentInput });
      const botMessage = { role: 'bot' as const, text: res.data.answer, sources: res.data.sources };
      addMessage(botMessage);
    } catch (error) {
      const errorMessage = { role: 'bot' as const, text: 'Sorry, I encountered an error.' };
      addMessage(errorMessage);
    } finally {
      stopLoading();
    }
  };

  const handleSourceClick = (source: any) => {
    // ... (this function remains the same) ...
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
              <p className="whitespace-pre-wrap">{msg.text}</p>
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
                        {/* --- THIS IS THE DEFINITIVE FIX --- */}
                        {/* We use a ternary operator to conditionally render the page number */}
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
        {isLoading && <div className="flex items-start gap-4"><Bot className="h-8 w-8 text-primary" /><div className="max-w-lg p-4 rounded-lg bg-muted">Thinking...</div></div>}
      </div>
      <div className="p-4 border-t border-muted">
        {/* ... (input section remains the same) ... */}
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