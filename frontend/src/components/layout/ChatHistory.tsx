import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { useAppStore } from '../../store/useAppStore';
import { MessageSquare, Trash2 } from 'lucide-react';
import { useToast } from '../../hooks/useToast';

type Session = {
  session_id: string;
  title: string;
};

export const ChatHistory = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const { 
    loadConversation, 
    sessionId: activeSessionId, 
    historyRefreshTrigger
  } = useAppStore();
  
  const navigate = useNavigate();
  const { toast } = useToast();

  const fetchSessions = async () => {
    try {
      const res = await api.get('/chat/sessions');
      setSessions(res.data);
    } catch (error) {
      console.error("Failed to fetch chat sessions", error);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [historyRefreshTrigger]);

  const handleLoadSession = async (sessionId: string) => {
    try {
      const res = await api.get(`/chat/history/${sessionId}`);
      loadConversation(sessionId, res.data);
      navigate('/chat');
    } catch (error) {
      toast({ title: "Error", description: "Failed to load chat history.", variant: "destructive" });
      console.error("Failed to load chat history", error);
    }
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation(); 
    if (window.confirm("Are you sure you want to delete this chat history?")) {
      try {
        await api.delete(`/chat/session/${sessionId}`);
        toast({ title: "History Deleted", description: "The conversation has been removed." });
        fetchSessions();
      } catch (error) {
        toast({ title: "Error", description: "Failed to delete the conversation.", variant: "destructive" });
      }
    }
  };

  return (
    <div className="px-4 mt-6">
      <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">History</h2>
      <div className="space-y-1">
        {sessions.length === 0 && (
          <p className="text-sm text-muted-foreground px-2">No conversations yet.</p>
        )}
        {sessions.map(session => (
          <button
            key={session.session_id}
            onClick={() => handleLoadSession(session.session_id)}
            className={`w-full flex items-center justify-between text-left text-sm p-2 rounded-md transition-colors group ${
              activeSessionId === session.session_id 
                ? 'bg-muted text-foreground' 
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            }`}
          >
            <div className="flex items-center gap-2 truncate">
              <MessageSquare size={16} />
              <span className="truncate">{session.title}</span>
            </div>
            {/* --- THIS IS THE DEFINITIVE FIX --- */}
            {/* We wrap the icon in a span and apply the title attribute to the span. */}
            <span title="Delete chat">
              <Trash2 
                size={16} 
                className="flex-shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-destructive transition-opacity"
                onClick={(e) => handleDeleteSession(session.session_id, e)}
              />
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};