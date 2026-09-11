import React, { useState, useEffect } from 'react';
import { Onboarding } from './pages/Onboarding';
import { DailyLoop } from './pages/DailyLoop';
import { SessionSummary } from './pages/SessionSummary';
import { Progress } from './pages/Progress';
import { LearnersDirectory } from './pages/LearnersDirectory';
import { SessionSummary as ISessionSummary } from './api/client';
import { RefreshCw, MessageSquare, BarChart2, User, RotateCcw, Users } from 'lucide-react';

interface UserProfile {
  id: string;
  name: string;
  level: string;
  goal: string;
}

export function App() {
  const [user, setUser] = useState<UserProfile | null>(() => {
    const saved = localStorage.getItem('loop_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [activeTab, setActiveTab] = useState<'loop' | 'review' | 'summary' | 'progress' | 'learners'>('loop');
  const [lastSummary, setLastSummary] = useState<ISessionSummary | null>(null);

  useEffect(() => {
    if (user) {
      localStorage.setItem('loop_user', JSON.stringify(user));
    }
  }, [user]);

  const handleOnboardingComplete = (newUser: UserProfile) => {
    setUser(newUser);
    setActiveTab('loop');
  };

  const handleFinishSession = (summary: ISessionSummary) => {
    setLastSummary(summary);
    setActiveTab('summary');
  };

  const handleResetUser = () => {
    localStorage.removeItem('loop_user');
    setUser(null);
    setLastSummary(null);
    setActiveTab('loop');
  };

  const isFullBleedStudio = user && (activeTab === 'loop' || activeTab === 'review');

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-page)' }}>
      {/* Professional Full-Width Top Navigation Bar */}
      <header
        style={{
          borderBottom: '1px solid var(--border-subtle)',
          backgroundColor: 'var(--bg-surface)',
          position: 'sticky',
          top: 0,
          zIndex: 50,
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          padding: '0 clamp(12px, 3vw, 28px)',
          boxShadow: 'var(--shadow-xs)',
        }}
      >
        <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
          {/* Brand Logo */}
          <div
            style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', userSelect: 'none', flexShrink: 0 }}
            onClick={() => user && setActiveTab('loop')}
          >
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                backgroundColor: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)',
              }}
            >
              <RefreshCw size={18} strokeWidth={2.4} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.03em' }}>
                Loop
              </span>
              <span
                className="header-tagline"
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  color: 'var(--primary)',
                  backgroundColor: 'var(--primary-light)',
                  padding: '2px 8px',
                  borderRadius: '6px',
                  border: '1px solid #bfdbfe',
                }}
              >
                Adaptive AI Tutor
              </span>
            </div>
          </div>

          {/* If No User (Onboarding view): Provide direct entry to Learners Directory */}
          {!user && (
            <button
              onClick={() => setActiveTab(activeTab === 'learners' ? 'loop' : 'learners')}
              className="btn-secondary"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '7px 14px',
                fontSize: '0.84rem',
                fontWeight: 600,
              }}
            >
              <Users size={15} />
              <span>{activeTab === 'learners' ? 'Back to Onboarding' : 'Learners & Records'}</span>
            </button>
          )}

          {/* Navigation & Learner Profile (When user logged in) */}
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'clamp(8px, 2vw, 18px)' }}>
              {/* Segmented Tab Navigation */}
              <nav
                style={{
                  display: 'flex',
                  gap: '3px',
                  backgroundColor: 'var(--bg-surface-subtle)',
                  padding: '3px',
                  borderRadius: '10px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <button
                  onClick={() => setActiveTab('loop')}
                  className={activeTab === 'loop' || activeTab === 'review' ? 'btn-tab-active' : 'btn-tab-inactive'}
                  style={{ padding: '6px clamp(8px, 1.5vw, 14px)', fontSize: '0.84rem' }}
                  title="Daily Loop Studio"
                >
                  <MessageSquare size={15} />
                  <span className="header-nav-btn-text">Daily Loop</span>
                </button>
                <button
                  onClick={() => setActiveTab('progress')}
                  className={activeTab === 'progress' || activeTab === 'summary' ? 'btn-tab-active' : 'btn-tab-inactive'}
                  style={{ padding: '6px clamp(8px, 1.5vw, 14px)', fontSize: '0.84rem' }}
                  title="Progress & Matrix"
                >
                  <BarChart2 size={15} />
                  <span className="header-nav-btn-text">Progress</span>
                </button>
                <button
                  onClick={() => setActiveTab('learners')}
                  className={activeTab === 'learners' ? 'btn-tab-active' : 'btn-tab-inactive'}
                  style={{ padding: '6px clamp(8px, 1.5vw, 14px)', fontSize: '0.84rem' }}
                  title="View Platform Learners & Audit Records"
                >
                  <Users size={15} />
                  <span className="header-nav-btn-text">Learners & Records</span>
                </button>
              </nav>

              {/* Learner Info Badge & Switch Action */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 'clamp(6px, 1.5vw, 12px)', borderLeft: '1px solid var(--border-subtle)', paddingLeft: 'clamp(8px, 2vw, 14px)' }}>
                <div className="header-learner-details" style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--text-main)', maxWidth: '120px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {user.name}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '5px', marginTop: '1px' }}>
                    <span className={`badge badge-${user.level.toLowerCase()}`} style={{ fontSize: '0.62rem', padding: '1px 5px' }}>
                      {user.level}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                      · {user.goal}
                    </span>
                  </div>
                </div>

                <button
                  onClick={handleResetUser}
                  title="Switch or reset learner profile"
                  className="btn-secondary"
                  style={{
                    padding: '7px',
                    borderRadius: '8px',
                    color: 'var(--text-muted)',
                    flexShrink: 0,
                  }}
                >
                  <RotateCcw size={14} />
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content Area - Fluid full-page & studio adaptation */}
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          width: '100%',
          maxWidth: '100%',
          margin: 0,
          padding: 0,
          minHeight: 'calc(100dvh - 64px)',
          overflow: isFullBleedStudio ? 'hidden' : 'visible',
        }}
      >
        {activeTab === 'learners' ? (
          <LearnersDirectory
            onSelectLearner={(selected) => {
              setUser(selected);
              setActiveTab('loop');
            }}
            onBack={() => setActiveTab('loop')}
          />
        ) : !user ? (
          <Onboarding onComplete={handleOnboardingComplete} />
        ) : activeTab === 'loop' ? (
          <DailyLoop user={user} mode="daily_loop" onFinishSession={handleFinishSession} />
        ) : activeTab === 'review' ? (
          <DailyLoop user={user} mode="review_only" onFinishSession={handleFinishSession} />
        ) : activeTab === 'summary' && lastSummary ? (
          <SessionSummary
            summary={lastSummary}
            onContinue={() => setActiveTab('loop')}
            onViewProgress={() => setActiveTab('progress')}
          />
        ) : (
          <Progress
            user={user}
            onBackToLoop={() => setActiveTab('loop')}
            onStartReview={() => setActiveTab('review')}
          />
        )}
      </main>

      {/* Footer (rendered on non-studio views) */}
      {!isFullBleedStudio && (
        <footer
          style={{
            borderTop: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-surface)',
            padding: '20px clamp(16px, 4vw, 48px)',
            fontSize: '0.82rem',
            color: 'var(--text-muted)',
            width: '100%',
            marginTop: 'auto',
          }}
        >
          <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <strong>Loop</strong> · Conversational Language Learning Orchestration
            </div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.78rem' }}>
              LangGraph Multi-Agent Workflows · ChromaDB RAG · FSRS-4.5 Memory Engine
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}

export default App;
