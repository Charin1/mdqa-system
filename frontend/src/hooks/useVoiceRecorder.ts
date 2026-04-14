import { useState, useRef, useCallback } from 'react';
import { API_BASE_URL } from '../config';

interface VoiceRecorderState {
  isRecording: boolean;
  isTranscribing: boolean;
  error: string | null;
  duration: number;
}

export function useVoiceRecorder() {
  const [state, setState] = useState<VoiceRecorderState>({
    isRecording: false,
    isTranscribing: false,
    error: null,
    duration: 0,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const startRecording = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, error: null, duration: 0 }));

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // Prefer webm/opus (widely supported), fall back to whatever is available
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.start(250); // Collect data every 250ms
      startTimeRef.current = Date.now();

      // Update duration every 100ms for the UI timer
      timerRef.current = setInterval(() => {
        setState(prev => ({
          ...prev,
          duration: Math.floor((Date.now() - startTimeRef.current) / 1000),
        }));
      }, 100);

      setState(prev => ({ ...prev, isRecording: true }));
    } catch (err: any) {
      const message = err.name === 'NotAllowedError'
        ? 'Microphone access denied. Please allow microphone permissions.'
        : `Failed to start recording: ${err.message}`;
      setState(prev => ({ ...prev, error: message }));
    }
  }, []);

  const stopRecording = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current;

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        setState(prev => ({ ...prev, isRecording: false }));
        resolve(null);
        return;
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType });
        // Stop all tracks to release the microphone
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        setState(prev => ({ ...prev, isRecording: false }));
        resolve(blob);
      };

      mediaRecorder.stop();
    });
  }, []);

  const transcribe = useCallback(async (audioBlob: Blob): Promise<string> => {
    setState(prev => ({ ...prev, isTranscribing: true, error: null }));

    try {
      const formData = new FormData();
      // Determine file extension from mime type
      const ext = audioBlob.type.includes('webm') ? 'webm' : 'mp4';
      formData.append('file', audioBlob, `recording.${ext}`);

      const response = await fetch(`${API_BASE_URL}/api/voice/transcribe`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Transcription failed (${response.status})`);
      }

      const data = await response.json();
      return data.text || '';
    } catch (err: any) {
      const message = `Transcription error: ${err.message}`;
      setState(prev => ({ ...prev, error: message }));
      return '';
    } finally {
      setState(prev => ({ ...prev, isTranscribing: false }));
    }
  }, []);

  const stopAndTranscribe = useCallback(async (): Promise<string> => {
    const blob = await stopRecording();
    if (!blob || blob.size === 0) {
      setState(prev => ({ ...prev, error: 'No audio recorded.' }));
      return '';
    }
    return transcribe(blob);
  }, [stopRecording, transcribe]);

  return {
    ...state,
    startRecording,
    stopRecording,
    stopAndTranscribe,
    transcribe,
  };
}
