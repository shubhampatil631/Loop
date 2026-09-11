import React, { useState, useEffect, useRef } from 'react';
import { api, SessionSummary as ISessionSummary } from '../api/client';
import { MessageSquare, Send, Sparkles, AlertCircle, CheckCircle2, RotateCcw, User, BookOpen, Info, X } from 'lucide-react';

interface DailyLoopProps {
  user: { id: string; name: string; level: string; goal: string };
  mode?: 'daily_loop' | 'review_only';
  onFinishSession: (summary: ISessionSummary) => void;
}

export const DailyLoop: React.FC<DailyLoopProps> = ({ user, mode = 'daily_loop', onFinishSession }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [scenario, setScenario] = useState<string>(mode === 'review_only' ? 'Active Recall & Spaced Review' : 'Conversational Roleplay');
  const [messages, setMessages] = useState<{ role: 'agent' | 'learner'; text: string }[]>([]);
  const [inputText, setInputText] = useState('');
  const [turnCount, setTurnCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [sessionEnding, setSessionEnding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);

  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Initialize session
  useEffect(() => {
    let mounted = true;
    async function start() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.sessionStart(user.id, mode);
        if (!mounted) return;
        setSessionId(res.session_id);
        if (res.scenario) setScenario(res.scenario);
        setMessages([{ role: 'agent', text: res.agent_text }]);
        setTurnCount(0);
      } catch (err: any) {
        if (!mounted) return;
        setError(err.message || 'Failed to start session');
      } finally {
        if (mounted) setLoading(false);
      }
    }
    start();
    return () => {
      mounted = false;
    };
  }, [user.id, mode]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !sessionId || loading) return;

    const userText = inputText.trim();
    setInputText('');
    setMessages((prev) => [...prev, { role: 'learner', text: userText }]);
    setLoading(true);

    try {
      const res = await api.sessionTurn(sessionId, userText);
      setMessages((prev) => [...prev, { role: 'agent', text: res.agent_text }]);
      setTurnCount(res.turn_count);

      if (res.session_complete) {
        handleEndSession();
      }
    } catch (err: any) {
      setError(err.message || 'Error processing turn');
    } finally {
      setLoading(false);
    }
  };

  const handleEndSession = async () => {
    if (!sessionId || sessionEnding) return;
    setSessionEnding(true);
    try {
      const summary = await api.sessionEnd(sessionId);
      onFinishSession(summary);
    } catch (err: any) {
      setError(err.message || 'Error ending session');
      setSessionEnding(false);
    }
  };

  const maxTurns = 4;
  const turns = [1, 2, 3, 4];

  const renderSidebarContent = () => (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between' }}>
      <div>
        {/* Scenario Overview */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className={`badge badge-${user.level.toLowerCase()}`}>CEFR {user.level}</span>
            {mode === 'review_only' ? (
              <span className="badge badge-warning">Active Recall</span>
            ) : (
              <span className="badge badge-a1">Live Roleplay</span>
            )}
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1.3 }}>
            {scenario}
          </h2>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginTop: '6px', lineHeight: 1.5 }}>
            Immersive conversational practice calibrated to your current fluency matrix.
          </p>
        </div>

        {/* Turn Progress Checklist */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '16px', marginBottom: '20px', boxShadow: 'var(--shadow-xs)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
              Turn Progression
            </span>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--primary)' }}>
              {turnCount} of {maxTurns} Completed
            </span>
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            {turns.map((t) => {
              const isCompleted = t <= turnCount;
              const isCurrent = t === turnCount + 1;
              return (
                <div
                  key={t}
                  style={{
                    flex: 1,
                    height: '8px',
                    borderRadius: '4px',
                    backgroundColor: isCompleted ? 'var(--primary)' : isCurrent ? '#bfdbfe' : 'var(--bg-surface-subtle)',
                    border: isCurrent ? '1px solid var(--primary)' : '1px solid var(--border-subtle)',
                    transition: 'all 0.2s ease',
                  }}
                />
              );
            })}
          </div>
        </div>

        {/* Session Grounding & Pedagogical Focus */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '16px', marginBottom: '20px', boxShadow: 'var(--shadow-xs)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <BookOpen size={16} color="var(--primary)" />
            <span style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Session Objectives
            </span>
          </div>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
              <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>•</span>
              <span>Active retrieval of CEFR {user.level} vocabulary</span>
            </li>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
              <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>•</span>
              <span>Natural conversational flow & responses</span>
            </li>
            <li style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
              <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>•</span>
              <span>Silent error classification in background</span>
            </li>
          </ul>
        </div>

        {/* Tips card */}
        <div style={{ backgroundColor: 'var(--primary-light)', border: '1px solid #bfdbfe', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '4px' }}>
            <Sparkles size={14} /> Tutor Coaching Tip
          </div>
          <p style={{ fontSize: '0.8rem', color: '#1e40af', lineHeight: 1.45, margin: 0 }}>
            Don't worry about minor mistakes! Loop's memory matrix records slip-ups to re-test them later.
          </p>
        </div>
      </div>

      {/* Action Button */}
      <div style={{ paddingTop: '20px', borderTop: '1px solid var(--border-subtle)', marginTop: '20px' }}>
        <button
          onClick={() => {
            setShowMobileSidebar(false);
            handleEndSession();
          }}
          className="btn-secondary"
          disabled={sessionEnding}
          style={{ width: '100%', padding: '10px', fontSize: '0.88rem' }}
        >
          {sessionEnding ? 'Concluding Session...' : 'Finish Loop & View Digest'}
        </button>
      </div>
    </div>
  );

  return (
    <div className="studio-container">
      {/* Desktop Left Studio Sidebar */}
      <aside className="studio-sidebar-desktop">
        {renderSidebarContent()}
      </aside>

      {/* Mobile Drawer Overlay */}
      {showMobileSidebar && (
        <div className="studio-drawer-backdrop" onClick={() => setShowMobileSidebar(false)}>
          <div className="studio-drawer-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)' }}>Session Details</span>
              <button
                onClick={() => setShowMobileSidebar(false)}
                className="btn-secondary"
                style={{ padding: '4px 8px', borderRadius: '6px' }}
              >
                <X size={16} />
              </button>
            </div>
            {renderSidebarContent()}
          </div>
        </div>
      )}

      {/* Right Studio Area - Main Conversation Canvas */}
      <section className="studio-chat-section">
        {/* Top Chat Status Bar */}
        <div
          style={{
            height: '52px',
            borderBottom: '1px solid var(--border-subtle)',
            padding: '0 clamp(12px, 3vw, 32px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#ffffff',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-emerald)', flexShrink: 0 }} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              Spanish Conversation Partner
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {/* Mobile Sidebar Trigger */}
            <button
              onClick={() => setShowMobileSidebar(true)}
              className="btn-secondary"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '5px 10px',
                fontSize: '0.78rem',
                borderRadius: '6px',
              }}
              title="View session context & turn progression"
            >
              <Info size={14} />
              <span>Info ({turnCount}/{maxTurns})</span>
            </button>

            {/* Quick Finish on Mobile */}
            <button
              onClick={handleEndSession}
              disabled={sessionEnding}
              className="btn-secondary"
              style={{
                padding: '5px 10px',
                fontSize: '0.78rem',
                borderRadius: '6px',
                color: 'var(--primary)',
                borderColor: '#bfdbfe',
              }}
            >
              {sessionEnding ? 'Ending...' : 'Finish'}
            </button>
          </div>
        </div>

        {error && (
          <div style={{ backgroundColor: 'var(--accent-rose-light)', border: '1px solid var(--accent-rose)', margin: '12px clamp(12px, 3vw, 32px) 0', padding: '10px 14px', borderRadius: '10px', color: '#991b1b', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem' }}>
            <AlertCircle size={17} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Scrollable Messages Stream */}
        <div className="studio-chat-messages">
          <div style={{ maxWidth: '860px', width: '100%', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {messages.map((m, idx) => {
              const isAgent = m.role === 'agent';
              return (
                <div key={idx} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', justifyContent: isAgent ? 'flex-start' : 'flex-end' }}>
                  {isAgent && (
                    <div
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '10px',
                        backgroundColor: 'var(--primary-light)',
                        color: 'var(--primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        marginTop: '2px',
                        border: '1px solid #bfdbfe',
                      }}
                    >
                      <Sparkles size={18} />
                    </div>
                  )}

                  <div className={isAgent ? 'chat-agent' : 'chat-learner'} style={{ maxWidth: '80%' }}>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '6px',
                        fontSize: '0.74rem',
                        fontWeight: 700,
                        color: isAgent ? 'var(--text-muted)' : 'rgba(255,255,255,0.9)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                      }}
                    >
                      <span>{isAgent ? 'Conversation Partner' : user.name}</span>
                    </div>
                    <div style={{ fontSize: '1rem', lineHeight: 1.6 }}>
                      {m.text}
                    </div>
                  </div>

                  {!isAgent && (
                    <div
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '10px',
                        backgroundColor: '#e0e7ff',
                        color: 'var(--primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        marginTop: '2px',
                      }}
                    >
                      <User size={18} />
                    </div>
                  )}
                </div>
              );
            })}

            {loading && (
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '10px',
                    backgroundColor: 'var(--primary-light)',
                    color: 'var(--primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Sparkles size={18} />
                </div>
                <div className="chat-agent" style={{ padding: '14px 20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--primary)', animation: 'softPulse 1s infinite' }} />
                    <span style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Partner is composing response...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>
        </div>

        {/* Pinned Bottom Input Composer */}
        <div className="studio-input-bar">
          <div style={{ maxWidth: '860px', margin: '0 auto', width: '100%' }}>
            {/* Quick Prompts Helper */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', overflowX: 'auto', paddingBottom: '2px' }}>
              <span style={{ fontSize: '0.76rem', fontWeight: 700, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                💡 Quick Prompts:
              </span>
              {[
                'Sí, entiendo perfectamente.',
                '¿Podrías explicar los detalles?',
                'Estoy de acuerdo con la propuesta.',
                '¿Cuándo comenzamos?'
              ].map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setInputText(prompt)}
                  className="suggestion-chip"
                >
                  {prompt}
                </button>
              ))}
            </div>

            <form onSubmit={handleSend} style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <input
                type="text"
                className="input-control"
                placeholder="Respond naturally in Spanish..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={loading || sessionEnding}
                style={{ padding: '14px 18px', fontSize: '1rem', borderRadius: '12px' }}
                autoFocus
              />
              <button
                type="submit"
                className="btn-primary"
                disabled={loading || !inputText.trim() || sessionEnding}
                style={{ padding: '14px 24px', flexShrink: 0, borderRadius: '12px' }}
              >
                <Send size={18} />
                <span>Send</span>
              </button>
            </form>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px', fontSize: '0.78rem', color: 'var(--text-dim)' }}>
              <span>Multi-agent error analysis & spaced repetition tracking active</span>
              <span>Press Enter ↵ to send</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
