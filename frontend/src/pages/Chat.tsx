import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { chatAPI } from '../lib/api';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// ── Types ────────────────────────────────────────────────────────────────────
interface MemoryCitation {
  node_type: string;
  retrieval_score: number;
  hop_distance: number | string;
  snippet: string;
  properties: Record<string, any>;
  score_breakdown?: {
    graph_distance: number;
    recency: number;
    confidence: number;
    reinforcement: number;
  };
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  retrieval_ms?: number;
  llm_generation_ms?: number;
  citations?: MemoryCitation[];
}

// ── Helpers ──────────────────────────────────────────────────────────────────
const NODE_COLORS: Record<string, string> = {
  Fact: 'bg-blue-500/10 text-blue-300/80 border-blue-500/15',
  Transaction: 'bg-emerald-500/10 text-emerald-300/80 border-emerald-500/15',
  Asset: 'bg-amber-500/10 text-amber-300/80 border-amber-500/15',
  Goal: 'bg-violet-500/10 text-violet-300/80 border-violet-500/15',
  Entity: 'bg-slate-400/10 text-slate-300/70 border-slate-400/15',
  Message: 'bg-sky-500/10 text-sky-300/80 border-sky-500/15',
};

const Logo = () => (
  <div className="w-7 h-7 rounded-lg bg-indigo-950 border border-indigo-800/40 flex items-center justify-center flex-shrink-0">
    <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" strokeWidth="2.2" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3m0 14v3M2 12h3m14 0h3m-3.5-6.5-2 2m-7 7-2 2m11 0-2-2m-7-7-2-2" />
    </svg>
  </div>
);

// ── CitationCard ─────────────────────────────────────────────────────────────
function CitationCard({ c, i }: { c: MemoryCitation; i: number }) {
  const [open, setOpen] = useState(false);
  const cls = NODE_COLORS[c.node_type] ?? 'bg-zinc-500/15 text-zinc-400 border-zinc-500/20';
  const pct = Math.round(c.retrieval_score * 100);

  return (
    <div className="rounded-lg border border-white/[0.06] overflow-hidden text-xs">
      <button onClick={() => setOpen(v => !v)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-white/[0.02] hover:bg-white/[0.04] transition-colors text-left">
        <span className="text-white/20 w-4 text-right flex-shrink-0">{i + 1}</span>
        <span className={`px-1.5 py-0.5 rounded-md border text-[10px] font-semibold flex-shrink-0 ${cls}`}>{c.node_type}</span>
        <span className="flex-1 truncate text-white/50">{c.snippet || '—'}</span>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <div className="w-14 h-1 bg-white/10 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-400/70 rounded-full" style={{ width: `${pct}%` }} />
          </div>
          <span className="text-white/30 w-7 text-right">{pct}%</span>
        </div>
        <span className="text-white/25 flex-shrink-0 ml-1 text-[10px]">
          {c.hop_distance !== 'N/A' ? `${c.hop_distance}-hop` : 'direct'}
        </span>
        <svg className={`w-3 h-3 text-white/25 flex-shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div className="px-3 py-3 space-y-3 bg-[#111115] border-t border-white/[0.04]">
          {c.score_breakdown && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-white/25 mb-2">Score Breakdown</p>
              <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
                {([
                  ['Graph distance', c.score_breakdown.graph_distance],
                  ['Recency', c.score_breakdown.recency],
                  ['Confidence', c.score_breakdown.confidence],
                  ['Reinforcement', c.score_breakdown.reinforcement],
                ] as [string, number][]).map(([lbl, val]) => (
                  <div key={lbl} className="flex items-center justify-between gap-2">
                    <span className="text-white/35 truncate">{lbl}</span>
                    <div className="flex items-center gap-1.5">
                      <div className="w-10 h-1 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full bg-indigo-400/60 rounded-full" style={{ width: `${Math.round(val * 100)}%` }} />
                      </div>
                      <span className="text-white/30 w-6 text-right">{Math.round(val * 100)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {Object.keys(c.properties).length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-white/25 mb-2">Properties</p>
              <div className="space-y-1">
                {Object.entries(c.properties).map(([k, v]) =>
                  v !== undefined && v !== null && v !== '' ? (
                    <div key={k} className="flex gap-3">
                      <span className="text-white/30 capitalize min-w-[90px] flex-shrink-0">{k.replace(/_/g, ' ')}</span>
                      <span className="text-white/60 break-all">{String(v)}</span>
                    </div>
                  ) : null
                )}
              </div>
            </div>
          )}
          {c.snippet && (
            <p className="text-white/30 italic border-t border-white/[0.04] pt-2">"{c.snippet}"</p>
          )}
        </div>
      )}
    </div>
  );
}

// ── SourcesPanel ─────────────────────────────────────────────────────────────
function SourcesPanel({ citations }: { citations: MemoryCitation[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-3 pt-3 border-t border-white/[0.06]">
      <button onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 text-xs text-white/30 hover:text-white/50 transition-colors">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4.03 3-9 3S3 13.66 3 12" /><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" />
        </svg>
        <span className="font-medium">{citations.length} source{citations.length !== 1 ? 's' : ''}</span>
        <svg className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {open && (
        <div className="mt-2 space-y-1.5">
          {citations.map((c, i) => <CitationCard key={i} c={c} i={i} />)}
        </div>
      )}
    </div>
  );
}

// ── TypingDots ────────────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex gap-1 px-1 py-0.5">
      {[0, 150, 300].map(d => (
        <span key={d} className="w-1.5 h-1.5 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: `${d}ms` }} />
      ))}
    </div>
  );
}

// ── Main Chat ─────────────────────────────────────────────────────────────────
export default function Chat() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  // Auto-resize textarea
  const resizeTextarea = () => {
    const ta = inputRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
  };
  useEffect(resizeTextarea, [input]);

  // Load history
  useEffect(() => {
    const loadHistory = async () => {
      if (!user) { setIsLoadingHistory(false); return; }
      setIsLoadingHistory(true);
      try {
        const sessions = await chatAPI.getSessions();
        const session = sessions?.[0];
        if (!session) { setSessionId(null); return; }
        setSessionId(session.id);
        const history = await chatAPI.getSessionMessages(session.id);
        setMessages((history || []).map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: msg.created_at ? new Date(msg.created_at) : new Date(),
          retrieval_ms: msg.retrieval_time_ms ?? undefined,
          llm_generation_ms: msg.llm_generation_time_ms ?? undefined,
          citations: Array.isArray(msg.memory_citations) ? msg.memory_citations : undefined,
        })));
      } catch (e) { console.error('Failed to load history', e); }
      finally { setIsLoadingHistory(false); }
    };
    loadHistory();
  }, [user]);

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isSending || !user) return;
    const text = input.trim();
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsSending(true);
    try {
      const res = await chatAPI.sendMessage(text, user.user_id);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.answer || res.message || 'Processed successfully.',
        timestamp: new Date(),
        retrieval_ms: res.retrieval_metrics?.retrieval_ms,
        llm_generation_ms: res.retrieval_metrics?.llm_generation_ms,
        citations: res.memory_citations ?? undefined,
      }]);
    } catch {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), role: 'assistant', content: 'Something went wrong. Please try again.', timestamp: new Date() }]);
    } finally { setIsSending(false); }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const empty = messages.length === 0 && !isLoadingHistory;

  return (
    <div className="flex flex-col h-screen bg-[#0d0d10] text-white">

      {/* ── Header ── */}
      <header className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.06] bg-[#0d0d10]/90 backdrop-blur-md z-10 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <Logo />
          <div>
            <p className="text-sm font-semibold text-white/90 leading-tight">GraphMind</p>
            <p className="text-[11px] text-white/30">Cognitive finance assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="hidden sm:block text-right mr-1">
            <p className="text-xs font-medium text-white/70">{user?.full_name}</p>
            <p className="text-[11px] text-white/30">{user?.email}</p>
          </div>
          <button onClick={() => navigate('/mindmap')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white/50 hover:text-white/80 hover:bg-white/[0.05] border border-white/[0.06] transition-all">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="5" cy="12" r="2" /><circle cx="19" cy="5" r="2" /><circle cx="19" cy="19" r="2" />
              <path d="M7 11l10-4M7 13l10 4" />
            </svg>
            <span className="hidden sm:inline">Knowledge Graph</span>
          </button>
          <button onClick={logout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white/40 hover:text-white/70 hover:bg-white/[0.05] border border-white/[0.06] transition-all">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
            </svg>
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </header>

      {/* ── Messages ── */}
      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-5">

          {isLoadingHistory && (
            <div className="flex justify-center py-12">
              <div className="flex items-center gap-2 text-sm text-white/25">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Loading your conversation…
              </div>
            </div>
          )}

          {empty && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/[0.07] flex items-center justify-center mb-5">
                <Logo />
              </div>
              <h2 className="text-xl font-semibold text-white/80 mb-2">Start your financial conversation</h2>
              <p className="text-sm text-white/30 max-w-sm leading-relaxed">
                Share your investments, goals, or ask questions. GraphMind remembers everything and builds your knowledge graph automatically.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-8 w-full max-w-xl">
                {[
                  'I invested ₹50,000 in HDFC mutual fund',
                  'My retirement goal is ₹2 crore by 2045',
                  'What have I invested so far?',
                ].map(s => (
                  <button key={s} onClick={() => { setInput(s); inputRef.current?.focus(); }}
                    className="text-left px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-xs text-white/40 hover:text-white/60 hover:bg-white/[0.05] hover:border-white/[0.09] transition-all">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-lg bg-indigo-950 border border-indigo-800/40 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" strokeWidth="2.2" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M12 2v3m0 14v3M2 12h3m14 0h3m-3.5-6.5-2 2m-7 7-2 2m11 0-2-2m-7-7-2-2" />
                  </svg>
                </div>
              )}

              <div className={`max-w-[78%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-indigo-600/[0.18] border border-indigo-500/20 text-white/90 rounded-br-sm'
                  : 'bg-[#111114] border border-white/[0.06] text-white/80 rounded-bl-sm'
              }`}>
                {msg.role === 'assistant' ? (
                  <div className="text-sm leading-relaxed prose-sm prose-invert max-w-none
                    [&>p]:mb-2 [&>p:last-child]:mb-0
                    [&>ul]:my-2 [&>ul]:pl-4 [&>ul>li]:mb-1 [&>ul>li]:list-disc
                    [&>ol]:my-2 [&>ol]:pl-4 [&>ol>li]:mb-1 [&>ol>li]:list-decimal
                    [&>h1]:text-base [&>h1]:font-semibold [&>h1]:mb-2 [&>h1]:mt-3
                    [&>h2]:text-sm [&>h2]:font-semibold [&>h2]:mb-1.5 [&>h2]:mt-3
                    [&>h3]:text-sm [&>h3]:font-semibold [&>h3]:mb-1 [&>h3]:mt-2
                    [&>strong]:font-semibold [&>strong]:text-white/90
                    [&_strong]:font-semibold [&_strong]:text-white/90
                    [&_em]:italic [&_em]:text-white/70
                    [&>code]:px-1.5 [&>code]:py-0.5 [&>code]:rounded [&>code]:bg-white/[0.06] [&>code]:text-xs [&>code]:font-mono
                    [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:bg-white/[0.06] [&_code]:text-xs [&_code]:font-mono
                    [&>pre]:my-2 [&>pre]:p-3 [&>pre]:rounded-lg [&>pre]:bg-white/[0.04] [&>pre]:overflow-x-auto
                    [&>blockquote]:border-l-2 [&>blockquote]:border-white/20 [&>blockquote]:pl-3 [&>blockquote]:text-white/50 [&>blockquote]:my-2
                    [&>hr]:border-white/10 [&>hr]:my-3
                    [&>table]:w-full [&>table]:text-xs [&_th]:px-2 [&_th]:py-1.5 [&_th]:border-b [&_th]:border-white/10 [&_th]:text-left [&_th]:text-white/50
                    [&_td]:px-2 [&_td]:py-1.5 [&_td]:border-b [&_td]:border-white/[0.04]">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                )}

                {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                  <SourcesPanel citations={msg.citations} />
                )}

                {msg.role === 'assistant' && (msg.retrieval_ms !== undefined || msg.llm_generation_ms !== undefined) && (
                  <div className="mt-2.5 pt-2.5 border-t border-white/[0.05] flex items-center gap-4 text-[11px] text-white/25">
                    {msg.retrieval_ms !== undefined && (
                      <span className="flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                          <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
                        </svg>
                        Retrieval {Math.round(msg.retrieval_ms)}ms
                      </span>
                    )}
                    {msg.llm_generation_ms !== undefined && (
                      <span className="flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                        </svg>
                        LLM {Math.round(msg.llm_generation_ms)}ms
                      </span>
                    )}
                  </div>
                )}

                <p className={`text-[10px] mt-2 ${msg.role === 'user' ? 'text-white/25' : 'text-white/20'}`}>
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>

              {msg.role === 'user' && (
                <div className="w-7 h-7 rounded-lg bg-white/[0.06] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-3.5 h-3.5 text-white/40" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" />
                  </svg>
                </div>
              )}
            </div>
          ))}

          {isSending && (
            <div className="flex gap-3">
            <div className="w-7 h-7 rounded-lg bg-indigo-950 border border-indigo-800/40 flex items-center justify-center flex-shrink-0 mt-0.5">
              <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" strokeWidth="2.2" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v3m0 14v3M2 12h3m14 0h3m-3.5-6.5-2 2m-7 7-2 2m11 0-2-2m-7-7-2-2" />
              </svg>
            </div>
              <div className="bg-[#111114] border border-white/[0.06] rounded-2xl rounded-bl-sm px-4 py-3">
                <TypingDots />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* ── Input ── */}
      <div className="flex-shrink-0 px-4 pb-5 pt-3 border-t border-white/[0.05] bg-[#0d0d10]">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleSend}
            className="flex items-end gap-2 bg-[#111114] border border-white/[0.08] rounded-2xl px-4 py-3 focus-within:border-white/[0.14] transition-all">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question or share a memory… (Enter to send, Shift+Enter for newline)"
              disabled={isSending}
              className="flex-1 resize-none bg-transparent text-sm text-white placeholder-white/20 focus:outline-none min-h-[24px] max-h-[160px] leading-relaxed disabled:opacity-50"
            />
            <button type="submit" disabled={isSending || !input.trim()}
              className="flex-shrink-0 w-8 h-8 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-all active:scale-95">
              <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </form>
          <p className="text-center text-[10px] text-white/15 mt-2">GraphMind may make mistakes. Verify important financial decisions independently.</p>
        </div>
      </div>
    </div>
  );
}
