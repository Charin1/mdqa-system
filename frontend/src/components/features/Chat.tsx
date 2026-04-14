import { useRef, useEffect, useState } from 'react';
import { Send, Bot, User, RefreshCw, Mic, MicOff, Volume2, VolumeX, Loader2, Settings, ChevronDown } from 'lucide-react';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../../store/useAppStore';
import { API_BASE_URL } from '../../config';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { useTextToSpeech } from '../../hooks/useTextToSpeech';

interface VoicePreset {
  id: string;
  label: string;
  gender: string;
  accent: string;
}

const Chat = () => {
  const { 
    sessionId, 
    messages, 
    isLoading, 
    voiceEnabled,
    addMessage, 
    startLoading, 
    stopLoading,
    startNewChat,
    toggleVoice,
    triggerHistoryRefresh
  } = useAppStore();

  const [input, setInput] = useState('');
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState('af_heart');
  const [voices, setVoices] = useState<VoicePreset[]>([]);
  const [voicesLoading, setVoicesLoading] = useState(false);
  const chatLogRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Voice hooks
  const {
    isRecording,
    isTranscribing,
    duration,
    error: voiceError,
    startRecording,
    stopAndTranscribe,
  } = useVoiceRecorder();

  const {
    isPlaying: isTTSPlaying,
    isLoading: isTTSLoading,
    error: ttsError,
    speak,
    stop: stopTTS,
  } = useTextToSpeech();

  // Track which message is currently being spoken
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null);

  // Fetch voice presets when voice mode is enabled
  useEffect(() => {
    if (voiceEnabled && voices.length === 0) {
      setVoicesLoading(true);
      fetch(`${API_BASE_URL}/api/voice/voices`)
        .then(r => r.json())
        .then((data: VoicePreset[]) => setVoices(data))
        .catch(() => setVoices(buildDefaultVoices()))
        .finally(() => setVoicesLoading(false));
    }
  }, [voiceEnabled]);

  useEffect(() => {
    setTimeout(() => {
      chatLogRef.current?.scrollTo({ top: chatLogRef.current.scrollHeight, behavior: 'smooth' });
    }, 100);
  }, [messages]);

  // Reset speaking index when TTS stops
  useEffect(() => {
    if (!isTTSPlaying && !isTTSLoading) {
      setSpeakingIndex(null);
    }
  }, [isTTSPlaying, isTTSLoading]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user' as const, text: input };
    addMessage(userMessage);
    const currentInput = input;
    setInput('');
    startLoading();

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, query: currentInput })
      });

      if (!response.body) {
        addMessage({ role: 'bot', text: 'No response from server.' });
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let botMessageInitialized = false;
      // Buffer to accumulate partial SSE lines across read() calls
      let sseBuffer = '';

      const processEvent = (eventData: string) => {
        if (!eventData.trim()) return;
        let data: any;
        try {
          data = JSON.parse(eventData);
        } catch {
          // Ignore malformed JSON — partial line, skip silently
          return;
        }

        // Sources event — initialise the bot message bubble
        if (data.sources !== undefined && !botMessageInitialized) {
          stopLoading();
          addMessage({ role: 'bot', text: '', sources: data.sources || [] });
          botMessageInitialized = true;
        }

        // Token event — append to the last bot message
        if (data.token !== undefined) {
          if (!botMessageInitialized) {
            stopLoading();
            addMessage({ role: 'bot', text: '', sources: [] });
            botMessageInitialized = true;
          }
          useAppStore.setState(state => {
            const msgs = [...state.messages];
            const last = msgs[msgs.length - 1];
            if (last?.role === 'bot') {
              msgs[msgs.length - 1] = { ...last, text: last.text + data.token };
            }
            return { messages: msgs };
          });
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Append newly decoded bytes to the buffer
        sseBuffer += decoder.decode(value, { stream: true });

        // Process all complete SSE events (separated by \n\n)
        const parts = sseBuffer.split('\n\n');
        // The last element may be an incomplete event — keep it in the buffer
        sseBuffer = parts.pop() ?? '';

        for (const part of parts) {
          // Each SSE event may have multiple lines; find the data: line
          for (const line of part.split('\n')) {
            if (line.startsWith('data:')) {
              processEvent(line.slice(5).trim());
            }
          }
        }
      }

      // Flush any remaining buffer content after the stream closes
      if (sseBuffer.trim()) {
        for (const line of sseBuffer.split('\n')) {
          if (line.startsWith('data:')) {
            processEvent(line.slice(5).trim());
          }
        }
      }

      // If the stream ended but we never got a bot message, show an error
      if (!botMessageInitialized) {
        addMessage({ role: 'bot', text: 'I could not generate a response. Please try again.' });
      }

    } catch (error) {
      console.error("Streaming failed:", error);
      addMessage({ role: 'bot', text: 'Sorry, a network error occurred. Please try again.' });
    } finally {
      stopLoading();
      triggerHistoryRefresh();
    }
  };

  const handleMicToggle = async () => {
    if (isRecording) {
      const text = await stopAndTranscribe();
      if (text) setInput(text);
    } else {
      await startRecording();
    }
  };

  const handleReadAloud = (text: string, index: number) => {
    if (speakingIndex === index && isTTSPlaying) {
      stopTTS();
      setSpeakingIndex(null);
    } else {
      setSpeakingIndex(index);
      speak(text, selectedVoice);
    }
  };

  const handleSourceClick = (source: any) => {
    if (source.doc_id && source.chunk_id) {
      navigate(`/library/${source.doc_id}?highlight=${source.chunk_id}`);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };


  return (
    <div className="h-full flex flex-col bg-card rounded-lg border border-muted">
      {/* Header */}
      <div className="p-4 border-b border-muted flex justify-between items-center">
        <h2 className="text-lg font-semibold">Chat</h2>
        <div className="flex items-center gap-2">
          {/* Voice Mode Toggle */}
          <Button
            variant={voiceEnabled ? "primary" : "outline"}
            size="sm"
            onClick={() => { toggleVoice(); setShowVoiceSettings(false); }}
            title={voiceEnabled ? "Disable voice features" : "Enable voice features"}
          >
            {voiceEnabled ? <Volume2 className="mr-2 h-4 w-4" /> : <VolumeX className="mr-2 h-4 w-4" />}
            Voice
          </Button>

          {/* Voice Settings button — only shown when voice is enabled */}
          {voiceEnabled && (
            <Button
              variant={showVoiceSettings ? "primary" : "outline"}
              size="sm"
              onClick={() => setShowVoiceSettings(v => !v)}
              title="Voice settings"
            >
              <Settings className="h-4 w-4" />
            </Button>
          )}

          <Button variant="outline" size="sm" onClick={startNewChat}>
            <RefreshCw className="mr-2 h-4 w-4" />
            New Chat
          </Button>
        </div>
      </div>

      {/* Voice Settings Panel */}
      {voiceEnabled && showVoiceSettings && (
        <div className="px-4 py-3 border-b border-muted bg-muted/30 space-y-3">
          <h3 className="text-sm font-semibold text-foreground">Voice Settings</h3>

          {/* Voice Selector */}
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Read Aloud Voice</label>
            {voicesLoading ? (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" /> Loading voices...
              </div>
            ) : (
              <div className="relative">
                <select
                  value={selectedVoice}
                  onChange={e => setSelectedVoice(e.target.value)}
                  className="w-full appearance-none bg-background border border-muted rounded-md px-3 py-2 pr-8 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
                >
                  {(['American', 'British'] as const).map(accent => {
                    const group = voices.filter(v => v.accent === accent);
                    if (group.length === 0) return null;
                    return (
                      <optgroup key={accent} label={`${accent} Voices`}>
                        {group.map(v => (
                          <option key={v.id} value={v.id}>{v.label}</option>
                        ))}
                      </optgroup>
                    );
                  })}
                </select>
                <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Voice / TTS error banners */}
      {(voiceError || ttsError) && (
        <div className="mx-4 mt-2 p-2 text-sm text-red-400 bg-red-950/30 border border-red-800 rounded-md">
          {voiceError || ttsError}
        </div>
      )}

      {/* Chat messages */}
      <div ref={chatLogRef} className="flex-1 p-6 overflow-y-auto space-y-6">
        {messages.map((msg, i) => (
          <div key={i} className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'bot' && <Bot className="h-8 w-8 text-primary flex-shrink-0" />}
            <div className={`max-w-2xl p-4 rounded-lg ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
              <p className="whitespace-pre-wrap">{msg.text || ' '}</p>

              {/* Read Aloud button — only for bot messages when voice mode on */}
              {msg.role === 'bot' && voiceEnabled && msg.text && msg.text.trim().length > 0 && (
                <button
                  onClick={() => handleReadAloud(msg.text, i)}
                  disabled={isTTSLoading && speakingIndex !== i}
                  className="mt-2 inline-flex items-center gap-1.5 px-2 py-1 text-xs rounded-md
                    bg-muted-foreground/10 hover:bg-muted-foreground/20
                    text-muted-foreground hover:text-foreground
                    transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
                  title={speakingIndex === i && isTTSPlaying ? "Stop reading" : `Read aloud (${voices.find(v => v.id === selectedVoice)?.label || selectedVoice})`}
                >
                  {isTTSLoading && speakingIndex === i ? (
                    <><Loader2 className="h-3 w-3 animate-spin" />Loading...</>
                  ) : speakingIndex === i && isTTSPlaying ? (
                    <><VolumeX className="h-3 w-3" />Stop</>
                  ) : (
                    <><Volume2 className="h-3 w-3" />Read Aloud</>
                  )}
                </button>
              )}

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 text-xs border-t border-muted-foreground/20 pt-2">
                  <strong className="text-muted-foreground">Sources:</strong>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {msg.sources.map((s, idx) => (
                      <Button key={idx} variant="outline" size="sm" onClick={() => handleSourceClick(s)}>
                        {s.filename}{s.page ? ` (p. ${s.page})` : ''}
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

      {/* Input area */}
      <div className="p-4 border-t border-muted">
        {/* Recording indicator */}
        {isRecording && (
          <div className="mb-3 flex items-center gap-3 px-3 py-2 rounded-lg bg-red-950/30 border border-red-800">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
            </span>
            <span className="text-sm text-red-300">Recording... {formatDuration(duration)}</span>
            <span className="text-xs text-muted-foreground ml-auto">Click mic to stop & transcribe</span>
          </div>
        )}

        {/* Transcribing indicator */}
        {isTranscribing && (
          <div className="mb-3 flex items-center gap-3 px-3 py-2 rounded-lg bg-blue-950/30 border border-blue-800">
            <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
            <span className="text-sm text-blue-300">Transcribing audio...</span>
          </div>
        )}

        <div className="flex gap-2">
          <Input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !isLoading && handleSend()}
            placeholder={isRecording ? "Recording... click mic to stop" : "Ask a question about your documents..."}
            disabled={isLoading || isRecording || isTranscribing}
            className="flex-1"
          />
          {/* Mic button — only shown when voice mode is enabled */}
          {voiceEnabled && (
            <Button
              onClick={handleMicToggle}
              disabled={isLoading || isTranscribing}
              variant={isRecording ? "destructive" : "outline"}
              title={isRecording ? "Stop recording & transcribe" : "Start voice input"}
              className={isRecording ? "animate-pulse" : ""}
            >
              {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
            </Button>
          )}
          <Button onClick={handleSend} disabled={isLoading || isRecording || isTranscribing}>
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
};

// Default voices (Kokoro) used if the /voices API call fails
function buildDefaultVoices(): VoicePreset[] {
  return [
    { id: 'af_heart',    label: 'Heart (American Female)',    gender: 'Female', accent: 'American' },
    { id: 'af_bella',    label: 'Bella (American Female)',    gender: 'Female', accent: 'American' },
    { id: 'af_nicole',   label: 'Nicole (American Female)',   gender: 'Female', accent: 'American' },
    { id: 'af_sky',      label: 'Sky (American Female)',      gender: 'Female', accent: 'American' },
    { id: 'am_adam',     label: 'Adam (American Male)',       gender: 'Male',   accent: 'American' },
    { id: 'am_michael',  label: 'Michael (American Male)',    gender: 'Male',   accent: 'American' },
    { id: 'bf_emma',     label: 'Emma (British Female)',      gender: 'Female', accent: 'British'  },
    { id: 'bf_isabella', label: 'Isabella (British Female)',  gender: 'Female', accent: 'British'  },
    { id: 'bm_george',   label: 'George (British Male)',      gender: 'Male',   accent: 'British'  },
    { id: 'bm_lewis',    label: 'Lewis (British Male)',       gender: 'Male',   accent: 'British'  },
  ];
}

export default Chat;