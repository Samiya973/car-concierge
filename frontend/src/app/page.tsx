'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Car, ShieldCheck, CheckCircle2, Fuel, Users, CreditCard, FileText } from 'lucide-react';
import { ChatMessage, UserPreferences, RankedListing } from '@/types';
import { submitBooking } from '@/lib/api';
import CheckoutApp from '../../components/CheckoutApp';
import FormFillingApp from '../../components/FormFillingApp'; // Second MCP App

const C = {
  bg: '#FAFAF8',
  surface: '#FFFFFF',
  surfaceMuted: '#F2F1EC',
  border: '#E5E3DC',
  borderStrong: '#D8D5CC',
  textPrimary: '#16181C',
  textSecondary: '#5B5F66',
  textMuted: '#9A9D9F',
  accent: '#1F3D2B',
  accentHover: '#16301F',
  accentSoft: '#E8EFE9',
  gold: '#9A6B2A',
};

function hashSeed(id: string): number {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return h % 1000;
}

function photoUrl(category: string, id: string): string {
  const kw = (category || 'car').toLowerCase().replace(/\s+/g, '');
  return `https://loremflickr.com/640/420/${kw},automobile/all?lock=${hashSeed(id)}`;
}

function MatchGauge({ score }: { score: number }) {
  const pct = Math.min(Math.max(score, 0), 100);
  const angle = -90 + (pct / 100) * 180;
  const rad = (angle * Math.PI) / 180;
  const needleX = 50 + 32 * Math.cos(rad);
  const needleY = 55 + 32 * Math.sin(rad);
  const arcLen = 125.6;
  return (
    <div style={{ width: 58, height: 40 }} className="relative shrink-0">
      <svg viewBox="0 0 100 60" className="w-full h-full">
        <path d="M10,55 A40,40 0 0,1 90,55" fill="none" stroke={C.border} strokeWidth="7" strokeLinecap="round" />
        <path
          d="M10,55 A40,40 0 0,1 90,55"
          fill="none"
          stroke={C.accent}
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={`${(pct / 100) * arcLen} ${arcLen}`}
        />
        <line x1="50" y1="55" x2={needleX} y2={needleY} stroke={C.textPrimary} strokeWidth="2" strokeLinecap="round" />
        <circle cx="50" cy="55" r="3" fill={C.textPrimary} />
      </svg>
      <div
        className="absolute inset-x-0 bottom-0 text-center"
        style={{ fontSize: 11, fontWeight: 600, color: C.textSecondary, fontVariantNumeric: 'tabular-nums' }}
      >
        {Math.round(pct)}
      </div>
    </div>
  );
}

function SpecLabel({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="uppercase"
      style={{ fontSize: 11, fontWeight: 500, letterSpacing: '0.06em', color: C.textSecondary }}
    >
      {children}
    </span>
  );
}

export default function Home() {
  const [sessionId] = useState<string>(() => `sess_${Math.random().toString(36).substring(7)}`);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { sender: 'agent', text: "Welcome to the AI Car Matchmaker. Are you looking to buy or rent a vehicle today?" },
  ]);
  const [input, setInput] = useState('');

  const [streamingText, setStreamingText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const streamingReplyRef = useRef('');

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [preferences, setPreferences] = useState<UserPreferences>({});
  const [results, setResults] = useState<RankedListing[]>([]);
  const [stage, setStage] = useState<string>('interview');
  const [reasoningLog, setReasoningLog] = useState<{ ts: number; text: string }[]>([]);

  const [bookingForm, setBookingForm] = useState({ name: '', email: '', phone: '' });
  const [bookingDone, setBookingDone] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`ws://127.0.0.1:8000/api/chat/ws/${sessionId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'chunk') {
        setIsTyping(true);
        streamingReplyRef.current += data.text;
        setStreamingText(streamingReplyRef.current);
      } else if (data.type === 'state') {
        const finalReply = streamingReplyRef.current;
        if (finalReply) {
          setMessages((prev) => [...prev, { sender: 'agent', text: finalReply }]);
        }
        streamingReplyRef.current = '';
        setStreamingText('');
        setIsTyping(false);
        setPreferences(data.session.preferences || {});
        setResults(data.session.results || []);
        setStage(data.session.stage || 'interview');
        setReasoningLog(data.session.reasoning_log || []);
      }
    };

    wsRef.current = ws;
    return () => ws.close();
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userText = input;
    setInput('');
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(userText);
    }
  };

  const buildSheet: string[] = [];
  if (preferences.intent) buildSheet.push(preferences.intent.toUpperCase());
  if (preferences.category) buildSheet.push(preferences.category);
  if (preferences.intent !== 'rent' && preferences.budget_max) {
    buildSheet.push(`UP TO ₹${(preferences.budget_max / 100000).toFixed(1)}L`);
  } else if (preferences.intent === 'rent') {
    buildSheet.push('DAILY RATES');
  }
  if ((preferences as any).seats) buildSheet.push(`${(preferences as any).seats} SEATS`);
  if ((preferences as any).fuel_type && (preferences as any).fuel_type !== 'any') {
    buildSheet.push((preferences as any).fuel_type.toUpperCase());
  }

  return (
    <div style={{ background: C.bg, color: C.textPrimary }} className="flex flex-col h-screen overflow-hidden">
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; }
      `}</style>

      {/* TOP NAVIGATION */}
      <header
        style={{ background: C.surface, borderBottom: `1px solid ${C.border}` }}
        className="flex items-center justify-between px-6 py-3.5 shrink-0"
      >
        <div className="flex items-center gap-2.5">
          <div
            style={{ background: C.accent, width: 28, height: 28, borderRadius: 6 }}
            className="flex items-center justify-center shadow-sm"
          >
            <Car className="w-4 h-4 text-white" />
          </div>
          <span style={{ fontWeight: 600, fontSize: 15, letterSpacing: '-0.01em' }}>
            AI Car Matchmaker & Concierge
          </span>
        </div>
        {buildSheet.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap justify-end">
            <ShieldCheck style={{ color: C.accent }} className="w-4 h-4 shrink-0" />
            {buildSheet.map((item, i) => (
              <React.Fragment key={item}>
                {i > 0 && <span style={{ color: C.borderStrong }}>·</span>}
                <SpecLabel>{item}</SpecLabel>
              </React.Fragment>
            ))}
          </div>
        )}
      </header>

      {/* AGENT STATE & REASONING STRIP */}
      <div style={{ background: C.surface, borderBottom: `1px solid ${C.border}` }} className="px-6 py-3 shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {(['interview', 'research', 'recommend', 'payment', 'done'] as const).map((s, i, arr) => {
              const stageOrder = arr.indexOf(stage as any);
              const isActive = s === stage;
              const isPast = stageOrder > i;
              return (
                <React.Fragment key={s}>
                  <div className="flex items-center gap-1.5">
                    <div
                      style={{
                        width: 7,
                        height: 7,
                        borderRadius: '50%',
                        background: isActive || isPast ? C.accent : C.borderStrong,
                      }}
                    />
                    <span
                      style={{
                        fontSize: 11.5,
                        fontWeight: isActive ? 600 : 500,
                        color: isActive ? C.textPrimary : isPast ? C.textSecondary : C.textMuted,
                        textTransform: 'capitalize',
                      }}
                    >
                      {s}
                    </span>
                  </div>
                  {i < arr.length - 1 && (
                    <div style={{ width: 18, height: 1, background: isPast ? C.accent : C.border }} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                  wsRef.current.send("book");
                }
              }}
              style={{ background: C.surfaceMuted, border: `1px solid ${C.border}`, color: C.textPrimary }}
              className="px-3 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 hover:bg-gray-100 transition"
            >
              <CreditCard className="w-3.5 h-3.5 text-amber-700" /> Checkout Gateway (MCP)
            </button>
          </div>
        </div>

        {reasoningLog.length > 0 && (
          <div
            style={{ background: C.surfaceMuted, border: `1px solid ${C.border}` }}
            className="rounded-lg px-3 py-2 max-h-20 overflow-y-auto"
          >
            {reasoningLog.slice(-5).map((entry, i) => (
              <div key={i} style={{ color: C.textSecondary, fontSize: 11.5 }} className="leading-relaxed">
                <span style={{ color: C.accent, fontWeight: 600 }}>›</span> {entry.text}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* MAIN SPLIT VIEW */}
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT: CHAT & MCP RENDERERS */}
        <div style={{ borderRight: `1px solid ${C.border}`, background: C.surface }} className="w-1/2 flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((msg, index) => {
              const isUser = msg.sender === 'user';

              if (!isUser) {
                try {
                  const parsed = JSON.parse(msg.text);
                  if (parsed.type === 'mcp_app_render') {
                    if (parsed.app_name === 'CheckoutFlow') {
                      return (
                        <div key={index} className="my-3 flex justify-start w-full">
                          <CheckoutApp payload={parsed.data} />
                        </div>
                      );
                    } else if (parsed.app_name === 'FormFillingApp') {
                      return (
                        <div key={index} className="my-3 flex justify-start w-full">
                          <FormFillingApp payload={parsed.data} />
                        </div>
                      );
                    }
                    return null;
                  }
                } catch (e) {
                  // Fall through to normal text rendering
                }
              }

              return (
                <div key={index} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                  <div
                    style={
                      isUser
                        ? { background: C.accent, color: '#FFFFFF' }
                        : { background: C.surfaceMuted, color: C.textPrimary, border: `1px solid ${C.border}` }
                    }
                    className="max-w-[85%] px-4 py-3 rounded-xl text-sm leading-relaxed shadow-sm"
                  >
                    {msg.text}
                  </div>
                </div>
              );
            })}

            {isTyping && streamingText && (
              <div className="flex justify-start">
                <div
                  style={{ background: C.surfaceMuted, color: C.textPrimary, border: `1px solid ${C.border}` }}
                  className="max-w-[85%] px-4 py-3 rounded-xl text-sm leading-relaxed shadow-sm"
                >
                  {streamingText}
                  <span style={{ background: C.accent }} className="ml-1 inline-block w-1.5 h-4 animate-pulse align-middle" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form
            onSubmit={handleSend}
            style={{ borderTop: `1px solid ${C.border}`, background: C.surface }}
            className="p-4 flex gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your preferences or request..."
              style={{
                background: C.surfaceMuted,
                border: `1px solid ${C.borderStrong}`,
                color: C.textPrimary,
              }}
              className="flex-1 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2"
              onFocus={(e) => (e.currentTarget.style.boxShadow = `0 0 0 2px ${C.accentSoft}`)}
              onBlur={(e) => (e.currentTarget.style.boxShadow = 'none')}
            />
            <button
              type="submit"
              disabled={isTyping}
              style={{ background: C.accent }}
              className="w-11 h-11 rounded-xl flex items-center justify-center transition disabled:opacity-40 shrink-0 hover:opacity-90 shadow-sm"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </form>
        </div>

        {/* RIGHT: MATCHES CATALOGUE */}
        <div className="w-1/2 p-6 overflow-y-auto" style={{ background: C.bg }}>
          <div className="mb-4 flex items-center justify-between">
            <h2 style={{ fontWeight: 600, fontSize: 16 }} className="flex items-center gap-2">
              Marketplace Matches
            </h2>
            {results.length > 0 && (
              <span
                style={{ color: C.textSecondary, border: `1px solid ${C.border}`, fontVariantNumeric: 'tabular-nums', background: C.surface }}
                className="px-3 py-1 rounded-full text-xs font-semibold shadow-sm"
              >
                {results.length} vehicles verified
              </span>
            )}
          </div>

          {results.length === 0 ? (
            <div
              style={{ border: `1px dashed ${C.borderStrong}`, background: C.surface }}
              className="h-[70%] flex flex-col items-center justify-center rounded-2xl p-8 text-center shadow-sm"
            >
              <Car style={{ color: C.textMuted }} className="w-8 h-8 mb-3" />
              <h3 style={{ color: C.textPrimary }} className="text-sm font-semibold">Awaiting build sheet requirements</h3>
              <p style={{ color: C.textMuted }} className="text-xs mt-1 max-w-xs leading-relaxed">
                Chat with the concierge to define your budget, category, and use case. Ranked matches populate here instantly.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              <AnimatePresence>
                {results.map((item, idx) => (
                  <motion.div
                    key={item.listing.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.06 }}
                    style={{ background: C.surface, border: `1px solid ${C.border}` }}
                    className="rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all"
                  >
                    <div className="relative h-40 w-full" style={{ background: C.surfaceMuted }}>
                      <img
                        src={photoUrl(item.listing.category, item.listing.id)}
                        alt={`${item.listing.brand} ${item.listing.model}`}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                      <div
                        style={{ background: 'rgba(255,255,255,0.95)', border: `1px solid ${C.border}` }}
                        className="absolute top-3 right-3 rounded-xl p-1 shadow-sm"
                      >
                        <MatchGauge score={item.score} />
                      </div>
                    </div>

                    <div className="p-5">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <SpecLabel>{item.listing.category}</SpecLabel>
                        <span style={{ color: C.borderStrong }}>·</span>
                        <SpecLabel>{item.listing.fuel_type}</SpecLabel>
                        <span style={{ color: C.borderStrong }}>·</span>
                        <SpecLabel>{item.listing.condition}</SpecLabel>
                      </div>

                      <h3 style={{ fontWeight: 600, fontSize: 16 }} className="mb-1.5 text-gray-900">
                        {item.listing.brand} {item.listing.model}
                      </h3>

                      <div className="flex items-center gap-4 mb-3">
                        <span
                          style={{ color: C.gold, fontSize: 16, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}
                        >
                          ₹{item.listing.price.toLocaleString('en-IN')}
                        </span>
                        <span style={{ color: C.textSecondary }} className="flex items-center gap-1 text-xs">
                          <Users className="w-3.5 h-3.5" /> {item.listing.seats} Seats
                        </span>
                        <span style={{ color: C.textSecondary }} className="flex items-center gap-1 text-xs">
                          <Fuel className="w-3.5 h-3.5" /> {item.listing.fuel_type}
                        </span>
                      </div>

                      <p
                        style={{ background: C.surfaceMuted, color: C.textSecondary, borderLeft: `2px solid ${C.accent}` }}
                        className="text-xs px-3 py-2.5 rounded-lg mb-4 leading-relaxed"
                      >
                        {item.explanation}
                      </p>

                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                              wsRef.current.send(`book car ${idx + 1}`);
                            }
                          }}
                          style={{ background: C.accent, color: '#FFFFFF' }}
                          className="w-full font-medium text-xs py-2.5 rounded-xl transition hover:opacity-90 shadow-sm"
                        >
                          Checkout / Buy
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}