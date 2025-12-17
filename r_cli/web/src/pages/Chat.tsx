import { useState, useRef, useEffect } from 'react';
import api from '../api/client';
import VoiceButton from '../components/VoiceButton';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  skill?: string;
  tools?: string[];
  isVoice?: boolean;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [voiceMode, setVoiceMode] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check voice system status on mount
  useEffect(() => {
    async function checkVoiceStatus() {
      try {
        const response = await fetch(`${API_BASE}/v1/voice/status`);
        const data = await response.json();
        setVoiceEnabled(data.ready === true);
      } catch {
        setVoiceEnabled(false);
      }
    }
    checkVoiceStatus();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    await sendMessage(input.trim(), false);
  }

  async function sendMessage(text: string, isVoice: boolean) {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      isVoice,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response = await api.chat({ message: text });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        skill: response.skill_used || undefined,
        tools: response.tools_called,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // If voice mode is active, speak the response
      if (voiceMode && voiceEnabled) {
        await speakText(response.response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setLoading(false);
    }
  }

  async function speakText(text: string) {
    try {
      // Limit text length for TTS
      const truncatedText = text.slice(0, 500);

      const response = await fetch(
        `${API_BASE}/v1/voice/speak?text=${encodeURIComponent(truncatedText)}&voice=M1`,
        { method: 'POST' }
      );

      if (!response.ok) {
        console.error('TTS failed:', response.statusText);
        return;
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
      }
    } catch (err) {
      console.error('Failed to speak:', err);
    }
  }

  function handleVoiceTranscript(text: string) {
    // When voice input is received, send it as a message
    sendMessage(text, true);
  }

  function handleClear() {
    setMessages([]);
    setError(null);
  }

  function toggleVoiceMode() {
    setVoiceMode(!voiceMode);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      {/* Hidden audio element for TTS playback */}
      <audio ref={audioRef} className="hidden" />

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-white">Chat</h1>
          {voiceEnabled && (
            <button
              onClick={toggleVoiceMode}
              className={`flex items-center gap-2 px-3 py-1 text-sm rounded transition-colors ${
                voiceMode
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
              }`}
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
              </svg>
              {voiceMode ? 'Voice ON' : 'Voice OFF'}
            </button>
          )}
        </div>
        <button
          onClick={handleClear}
          className="px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition-colors"
        >
          Clear Chat
        </button>
      </div>

      {/* Voice Mode Banner */}
      {voiceMode && (
        <div className="mb-4 p-3 bg-green-900/30 border border-green-600 rounded-lg flex items-center gap-3">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
          <span className="text-green-400 text-sm">
            Voice mode active - Click the microphone to speak, AI will respond with voice
          </span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-slate-800 rounded-lg border border-slate-700 p-4 mb-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <span className="text-4xl mb-4">💬</span>
            <p>Start a conversation with R CLI</p>
            <p className="text-sm mt-2">Your local AI agent with 81 skills</p>
            {voiceEnabled && (
              <p className="text-sm mt-4 text-green-400">
                Voice chat available - toggle Voice Mode above
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-100'
                  }`}
                >
                  {message.isVoice && (
                    <div className="flex items-center gap-1 mb-2 text-xs opacity-70">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                      </svg>
                      Voice input
                    </div>
                  )}
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.skill && (
                    <div className="mt-2 pt-2 border-t border-slate-600 text-xs text-slate-400">
                      Skill: {message.skill}
                      {message.tools && message.tools.length > 0 && (
                        <span> • Tools: {message.tools.join(', ')}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-700 rounded-lg p-4 text-slate-400">
                  <span className="animate-pulse">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-500 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        {/* Voice Button */}
        {voiceEnabled && voiceMode && (
          <VoiceButton
            onTranscript={handleVoiceTranscript}
            disabled={loading}
            silenceTimeout={2000}
            apiBase={API_BASE}
          />
        )}

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={voiceMode ? "Type or use the microphone..." : "Type your message..."}
          className="flex-1 px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}
