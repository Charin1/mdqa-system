import { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Send, Bot, User } from 'lucide-react';
import { api } from '../../services/api';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';

type Message = {
  role: 'user' | 'bot';
  text: string;
  sources?: any[];
};

const Chat = () => {
  const [sessionId] = useState(uuidv4());
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', text: "Hello! How can I help you with your documents today?" }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatLogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatLogRef.current?.scrollTo(0, chatLogRef.current.scrollHeight);
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage: Message = { role: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await api.post('/chat/query', { session_id: sessionId, query: input });
      const botMessage: Message = { role: 'bot', text: res.data.answer, sources: res.data.sources };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = { role: 'bot', text: 'Sorry, I encountered an error. Please try again.' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-card rounded-lg border border-muted">
      <div ref={chatLogRef} className="flex-1 p-6 overflow-y-auto space-y-6">
        {messages.map((msg, i) => (
          <div key={i} className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'bot' && <Bot className="h-8 w-8 text-primary flex-shrink-0" />}
            <div className={`max-w-2xl p-4 rounded-lg ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
              <p className="whitespace-pre-wrap">{msg.text}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 text-xs text-muted-foreground border-t border-muted-foreground/20 pt-2">
                  <strong>Sources:</strong>
                  <ul className="list-disc list-inside mt-1">
                    {msg.sources.map((s, idx) => <li key={idx}>{s.filename} (Score: {s.score})</li>)}
                  </ul>
                </div>
              )}
            </div>
            {msg.role === 'user' && <User className="h-8 w-8 text-muted-foreground flex-shrink-0" />}
          </div>
        ))}
        {isLoading && <div className="flex items-start gap-4"><Bot className="h-8 w-8 text-primary" /><div className="max-w-lg p-4 rounded-lg bg-muted">Thinking...</div></div>}
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