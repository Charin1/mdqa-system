import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { useAppStore } from '../../store/useAppStore';
import { MessageSquare, Trash2, Edit2, Check, X } from 'lucide-react';
import { useToast } from '../../hooks/useToast';

type Session = {
  session_id: string;
  title: string;
};

export const ChatHistory = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  
  const { 
    loadConversation, 
    sessionId: activeSessionId, 
    historyRefreshTrigger,
    setSessionTitle
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
  const handleLoadSession = async (session: Session) => {
    // Don't switch if we're editing this session
    if (editingId === session.session_id) return;

    try {
      const res = await api.get(`/chat/history/${session.session_id}`);
      // Robustly handle both old (array) and new (object) formats
      let messages = [];
      let title = session.title;

      if (Array.isArray(res.data)) {
        // Old format: List[turn_dict]
        messages = res.data;
      } else if (res.data && typeof res.data === 'object') {
        // New format: { messages: [...], title: "...", session_id: "..." }
        messages = res.data.messages || [];
        title = res.data.title || session.title;
      }

      loadConversation(session.session_id, messages, title);
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

  const startEditing = (e: React.MouseEvent, session: Session) => {
    e.stopPropagation();
    setEditingId(session.session_id);
    setEditValue(session.title);
  };

  const cancelEditing = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    setEditingId(null);
    setEditValue('');
  };

  const saveEdit = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (!editValue.trim() || editValue === sessions.find(s => s.session_id === sessionId)?.title) {
      cancelEditing();
      return;
    }

    try {
      await api.patch(`/chat/session/${sessionId}/title`, { title: editValue.trim() });
      
      // Update local state for immediate feedback
      setSessions(prev => prev.map(s => s.session_id === sessionId ? { ...s, title: editValue.trim() } : s));
      
      // If this is the active session, update the header title via store
      if (sessionId === activeSessionId) {
        setSessionTitle(editValue.trim());
      }
      
      toast({ title: "Name Updated", description: "Chat has been renamed." });
      cancelEditing();
    } catch (error) {
      toast({ title: "Error", description: "Failed to rename chat.", variant: "destructive" });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === 'Enter') {
      saveEdit(e as any, sessionId);
    } else if (e.key === 'Escape') {
      cancelEditing();
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
          <div
            key={session.session_id}
            onClick={() => handleLoadSession(session)}
            className={`w-full flex items-center justify-between text-left text-sm p-2 rounded-md transition-colors group cursor-pointer ${
              activeSessionId === session.session_id 
                ? 'bg-muted text-foreground' 
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            }`}
          >
            <div className="flex items-center gap-2 truncate flex-1 mr-2">
              <MessageSquare size={16} className="flex-shrink-0" />
              {editingId === session.session_id ? (
                <input
                  autoFocus
                  className="bg-background border border-primary rounded px-1 w-full text-foreground focus:outline-none"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => handleKeyDown(e, session.session_id)}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="truncate">{session.title}</span>
              )}
            </div>
            
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {editingId === session.session_id ? (
                <>
                  <button 
                    title="Save"
                    onClick={(e) => saveEdit(e, session.session_id)}
                    className="hover:text-primary transition-colors"
                  >
                    <Check size={14} />
                  </button>
                  <button 
                    title="Cancel"
                    onClick={(e) => cancelEditing(e)}
                    className="hover:text-destructive transition-colors"
                  >
                    <X size={14} />
                  </button>
                </>
              ) : (
                <>
                  <button 
                    title="Rename"
                    onClick={(e) => startEditing(e, session)}
                    className="hover:text-primary transition-colors"
                  >
                    <Edit2 size={14} />
                  </button>
                  <button 
                    title="Delete"
                    onClick={(e) => handleDeleteSession(session.session_id, e)}
                    className="hover:text-destructive transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};