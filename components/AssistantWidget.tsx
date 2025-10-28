
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ChatMessage } from '../types';
import { continueChat } from '../services/geminiService';
import { GoogleGenAI, LiveSession } from '@google/genai';

// Base64 encode/decode functions required for Live API
const encode = (bytes: Uint8Array) => {
  let binary = '';
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
};

// Main Component
export const AssistantWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'log'>('chat');

  return (
    <>
      <div className={`fixed bottom-6 right-6 transition-all duration-300 ${isOpen ? 'opacity-0 scale-90' : 'opacity-100 scale-100'}`}>
        <button onClick={() => setIsOpen(true)} className="bg-pcp-blue rounded-full p-4 shadow-lg hover:bg-pcp-blue/80 focus:outline-none focus:ring-2 focus:ring-pcp-blue focus:ring-offset-2 focus:ring-offset-pcp-dark">
          <IconMessageCircle className="w-8 h-8 text-white" />
        </button>
      </div>

      <div className={`fixed bottom-6 right-6 w-[400px] h-[600px] bg-pcp-light-dark border border-pcp-border rounded-lg shadow-2xl flex flex-col transition-all duration-300 origin-bottom-right ${isOpen ? 'opacity-100 scale-100' : 'opacity-0 scale-90 pointer-events-none'}`}>
        <header className="flex items-center justify-between p-3 border-b border-pcp-border flex-shrink-0">
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-pcp-text">PCP Assistant</h3>
            <div className="w-2.5 h-2.5 bg-pcp-green rounded-full animate-pulse"></div>
          </div>
          <button onClick={() => setIsOpen(false)} className="text-pcp-text-dim hover:text-pcp-text">
            <IconX className="w-5 h-5" />
          </button>
        </header>
        <div className="flex border-b border-pcp-border flex-shrink-0">
            <TabButton name="Chat" isActive={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
            <TabButton name="Live Log" isActive={activeTab === 'log'} onClick={() => setActiveTab('log')} />
        </div>
        <div className="flex-1 overflow-y-auto">
            {activeTab === 'chat' ? <ChatPanel /> : <LiveLogPanel />}
        </div>
      </div>
    </>
  );
};

const TabButton: React.FC<{ name: string; isActive: boolean; onClick: () => void }> = ({ name, isActive, onClick }) => (
    <button onClick={onClick} className={`flex-1 py-2 text-sm font-medium transition-colors ${isActive ? 'text-pcp-blue border-b-2 border-pcp-blue' : 'text-pcp-text-dim hover:bg-pcp-border/30'}`}>
        {name}
    </button>
);

const ChatPanel: React.FC = () => {
    const [messages, setMessages] = useState<ChatMessage[]>(() => {
        try {
            const savedMessages = localStorage.getItem('pcp-assistant-chat-history');
            if (savedMessages) {
                const parsedMessages = JSON.parse(savedMessages);
                if (Array.isArray(parsedMessages) && parsedMessages.length > 0) {
                    return parsedMessages;
                }
            }
        } catch (error) {
            console.error("Failed to load chat history from localStorage", error);
        }
        return [{ role: 'model', text: 'Hello! How can I help you with the PCP dashboard today?' }];
    });
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        try {
            localStorage.setItem('pcp-assistant-chat-history', JSON.stringify(messages));
        } catch (error) {
            console.error("Failed to save chat history to localStorage", error);
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;
        const newMessages: ChatMessage[] = [...messages, { role: 'user', text: input }];
        setMessages(newMessages);
        setInput('');
        setIsLoading(true);

        const response = await continueChat(newMessages);
        setMessages(prev => [...prev, { role: 'model', text: response }]);
        setIsLoading(false);
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 p-4 space-y-4 overflow-y-auto">
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${msg.role === 'user' ? 'bg-pcp-blue text-white' : 'bg-pcp-border/50 text-pcp-text'}`}>
                            {msg.text}
                        </div>
                    </div>
                ))}
                {isLoading && <div className="flex justify-start"><div className="bg-pcp-border/50 text-pcp-text rounded-lg px-3 py-2 text-sm">Thinking...</div></div>}
                <div ref={messagesEndRef} />
            </div>
            <div className="p-3 border-t border-pcp-border">
                <div className="flex items-center space-x-2">
                    <input
                        type="text"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyPress={e => e.key === 'Enter' && handleSend()}
                        placeholder="Ask PCP-Bot..."
                        className="flex-1 bg-pcp-dark border border-pcp-border rounded-md px-3 py-2 text-sm placeholder-pcp-text-dim focus:outline-none focus:ring-1 focus:ring-pcp-blue"
                    />
                    <button onClick={handleSend} disabled={isLoading} className="bg-pcp-blue p-2 rounded-md hover:bg-pcp-blue/80 disabled:opacity-50">
                        <IconSend className="w-5 h-5 text-white" />
                    </button>
                </div>
            </div>
        </div>
    );
};

const LiveLogPanel: React.FC = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcription, setTranscription] = useState('');
  const sessionPromiseRef = useRef<Promise<LiveSession> | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const mediaStreamSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  
  const stopListening = useCallback(() => {
    if (sessionPromiseRef.current) {
      sessionPromiseRef.current.then(session => session.close());
      sessionPromiseRef.current = null;
    }
    if (mediaStreamSourceRef.current) {
        mediaStreamSourceRef.current.disconnect();
        mediaStreamSourceRef.current = null;
    }
    if (scriptProcessorRef.current) {
        scriptProcessorRef.current.disconnect();
        scriptProcessorRef.current.onaudioprocess = null;
        scriptProcessorRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
        audioContextRef.current = null;
    }
    setIsListening(false);
  }, []);

  const startListening = useCallback(async () => {
    setIsListening(true);
    setTranscription('');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY as string });
      
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      mediaStreamSourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      scriptProcessorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      
      sessionPromiseRef.current = ai.live.connect({
        model: 'gemini-2.5-flash-native-audio-preview-09-2025',
        config: { inputAudioTranscription: {} },
        callbacks: {
          onopen: () => {
            console.log('Live session opened.');
            scriptProcessorRef.current!.onaudioprocess = (audioProcessingEvent) => {
              const inputData = audioProcessingEvent.inputBuffer.getChannelData(0);
              const l = inputData.length;
              const int16 = new Int16Array(l);
              for (let i = 0; i < l; i++) {
                int16[i] = inputData[i] * 32768;
              }
              const pcmBlob = {
                data: encode(new Uint8Array(int16.buffer)),
                mimeType: 'audio/pcm;rate=16000',
              };
              sessionPromiseRef.current?.then((session) => {
                session.sendRealtimeInput({ media: pcmBlob });
              });
            };
            mediaStreamSourceRef.current!.connect(scriptProcessorRef.current!);
            scriptProcessorRef.current!.connect(audioContextRef.current!.destination);
          },
          onmessage: (message) => {
            if (message.serverContent?.inputTranscription) {
              const text = message.serverContent.inputTranscription.text;
              setTranscription(prev => prev + text);
            }
          },
          onerror: (e) => {
            console.error('Live API Error:', e);
            stopListening();
          },
          onclose: () => {
            console.log('Live session closed.');
            stream.getTracks().forEach(track => track.stop());
          },
        },
      });

    } catch (error) {
      console.error('Failed to start microphone:', error);
      setIsListening(false);
    }
  }, [stopListening]);
  
  // Cleanup on component unmount
  useEffect(() => {
    return () => stopListening();
  }, [stopListening]);
  
  const handleToggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  return (
    <div className="p-4 flex flex-col h-full">
      <p className="text-sm text-pcp-text-dim mb-4">Click the microphone to start/stop dictating a log entry. The transcription will appear below in real-time.</p>
      <div className="flex-1 bg-pcp-dark border border-pcp-border rounded-md p-3 text-sm text-pcp-text font-mono overflow-y-auto">
        {transcription || <span className="text-pcp-text-dim">Waiting for audio...</span>}
      </div>
      <div className="mt-4 flex justify-center">
        <button onClick={handleToggleListening} className={`p-4 rounded-full transition-colors ${isListening ? 'bg-pcp-red/20' : 'bg-pcp-blue/20'}`}>
          {isListening ? 
            <IconMicOff className="w-8 h-8 text-pcp-red" /> :
            <IconMic className="w-8 h-8 text-pcp-blue" />
          }
        </button>
      </div>
    </div>
  );
};


// SVG Icons
const IconMessageCircle = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>;
const IconX = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>;
const IconSend = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>;
const IconMic = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line></svg>;
const IconMicOff = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="1" y1="1" x2="23" y2="23"></line><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"></path><path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"></path><line x1="12" y1="19" x2="12" y2="23"></line></svg>;
