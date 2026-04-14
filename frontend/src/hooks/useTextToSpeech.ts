import { useState, useRef, useCallback } from 'react';
import { API_BASE_URL } from '../config';

interface TTSState {
  isLoading: boolean;
  isPlaying: boolean;
  error: string | null;
}

export function useTextToSpeech() {
  const [state, setState] = useState<TTSState>({
    isLoading: false,
    isPlaying: false,
    error: null,
  });

  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null);

  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
      audioContextRef.current = new AudioContext();
    }
    // Resume if suspended (browsers require user interaction first)
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume();
    }
    return audioContextRef.current;
  }, []);

  const stop = useCallback(() => {
    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.stop();
      } catch {
        // Already stopped
      }
      sourceNodeRef.current = null;
    }
    setState(prev => ({ ...prev, isPlaying: false }));
  }, []);

  const speak = useCallback(async (text: string, voice?: string) => {
    // Stop any currently playing audio
    stop();

    setState({ isLoading: true, isPlaying: false, error: null });

    try {
      const response = await fetch(`${API_BASE_URL}/api/voice/synthesize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: voice || undefined }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `TTS failed (${response.status})`);
      }

      const arrayBuffer = await response.arrayBuffer();
      const audioContext = getAudioContext();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      const sourceNode = audioContext.createBufferSource();
      sourceNode.buffer = audioBuffer;
      sourceNode.connect(audioContext.destination);

      sourceNode.onended = () => {
        sourceNodeRef.current = null;
        setState(prev => ({ ...prev, isPlaying: false }));
      };

      sourceNodeRef.current = sourceNode;
      sourceNode.start();

      setState({ isLoading: false, isPlaying: true, error: null });
    } catch (err: any) {
      const message = `TTS error: ${err.message}`;
      setState({ isLoading: false, isPlaying: false, error: message });
    }
  }, [stop, getAudioContext]);

  return {
    ...state,
    speak,
    stop,
  };
}
