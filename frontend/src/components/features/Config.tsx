import { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Card } from '../ui/Card';
import { Loader } from '../ui/Loader';
import { Button } from '../ui/Button';
import { useAppStore } from '../../store/useAppStore';
import { API_BASE_URL } from '../../config';
import { Volume2, VolumeX, Settings, Loader2, ChevronDown } from 'lucide-react';

interface VoicePreset {
  id: string;
  label: string;
  gender: string;
  accent: string;
}

const Config = () => {
  const [config, setConfig] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [voices, setVoices] = useState<VoicePreset[]>([]);
  const [voicesLoading, setVoicesLoading] = useState(false);
  
  const { 
    voiceEnabled, 
    toggleVoice, 
    selectedVoice, 
    setSelectedVoice 
  } = useAppStore();

  useEffect(() => {
    api.get('/config/models')
      .then(res => setConfig(res.data))
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  // Fetch voices if enabled
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

  if (isLoading) return <Loader />;

  return (
    <div className="space-y-6 overflow-y-auto h-full pb-8">
      <h1 className="text-3xl font-bold">System Configuration</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Model Configuration */}
        <Card className="p-8">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <Settings className="h-5 w-5 text-primary" />
            Model Settings
          </h2>
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Embedding Model</h3>
              <p className="text-lg font-medium">{config?.embedding_model}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Chunking Strategy</h3>
              <div className="mt-1 flex gap-4">
                <div className="px-3 py-1 bg-muted rounded-md text-sm">
                  <span className="text-muted-foreground mr-1">Size:</span> {config?.chunk_size}
                </div>
                <div className="px-3 py-1 bg-muted rounded-md text-sm">
                  <span className="text-muted-foreground mr-1">Overlap:</span> {config?.chunk_overlap}
                </div>
              </div>
            </div>
            <p className="text-xs text-muted-foreground border-t border-muted pt-4">
              These settings are configured on the backend and apply to all new document uploads.
            </p>
          </div>
        </Card>

        {/* Voice Features Configuration */}
        <Card className="p-8 flex flex-col">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <Volume2 className="h-5 w-5 text-primary" />
            Voice Features
          </h2>
          
          <div className="space-y-6 flex-1">
            <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border border-muted">
              <div>
                <h3 className="font-semibold text-foreground">Enable Voice Mode</h3>
                <p className="text-xs text-muted-foreground">Speech-to-Text and Read Aloud features</p>
              </div>
              <Button
                variant={voiceEnabled ? "primary" : "outline"}
                onClick={toggleVoice}
                className="w-32"
              >
                {voiceEnabled ? (
                  <><Volume2 className="mr-2 h-4 w-4" /> Enabled</>
                ) : (
                  <><VolumeX className="mr-2 h-4 w-4" /> Disabled</>
                )}
              </Button>
            </div>

            {voiceEnabled && (
              <div className="animate-in fade-in slide-in-from-top-2 duration-300">
                <label className="text-sm font-semibold text-muted-foreground mb-2 block uppercase tracking-wider">
                  Preferred AI Voice
                </label>
                {voicesLoading ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                    <Loader2 className="h-4 w-4 animate-spin" /> Loading available voices...
                  </div>
                ) : (
                  <div className="relative">
                    <select
                      value={selectedVoice}
                      onChange={e => setSelectedVoice(e.target.value)}
                      className="w-full appearance-none bg-background border border-muted rounded-md px-4 py-3 pr-10 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 cursor-pointer transition-all"
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
                    <ChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  </div>
                )}
                <p className="mt-3 text-xs text-muted-foreground italic">
                  Tip: Voice mode enables audio interaction and source reading in the chat.
                </p>
              </div>
            )}
          </div>
        </Card>
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

export default Config;