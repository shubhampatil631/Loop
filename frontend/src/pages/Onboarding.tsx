import React, { useState } from 'react';
import { api } from '../api/client';
import { Sparkles, ArrowRight, CheckCircle2, MessageSquare, Compass, Award, User, Clock, TrendingUp, BookOpen } from 'lucide-react';

interface OnboardingProps {
  onComplete: (user: { id: string; name: string; level: string; goal: string }) => void;
}

export const Onboarding: React.FC<OnboardingProps> = ({ onComplete }) => {
  const [step, setStep] = useState<'profile' | 'chat' | 'complete'>('profile');
  const [name, setName] = useState('');
  const [goal, setGoal] = useState('travel');
  const [dailyMinutes, setDailyMinutes] = useState('15');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [userId, setUserId] = useState('');
  const [placementSessionId, setPlacementSessionId] = useState('');
  const [messages, setMessages] = useState<{ role: 'agent' | 'learner'; text: string }[]>([]);
  const [inputText, setInputText] = useState('');
  const [assessedLevel, setAssessedLevel] = useState('A1');
  const [assessmentNotes, setAssessmentNotes] = useState('');

  const handleStartPlacement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.onboardingStart(name.trim(), 'es', goal);
      setUserId(res.user_id);
      setPlacementSessionId(res.placement_session_id);
      setMessages([{ role: 'agent', text: res.greeting || '¡Hola! ¿Cómo te llamas y por qué quieres aprender español?' }]);
      setStep('chat');
    } catch (err: any) {
      setError(err.message || 'Failed to start onboarding');
    } finally {
      setLoading(false);
    }
  };

  const handleSendTurn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;

    const userMsg = inputText.trim();
    setInputText('');
    setMessages((prev) => [...prev, { role: 'learner', text: userMsg }]);
    setLoading(true);

    try {
      const res = await api.onboardingPlacementTurn(placementSessionId, userMsg);
      setMessages((prev) => [...prev, { role: 'agent', text: res.agent_text }]);

      if (res.placement_complete) {
        const lvl = res.level || 'A1';
        setAssessedLevel(lvl);
        setAssessmentNotes(res.notes || 'Baseline proficiency established');
        setStep('complete');
      }
    } catch (err: any) {
      setError(err.message || 'Error processing turn');
    } finally {
      setLoading(false);
    }
  };

  const goalOptions = [
    {
      id: 'travel',
      title: 'Travel & Dining',
      desc: 'Order food, navigate transit, book accommodations, and handle spontaneous travel scenarios with ease.',
      icon: Compass,
      tag: 'Most Popular',
    },
    {
      id: 'work',
      title: 'Career & Workplace',
      desc: 'Professional greetings, formal emails, team meetings, client negotiation, and industry vocabulary.',
      icon: Award,
      tag: 'Professional',
    },
    {
      id: 'family',
      title: 'Culture & Daily Life',
      desc: 'Everyday conversations, socializing with native speakers, idiomatic expressions, and local culture.',
      icon: MessageSquare,
      tag: 'Conversational',
    },
  ];

  return (
    <div className="onboarding-container">
      {/* Left Feature Showcase Panel (Responsive) */}
      <aside className="onboarding-aside">
        <div>
          {/* Logo & Headline */}
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', padding: '5px 12px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 700, marginBottom: '16px' }}>
            <Sparkles size={15} /> Cognitive AI Language Tutor
          </div>

          <h1 style={{ fontSize: 'clamp(1.5rem, 3.5vw, 2.1rem)', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1.25, marginBottom: '14px', letterSpacing: '-0.03em' }}>
            Master Fluent Spanish Through Real Conversation
          </h1>

          <p style={{ color: 'var(--text-muted)', fontSize: '0.94rem', lineHeight: 1.6, marginBottom: '28px' }}>
            Unlike rote flashcard apps, Loop orchestrates adaptive AI conversational partners that remember your grammatical slips and strategically re-trigger them until they become second nature.
          </p>

          {/* 3 Value Pillars */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div className="feature-showcase-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Compass size={17} />
                </div>
                <div style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  LangGraph Multi-Agent Orchestration
                </div>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: 0 }}>
                Specialized agents work concurrently: the Conversation Partner talks naturally, the Error Classifier diagnoses grammar in real-time, and the Curriculum Agent plans spaced recall.
              </p>
            </div>

            <div className="feature-showcase-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: 'var(--accent-emerald-light)', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <TrendingUp size={17} />
                </div>
                <div style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  FSRS-4.5 Spaced Memory Matrix
                </div>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: 0 }}>
                Vocabulary decay is mathematically calculated. Words due for review are naturally woven into your next roleplay dialogue so you never have to do boring card drills.
              </p>
            </div>

            <div className="feature-showcase-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: 'var(--accent-amber-light)', color: 'var(--accent-amber)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <CheckCircle2 size={17} />
                </div>
                <div style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  Zero-Anxiety Mistake Retriggering
                </div>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: 0 }}>
                Made a gender agreement slip? The partner never interrupts awkwardly; the system tags the error and provides pedagogical guidance in your post-session digest.
              </p>
            </div>
          </div>
        </div>

        {/* CEFR Roadmap Footer */}
        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '20px', marginTop: '28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', flexWrap: 'wrap', gap: '8px' }}>
            <span>CEFR Framework Calibrated:</span>
            <div style={{ display: 'flex', gap: '6px' }}>
              <span className="badge badge-a1" style={{ fontSize: '0.68rem' }}>A1</span>
              <span className="badge badge-a2" style={{ fontSize: '0.68rem' }}>A2</span>
              <span className="badge badge-b1" style={{ fontSize: '0.68rem' }}>B1</span>
              <span className="badge badge-b2" style={{ fontSize: '0.68rem' }}>B2</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Right Interactive Setup & Diagnostic Canvas (Responsive) */}
      <section className="onboarding-main">
        <div style={{ maxWidth: '680px', width: '100%', margin: '0 auto' }}>
          {/* Step Progression Bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '36px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  backgroundColor: step === 'profile' ? 'var(--primary)' : 'var(--accent-emerald)',
                  color: '#ffffff',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {step !== 'profile' ? '✓' : '1'}
              </span>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: step === 'profile' ? 'var(--text-main)' : 'var(--text-muted)' }}>Step 1</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Learner Profile</div>
              </div>
            </div>

            <div style={{ flex: 1, height: '2px', backgroundColor: step !== 'profile' ? 'var(--accent-emerald)' : 'var(--border-subtle)', margin: '0 16px' }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  backgroundColor: step === 'chat' ? 'var(--primary)' : step === 'complete' ? 'var(--accent-emerald)' : 'var(--bg-surface-subtle)',
                  color: step === 'chat' || step === 'complete' ? '#ffffff' : 'var(--text-dim)',
                  border: step === 'profile' ? '1px solid var(--border-default)' : 'none',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {step === 'complete' ? '✓' : '2'}
              </span>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: step === 'chat' ? 'var(--text-main)' : 'var(--text-muted)' }}>Step 2</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Calibration Diagnostic</div>
              </div>
            </div>

            <div style={{ flex: 1, height: '2px', backgroundColor: step === 'complete' ? 'var(--accent-emerald)' : 'var(--border-subtle)', margin: '0 16px' }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  backgroundColor: step === 'complete' ? 'var(--accent-emerald)' : 'var(--bg-surface-subtle)',
                  color: step === 'complete' ? '#ffffff' : 'var(--text-dim)',
                  border: step !== 'complete' ? '1px solid var(--border-default)' : 'none',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                3
              </span>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: step === 'complete' ? 'var(--text-main)' : 'var(--text-muted)' }}>Step 3</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Curriculum Matrix</div>
              </div>
            </div>
          </div>

          {/* STEP 1: Profile & Focus Goals */}
          {step === 'profile' && (
            <div>
              <div style={{ marginBottom: '24px' }}>
                <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '8px' }}>
                  Create Your Learner Profile
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem' }}>
                  Tell us who you are and what you want to achieve. Loop adapts your scenario generation to match your goals.
                </p>
              </div>

              {error && (
                <div style={{ backgroundColor: 'var(--accent-rose-light)', border: '1px solid var(--accent-rose)', padding: '12px 16px', borderRadius: '10px', color: '#991b1b', marginBottom: '20px', fontSize: '0.9rem' }}>
                  {error}
                </div>
              )}

              <form onSubmit={handleStartPlacement} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 600, marginBottom: '8px', color: 'var(--text-main)' }}>
                    Your Name or Display Handle
                  </label>
                  <input
                    type="text"
                    className="input-control"
                    placeholder="e.g. Maya Chen"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 600, marginBottom: '10px', color: 'var(--text-main)' }}>
                    Choose Your Conversation Focus Area
                  </label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {goalOptions.map((item) => {
                      const Icon = item.icon;
                      const isSelected = goal === item.id;
                      return (
                        <div
                          key={item.id}
                          onClick={() => setGoal(item.id)}
                          style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: '14px',
                            padding: '16px',
                            borderRadius: '12px',
                            border: isSelected ? '2px solid var(--primary)' : '1px solid var(--border-subtle)',
                            backgroundColor: isSelected ? 'var(--primary-light)' : '#ffffff',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          <div
                            style={{
                              width: '40px',
                              height: '40px',
                              borderRadius: '10px',
                              backgroundColor: isSelected ? 'var(--primary)' : 'var(--bg-surface-subtle)',
                              color: isSelected ? '#ffffff' : 'var(--text-muted)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexShrink: 0,
                              marginTop: '2px',
                            }}
                          >
                            <Icon size={20} />
                          </div>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ fontSize: '0.96rem', fontWeight: 700, color: isSelected ? 'var(--primary)' : 'var(--text-main)' }}>
                                {item.title}
                              </span>
                              <span style={{ fontSize: '0.7rem', fontWeight: 600, backgroundColor: isSelected ? '#ffffff' : 'var(--bg-surface-subtle)', color: isSelected ? 'var(--primary)' : 'var(--text-dim)', padding: '2px 8px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                                {item.tag}
                              </span>
                            </div>
                            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.45, margin: 0 }}>
                              {item.desc}
                            </p>
                          </div>
                          <div
                            style={{
                              width: '20px',
                              height: '20px',
                              borderRadius: '50%',
                              border: isSelected ? '6px solid var(--primary)' : '2px solid var(--border-default)',
                              backgroundColor: '#ffffff',
                              marginTop: '4px',
                              flexShrink: 0,
                            }}
                          />
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Daily Habit Commitment */}
                <div>
                  <label style={{ display: 'block', fontSize: '0.88rem', fontWeight: 600, marginBottom: '8px', color: 'var(--text-main)' }}>
                    Daily Practice Commitment
                  </label>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 140px), 1fr))', gap: '10px' }}>
                    {[
                      { min: '5', label: 'Casual (5 min/day)' },
                      { min: '15', label: 'Regular (15 min/day)' },
                      { min: '30', label: 'Intensive (30 min/day)' },
                    ].map((c) => (
                      <button
                        key={c.min}
                        type="button"
                        onClick={() => setDailyMinutes(c.min)}
                        style={{
                          padding: '10px',
                          borderRadius: '8px',
                          border: dailyMinutes === c.min ? '2px solid var(--primary)' : '1px solid var(--border-subtle)',
                          backgroundColor: dailyMinutes === c.min ? 'var(--primary-light)' : 'transparent',
                          color: dailyMinutes === c.min ? 'var(--primary)' : 'var(--text-muted)',
                          fontSize: '0.82rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        {c.label}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  className="btn-primary"
                  disabled={loading}
                  style={{ marginTop: '8px', padding: '14px', fontSize: '1rem', borderRadius: '10px' }}
                >
                  {loading ? 'Starting Diagnostic Agent...' : 'Begin 3-Turn Diagnostic Assessment'} <ArrowRight size={18} />
                </button>
              </form>
            </div>
          )}

          {/* STEP 2: Placement Chat Diagnostic */}
          {step === 'chat' && (
            <div className="app-card" style={{ padding: 'clamp(16px, 3.5vw, 28px)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #bfdbfe' }}>
                    <Sparkles size={20} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)' }}>Placement Evaluator Agent</h3>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Conversational Spanish diagnostic (3 turns)</span>
                  </div>
                </div>
                <span className="badge badge-a2">Live Evaluation</span>
              </div>

              {/* Rubric hints */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', backgroundColor: 'var(--bg-surface-subtle)', padding: '10px 14px', borderRadius: '8px', fontSize: '0.78rem', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
                <span>🎯 <strong>Criteria:</strong> Vocabulary richness</span>
                <span>• Verb conjugation accuracy</span>
                <span>• Conversational ease</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', minHeight: '260px', maxHeight: '420px', overflowY: 'auto', paddingRight: '6px', marginBottom: '20px' }}>
                {messages.map((m, idx) => (
                  <div key={idx} className={m.role === 'agent' ? 'chat-agent' : 'chat-learner'}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: m.role === 'agent' ? 'var(--text-muted)' : 'rgba(255,255,255,0.9)', marginBottom: '4px', textTransform: 'uppercase' }}>
                      {m.role === 'agent' ? 'Diagnostic Tutor' : name || 'You'}
                    </div>
                    <div style={{ fontSize: '0.96rem', lineHeight: 1.55 }}>{m.text}</div>
                  </div>
                ))}
                {loading && (
                  <div className="chat-agent" style={{ width: 'fit-content' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--primary)', animation: 'softPulse 1s infinite' }} />
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Evaluating response and vocabulary level...</span>
                    </div>
                  </div>
                )}
              </div>

              <form onSubmit={handleSendTurn} style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <input
                  type="text"
                  className="input-control"
                  placeholder="Type response in Spanish (or English if beginner)..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  disabled={loading}
                  style={{ flex: 1, minWidth: '180px' }}
                  autoFocus
                />
                <button type="submit" className="btn-primary" disabled={loading || !inputText.trim()} style={{ whiteSpace: 'nowrap', padding: '12px 20px' }}>
                  Send <ArrowRight size={16} />
                </button>
              </form>
            </div>
          )}

          {/* STEP 3: Calibration Result & Roadmap */}
          {step === 'complete' && (
            <div className="app-card" style={{ padding: 'clamp(24px, 4vw, 44px) clamp(16px, 3.5vw, 36px)', textAlign: 'center' }}>
              <div
                style={{
                  width: '68px',
                  height: '68px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--accent-emerald-light)',
                  color: 'var(--accent-emerald)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 18px',
                }}
              >
                <CheckCircle2 size={36} />
              </div>

              <span className={`badge badge-${assessedLevel.toLowerCase()}`} style={{ fontSize: '0.92rem', padding: '6px 16px' }}>
                Calibrated Level: CEFR {assessedLevel}
              </span>

              <h2 style={{ fontSize: 'clamp(1.4rem, 3vw, 1.9rem)', fontWeight: 800, marginTop: '14px', marginBottom: '8px' }}>
                Cognitive Calibration Complete!
              </h2>
              <p style={{ color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto 24px', lineHeight: 1.6, fontSize: '0.95rem' }}>
                {assessmentNotes || 'Your starting profile has been established. Loop will tailor all upcoming roleplays and memory drills to this level.'}
              </p>

              {/* Ready Roadmap Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))', gap: '14px', maxWidth: '520px', margin: '0 auto 32px', textAlign: 'left' }}>
                <div className="app-panel" style={{ padding: '16px' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Focus Curriculum</div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--primary)', marginTop: '4px', textTransform: 'capitalize' }}>
                    {goal} Roleplays
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: '2px' }}>Targeted real-world situations</div>
                </div>

                <div className="app-panel" style={{ padding: '16px' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Vocabulary Schedule</div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--accent-emerald)', marginTop: '4px' }}>
                    FSRS-4.5 Active
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: '2px' }}>Cognitive memory decay active</div>
                </div>
              </div>

              <button
                onClick={() => onComplete({ id: userId, name, level: assessedLevel, goal })}
                className="btn-primary"
                style={{ padding: '14px 36px', fontSize: '1.02rem', borderRadius: '10px' }}
              >
                Launch Daily Loop Studio <ArrowRight size={18} />
              </button>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};
