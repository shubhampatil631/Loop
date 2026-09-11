import React, { useState, useEffect } from 'react';
import { api, ProgressData, VocabItem } from '../api/client';
import { Flame, CheckCircle2, BookOpen, Clock, AlertTriangle, ArrowLeft, RefreshCw, Sparkles, BarChart2, TrendingUp } from 'lucide-react';

interface ProgressProps {
  user: { id: string; name: string; level: string; goal: string };
  onBackToLoop: () => void;
  onStartReview?: () => void;
}

export const Progress: React.FC<ProgressProps> = ({ user, onBackToLoop, onStartReview }) => {
  const [data, setData] = useState<ProgressData | null>(null);
  const [dueItems, setDueItems] = useState<VocabItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Weekly Digest State
  const [digest, setDigest] = useState<{ summary: string; strength: string; focus_area: string } | null>(null);
  const [digestLoading, setDigestLoading] = useState(false);

  const fetchAll = async (forceRefresh: boolean = false) => {
    if (!data) {
      setLoading(true);
    } else {
      setIsRefreshing(true);
    }
    setError(null);
    try {
      const [progRes, dueRes] = await Promise.all([
        api.getProgress(user.id, forceRefresh),
        api.getReviewDue(user.id, forceRefresh),
      ]);
      setData(progRes);
      setDueItems(dueRes.due_items || []);
    } catch (err: any) {
      if (!data) {
        setError(err.message || 'Error fetching progress data');
      }
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAll(false);
  }, [user.id]);

  const handleFetchDigest = async () => {
    setDigestLoading(true);
    try {
      const res = await api.getWeeklyDigest(user.id);
      setDigest(res);
    } catch (e: any) {
      alert(`Error generating digest: ${e.message}`);
    } finally {
      setDigestLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div style={{ padding: '100px 16px', textAlign: 'center' }}>
        <div style={{ width: '40px', height: '40px', borderRadius: '50%', border: '3px solid var(--border-subtle)', borderTopColor: 'var(--primary)', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>Loading cognitive memory matrix...</p>
      </div>
    );
  }

  const masteryPercent = Math.round((data?.mastery_score || 0) * 100);

  return (
    <div className="page-container">
      {/* Top Action & Status Bar */}
      <div className="action-ribbon">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button onClick={onBackToLoop} className="btn-secondary" style={{ padding: '8px 16px', fontSize: '0.88rem' }}>
            <ArrowLeft size={16} /> Return to Daily Loop Studio
          </button>
          <button
            onClick={() => fetchAll(true)}
            disabled={isRefreshing}
            className="btn-secondary"
            style={{ padding: '8px 12px', fontSize: '0.84rem' }}
            title="Refresh memory matrix"
          >
            <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
            <span>{isRefreshing ? 'Syncing...' : 'Refresh'}</span>
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <span className={`badge badge-${user.level.toLowerCase()}`} style={{ fontSize: '0.82rem', padding: '6px 12px' }}>
            CEFR Level {user.level}
          </span>
          <div className="badge badge-warning" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', padding: '6px 12px' }}>
            <Flame size={15} color="#b45309" /> {data?.streak_days || 1} Day Streak Active
          </div>
          <div className="badge badge-a2" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', padding: '6px 12px' }}>
            <BarChart2 size={15} /> {data?.total_sessions ?? 0} Sessions ({data?.accuracy_rate ?? 100}% Accuracy)
          </div>
          {onStartReview && dueItems.length > 0 && (
            <button onClick={onStartReview} className="btn-primary" style={{ padding: '8px 18px', fontSize: '0.88rem' }}>
              <Sparkles size={16} /> Quick Review Session ({dueItems.length} Due)
            </button>
          )}
        </div>
      </div>

      {/* 4-Card Top Metrics Grid */}
      <div className="stats-grid">
        {/* Metric 1 */}
        <div className="app-card" style={{ padding: 'clamp(16px, 3vw, 24px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Proficiency Score
            </span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <TrendingUp size={18} />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1.1 }}>
              {masteryPercent}%
            </span>
            <span style={{ fontSize: '0.82rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>Active Calibrated</span>
          </div>
          <div style={{ height: '8px', backgroundColor: 'var(--bg-surface-subtle)', borderRadius: '4px', marginTop: '16px', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
            <div
              style={{
                height: '100%',
                width: `${masteryPercent}%`,
                backgroundColor: 'var(--primary)',
                borderRadius: '4px',
                transition: 'width 0.4s ease',
              }}
            />
          </div>
        </div>

        {/* Metric 2 */}
        <div className="app-card" style={{ padding: 'clamp(16px, 3vw, 24px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Graduated Lexemes
            </span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--accent-emerald-light)', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1.1 }}>
              {data?.words_graduated || 0}
            </span>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>words</span>
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-dim)', marginTop: '16px' }}>
            Solidified into permanent long-term recall
          </div>
        </div>

        {/* Metric 3 */}
        <div className="app-card" style={{ padding: 'clamp(16px, 3vw, 24px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              In-Progress Lexemes
            </span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--accent-amber-light)', color: 'var(--accent-amber)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Sparkles size={18} />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1.1 }}>
              {data?.words_in_progress || 0}
            </span>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>words</span>
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-dim)', marginTop: '16px' }}>
            Currently in FSRS spaced repetition cycles
          </div>
        </div>

        {/* Metric 4 */}
        <div className="app-card" style={{ padding: 'clamp(16px, 3vw, 24px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Spaced Due Items
            </span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--accent-violet-light)', color: 'var(--accent-violet)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Clock size={18} />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1.1 }}>
              {dueItems.length}
            </span>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>due now</span>
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-dim)', marginTop: '16px' }}>
            Ready for natural conversational weaving
          </div>
        </div>
      </div>

      {/* 2-Column Wide Dashboard Grid (Fluid 1-col on mobile/tablet) */}
      <div className="analytics-grid">
        {/* Left Column: Vocabulary & Due Queue */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Due for Conversation Weaving */}
          <div className="app-card" style={{ padding: 'clamp(18px, 3vw, 28px)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1.2rem', color: 'var(--text-main)' }}>
                  Due for Conversation Weaving ({dueItems.length})
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Target vocabulary scheduled for active recall in your next daily roleplay
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '12px' }}>
              {dueItems.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', padding: '12px 0' }}>
                  No words currently overdue. All items spaced appropriately!
                </div>
              ) : (
                dueItems.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      backgroundColor: 'var(--bg-surface)',
                      border: '1px solid var(--border-default)',
                      borderRadius: '10px',
                      padding: '8px 14px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      boxShadow: 'var(--shadow-xs)',
                    }}
                  >
                    <span style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-main)' }}>{item.lemma}</span>
                    <span className={`badge badge-${item.cefr_level.toLowerCase()}`} style={{ fontSize: '0.68rem', padding: '2px 8px' }}>
                      {item.cefr_level}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Curriculum Engine Overview */}
          <div className="app-card" style={{ padding: 'clamp(18px, 3vw, 28px)' }}>
            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)', marginBottom: '8px' }}>
              FSRS Cognitive Memory Engine
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '16px' }}>
              Loop implements the Free Spaced Repetition Scheduler (FSRS-4.5) to mathematically model your memory retention curve. Words you know well are spaced further apart, while challenging phrases are naturally re-triggered in conversation.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 160px), 1fr))', gap: '12px' }}>
              <div className="app-panel" style={{ padding: '14px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Memory Stability</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-emerald)', marginTop: '4px' }}>
                  {data?.retention_rate ?? 92}% Retention
                </div>
              </div>
              <div className="app-panel" style={{ padding: '14px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Spaced Active Queue</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--primary)', marginTop: '4px' }}>
                  {data?.words_in_progress ?? 0} In-Progress Lexemes
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: AI Digest & Mistake Ledger */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Weekly AI Digest */}
          <div className="app-card" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '10px', backgroundColor: 'var(--accent-violet-light)', color: 'var(--accent-violet)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <BookOpen size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)' }}>Weekly AI Cognitive Digest</h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Automated synthesis of weekly strengths & focus areas</p>
                </div>
              </div>
              <button
                onClick={handleFetchDigest}
                disabled={digestLoading}
                className="btn-primary"
                style={{ padding: '8px 16px', fontSize: '0.85rem' }}
              >
                {digestLoading ? 'Synthesizing...' : 'Generate AI Digest'}
              </button>
            </div>

            {digest ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '16px' }}>
                <div style={{ backgroundColor: 'var(--bg-surface-subtle)', border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '16px 20px' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Executive Synthesis
                  </div>
                  <div style={{ fontSize: '0.94rem', color: 'var(--text-main)', lineHeight: 1.55 }}>
                    {digest.summary}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
                  <div style={{ backgroundColor: '#ffffff', border: '1px solid var(--border-subtle)', borderLeft: '4px solid var(--accent-emerald)', borderRadius: '8px', padding: '14px 16px' }}>
                    <div style={{ fontSize: '0.76rem', fontWeight: 700, color: '#047857', textTransform: 'uppercase', marginBottom: '4px' }}>
                      Demonstrated Strength
                    </div>
                    <div style={{ fontSize: '0.86rem', color: 'var(--text-muted)' }}>{digest.strength}</div>
                  </div>

                  <div style={{ backgroundColor: '#ffffff', border: '1px solid var(--border-subtle)', borderLeft: '4px solid var(--accent-amber)', borderRadius: '8px', padding: '14px 16px' }}>
                    <div style={{ fontSize: '0.76rem', fontWeight: 700, color: '#b45309', textTransform: 'uppercase', marginBottom: '4px' }}>
                      Priority Focus Area
                    </div>
                    <div style={{ fontSize: '0.86rem', color: 'var(--text-muted)' }}>{digest.focus_area}</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="app-panel" style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                Click "Generate AI Digest" to generate an LLM synthesis of your performance.
              </div>
            )}
          </div>

          {/* Mistake Memory Ledger */}
          <div className="app-card" style={{ padding: '28px' }}>
            <div style={{ marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={18} color="var(--accent-amber)" />
                Mistake Memory Ledger (Retrigger Queue)
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: '3px' }}>
                Recorded linguistic slips tracked for targeted conversational re-testing
              </p>
            </div>

            {(!data?.recent_mistakes || data.recent_mistakes.length === 0) ? (
              <div className="app-panel" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                No mistake tags recorded yet. Complete daily conversational loops to build your feedback ledger!
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {data.recent_mistakes.map((m: any, idx: number) => {
                  const isRetriggered = (m.retriggered_count || 0) > 0;
                  return (
                    <div
                      key={idx}
                      style={{
                        backgroundColor: '#ffffff',
                        border: '1px solid var(--border-subtle)',
                        borderLeft: isRetriggered ? '4px solid var(--accent-emerald)' : '4px solid var(--accent-amber)',
                        borderRadius: '8px',
                        padding: '14px 16px',
                        boxShadow: 'var(--shadow-xs)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                        <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>
                          {m.error_type.replace('_', ' ')}
                        </span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: isRetriggered ? '#047857' : '#b45309' }}>
                          {isRetriggered ? '✓ Re-tested in Session' : '⏳ In Retrigger Queue'}
                        </span>
                      </div>

                      <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>Context:</span> "{m.example_turn}"
                      </div>

                      {m.correction && (
                        <div style={{ fontSize: '0.88rem', color: '#047857', fontWeight: 600 }}>
                          Target form: {m.correction}
                        </div>
                      )}

                      {m.explanation && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                          {m.explanation}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
