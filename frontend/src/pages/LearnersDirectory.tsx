import React, { useState, useEffect } from 'react';
import {
  Users,
  Search,
  RefreshCw,
  Award,
  BookOpen,
  AlertCircle,
  MessageSquare,
  Calendar,
  ChevronRight,
  ChevronDown,
  X,
  Flame,
  CheckCircle2,
  Database,
  Cpu,
  ArrowUpRight,
  Filter,
  UserCheck
} from 'lucide-react';
import {
  api,
  LearnerSummary,
  LearnerFullHistory,
  PlatformOverview,
  SessionRecord,
  MistakeTag
} from '../api/client';

interface LearnersDirectoryProps {
  onSelectLearner?: (learner: { id: string; name: string; level: string; goal: string }) => void;
  onBack?: () => void;
}

export function LearnersDirectory({ onSelectLearner, onBack }: LearnersDirectoryProps) {
  const [learners, setLearners] = useState<LearnerSummary[]>([]);
  const [overview, setOverview] = useState<PlatformOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [goalFilter, setGoalFilter] = useState('all');
  const [levelFilter, setLevelFilter] = useState('all');

  // Dossier Modal State
  const [selectedLearnerId, setSelectedLearnerId] = useState<string | null>(null);
  const [history, setHistory] = useState<LearnerFullHistory | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [historyTab, setHistoryTab] = useState<'sessions' | 'mistakes' | 'vocab'>('sessions');
  const [expandedSessionId, setExpandedSessionId] = useState<string | null>(null);
  const dossierCache = React.useRef<Record<string, LearnerFullHistory>>({});

  const fetchData = async (forceRefresh: boolean = false) => {
    setIsRefreshing(true);
    try {
      setError(null);
      const [learnersRes, overviewRes] = await Promise.all([
        api.getLearners(100, forceRefresh),
        api.getPlatformOverview(forceRefresh).catch(() => null)
      ]);
      setLearners(learnersRes.learners || []);
      if (overviewRes) setOverview(overviewRes);
    } catch (err: any) {
      setError(err?.message || 'Failed to load learners directory');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenDossier = async (userId: string) => {
    setSelectedLearnerId(userId);
    setHistoryTab('sessions');
    setExpandedSessionId(null);

    // Instant SWR: display from cache immediately if previously fetched
    if (dossierCache.current[userId]) {
      const cached = dossierCache.current[userId];
      setHistory(cached);
      if (cached.sessions && cached.sessions.length > 0) {
        setExpandedSessionId(cached.sessions[0].id);
      }
      setIsLoadingHistory(false);
    } else {
      setIsLoadingHistory(true);
    }

    try {
      const data = await api.getLearnerHistory(userId);
      dossierCache.current[userId] = data;
      setHistory(data);
      if (data.sessions && data.sessions.length > 0 && !expandedSessionId) {
        setExpandedSessionId(data.sessions[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load learner history:', err);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleCloseDossier = () => {
    setSelectedLearnerId(null);
    setHistory(null);
  };

  const handleLaunchStudio = (l: LearnerSummary) => {
    if (onSelectLearner) {
      onSelectLearner({
        id: l.user_id || l.id,
        name: l.name,
        level: l.level,
        goal: l.goal
      });
    }
  };

  // Filter learners
  const filteredLearners = learners.filter((l) => {
    const matchesSearch =
      !searchQuery.trim() ||
      l.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (l.user_id || l.id).toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.goal.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesGoal = goalFilter === 'all' || l.goal.toLowerCase() === goalFilter.toLowerCase();
    const matchesLevel = levelFilter === 'all' || l.level.toUpperCase() === levelFilter.toUpperCase();

    return matchesSearch && matchesGoal && matchesLevel;
  });

  return (
    <div style={{ padding: 'clamp(16px, 3vw, 36px)', maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
      {/* Page Title & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                backgroundColor: 'var(--primary-light)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Users size={20} strokeWidth={2.4} />
            </div>
            <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.03em' }}>
              Learners Directory & Audit Records
            </h1>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '750px' }}>
            Inspect everyone who has explored Loop. Review complete turn-by-turn dialogue transcripts, classified grammatical mistakes, pedagogical adaptations, and spaced repetition queues.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => fetchData(true)}
            disabled={isRefreshing}
            className="btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '9px 16px', fontSize: '0.85rem' }}
            title="Refresh database records"
          >
            <RefreshCw size={15} className={isRefreshing ? 'spin' : ''} />
            <span>{isRefreshing ? 'Syncing...' : 'Refresh Records'}</span>
          </button>
          {onBack && (
            <button
              onClick={onBack}
              className="btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '9px 18px', fontSize: '0.85rem' }}
            >
              <span>Back to Studio</span>
            </button>
          )}
        </div>
      </div>

      {/* Platform Overview Metrics Bar */}
      {overview && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '14px',
            marginBottom: '28px'
          }}
        >
          {/* Card 1: Total Users */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              boxShadow: 'var(--shadow-xs)'
            }}
          >
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              <Users size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Total Learners
              </div>
              <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1.15 }}>
                {overview.total_learners_registered}
              </div>
            </div>
          </div>

          {/* Card 2: Total Sessions */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              boxShadow: 'var(--shadow-xs)'
            }}
          >
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                color: 'var(--accent-emerald)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              <MessageSquare size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Sessions Conducted
              </div>
              <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1.15 }}>
                {overview.total_sessions_conducted}
              </div>
            </div>
          </div>

          {/* Card 3: Total Mistakes */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              boxShadow: 'var(--shadow-xs)'
            }}
          >
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                color: 'var(--accent-rose)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              <AlertCircle size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Mistakes Classified
              </div>
              <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1.15 }}>
                {overview.total_mistakes_classified}
              </div>
            </div>
          </div>

          {/* Card 4: Database & LLM Engine */}
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-subtle)',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              boxShadow: 'var(--shadow-xs)'
            }}
          >
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                color: 'var(--accent-violet)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              <Database size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Persistent Database
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: overview.database_connected ? 'var(--accent-emerald)' : 'var(--accent-amber)'
                  }}
                />
                <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  MongoDB Atlas ({overview.active_database})
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter & Search Toolbar */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
          padding: '14px 18px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          boxShadow: 'var(--shadow-xs)'
        }}
      >
        {/* Search Input */}
        <div style={{ position: 'relative', flex: '1 1 260px', maxWidth: '420px' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
          <input
            type="text"
            placeholder="Search by learner name, ID, or goal..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '9px 12px 9px 36px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-surface-subtle)',
              fontSize: '0.88rem',
              color: 'var(--text-main)',
              outline: 'none'
            }}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                color: 'var(--text-dim)',
                cursor: 'pointer'
              }}
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Goal & Level Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Goal Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>Goal:</span>
            {['all', 'travel', 'work', 'culture', 'family'].map((g) => (
              <button
                key={g}
                onClick={() => setGoalFilter(g)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  textTransform: 'capitalize',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: goalFilter === g ? 'var(--primary)' : 'var(--bg-surface-subtle)',
                  color: goalFilter === g ? '#ffffff' : 'var(--text-muted)',
                  transition: 'all 0.15s ease'
                }}
              >
                {g}
              </button>
            ))}
          </div>

          {/* Level Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', borderLeft: '1px solid var(--border-subtle)', paddingLeft: '10px' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>Level:</span>
            {['all', 'A1', 'A2', 'B1'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setLevelFilter(lvl)}
                style={{
                  padding: '4px 8px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: levelFilter === lvl ? 'var(--text-main)' : 'var(--bg-surface-subtle)',
                  color: levelFilter === lvl ? '#ffffff' : 'var(--text-muted)',
                  transition: 'all 0.15s ease'
                }}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div
          style={{
            backgroundColor: 'var(--accent-rose-light)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            marginBottom: '20px',
            color: 'var(--accent-rose)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.88rem'
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Directory Content */}
      {isLoading ? (
        <div style={{ padding: '80px 20px', textAlign: 'center', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
          <RefreshCw size={28} className="spin" style={{ color: 'var(--primary)', margin: '0 auto 12px' }} />
          <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>Loading registered learners from database...</div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>Connecting to MongoDB Atlas</div>
        </div>
      ) : filteredLearners.length === 0 ? (
        <div style={{ padding: '60px 20px', textAlign: 'center', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
          <Users size={36} style={{ color: 'var(--text-dim)', margin: '0 auto 12px' }} />
          <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '1.05rem' }}>No learners match current filters</div>
          <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginTop: '4px' }}>Try adjusting your search terms or clearing goal/level filters.</div>
        </div>
      ) : (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            overflow: 'hidden',
            boxShadow: 'var(--shadow-xs)'
          }}
        >
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-surface-subtle)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '12px 18px', fontWeight: 700, color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Learner Profile
                  </th>
                  <th style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    CEFR Level
                  </th>
                  <th style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Learning Goal
                  </th>
                  <th style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Sessions
                  </th>
                  <th style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Mistakes Tagged
                  </th>
                  <th style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Streak
                  </th>
                  <th style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    First Registered
                  </th>
                  <th style={{ padding: '12px 18px', fontWeight: 700, color: 'var(--text-muted)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.04em', textAlign: 'right' }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredLearners.map((learner) => {
                  const uid = learner.user_id || learner.id;
                  const initials = (learner.name || 'User')
                    .split(' ')
                    .map((n) => n[0])
                    .join('')
                    .toUpperCase()
                    .slice(0, 2);

                  const dateFormatted = learner.created_at
                    ? new Date(learner.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
                    : 'Recent';

                  return (
                    <tr
                      key={uid}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        transition: 'background-color 0.15s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--bg-surface-subtle)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      {/* Name & ID */}
                      <td style={{ padding: '14px 18px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <div
                            style={{
                              width: '36px',
                              height: '36px',
                              borderRadius: '50%',
                              backgroundColor: 'var(--primary-light)',
                              color: 'var(--primary)',
                              fontWeight: 700,
                              fontSize: '0.82rem',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexShrink: 0
                            }}
                          >
                            {initials}
                          </div>
                          <div>
                            <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>{learner.name}</div>
                            <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', fontFamily: 'monospace', letterSpacing: '0.02em' }}>
                              ID: {uid}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Level */}
                      <td style={{ padding: '14px 16px' }}>
                        <span className={`badge badge-${learner.level.toLowerCase()}`} style={{ fontSize: '0.74rem', padding: '2px 8px' }}>
                          {learner.level}
                        </span>
                      </td>

                      {/* Goal */}
                      <td style={{ padding: '14px 16px' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            textTransform: 'capitalize',
                            backgroundColor: 'var(--bg-surface-subtle)',
                            border: '1px solid var(--border-subtle)',
                            padding: '2px 8px',
                            borderRadius: '6px',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            color: 'var(--text-muted)'
                          }}
                        >
                          {learner.goal}
                        </span>
                      </td>

                      {/* Sessions */}
                      <td style={{ padding: '14px 16px', fontWeight: 600, color: 'var(--text-main)' }}>
                        {learner.total_sessions}
                      </td>

                      {/* Mistakes Tagged */}
                      <td style={{ padding: '14px 16px' }}>
                        <span
                          style={{
                            fontWeight: 700,
                            color: learner.total_mistakes > 0 ? 'var(--accent-rose)' : 'var(--text-dim)'
                          }}
                        >
                          {learner.total_mistakes}
                        </span>
                      </td>

                      {/* Streak */}
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent-amber)', fontWeight: 700 }}>
                          <Flame size={14} />
                          <span>{learner.streak_days || 1}d</span>
                        </div>
                      </td>

                      {/* Date */}
                      <td style={{ padding: '14px 16px', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                        {dateFormatted}
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '8px' }}>
                          <button
                            onClick={() => handleOpenDossier(uid)}
                            className="btn-secondary"
                            style={{
                              padding: '5px 12px',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              display: 'flex',
                              alignItems: 'center',
                              gap: '5px'
                            }}
                          >
                            <span>Inspect Records</span>
                            <ChevronRight size={13} />
                          </button>

                          {onSelectLearner && (
                            <button
                              onClick={() => handleLaunchStudio(learner)}
                              className="btn-primary"
                              style={{
                                padding: '5px 10px',
                                fontSize: '0.78rem',
                                fontWeight: 600,
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px'
                              }}
                              title="Switch active user to this learner"
                            >
                              <UserCheck size={13} />
                              <span>Switch</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div
            style={{
              padding: '12px 18px',
              backgroundColor: 'var(--bg-surface-subtle)',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.8rem',
              color: 'var(--text-muted)'
            }}
          >
            <span>Showing {filteredLearners.length} of {learners.length} registered learners</span>
            <span>Data synced from MongoDB Atlas <code>loop</code> database</span>
          </div>
        </div>
      )}

      {/* DETAILED LEARNER DOSSIER MODAL */}
      {selectedLearnerId && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(4px)',
            zIndex: 100,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
          }}
          onClick={handleCloseDossier}
        >
          <div
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 'var(--radius-xl)',
              width: '100%',
              maxWidth: '900px',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: 'var(--shadow-lg)',
              border: '1px solid var(--border-subtle)',
              overflow: 'hidden'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '20px 24px',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                backgroundColor: 'var(--bg-surface-subtle)'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    {history?.user.name || 'Learner Dossier'}
                  </h2>
                  {history && (
                    <span className={`badge badge-${history.user.level.toLowerCase()}`} style={{ fontSize: '0.72rem' }}>
                      {history.user.level}
                    </span>
                  )}
                  {history && (
                    <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                      · Goal: {history.user.goal}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontFamily: 'monospace', marginTop: '3px' }}>
                  User ID: {selectedLearnerId}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {history && onSelectLearner && (
                  <button
                    onClick={() => {
                      onSelectLearner({
                        id: history.user.user_id,
                        name: history.user.name,
                        level: history.user.level,
                        goal: history.user.goal
                      });
                      handleCloseDossier();
                    }}
                    className="btn-primary"
                    style={{ padding: '6px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <UserCheck size={14} />
                    <span>Launch as Learner</span>
                  </button>
                )}
                <button
                  onClick={handleCloseDossier}
                  style={{
                    padding: '6px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: 'var(--bg-surface)',
                    cursor: 'pointer',
                    color: 'var(--text-muted)'
                  }}
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            {isLoadingHistory ? (
              <div style={{ padding: '60px 20px', textAlign: 'center' }}>
                <RefreshCw size={26} className="spin" style={{ color: 'var(--primary)', margin: '0 auto 10px' }} />
                <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>Loading learner history & transcripts...</div>
              </div>
            ) : !history ? (
              <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                Unable to load history for this user.
              </div>
            ) : (
              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
                {/* Stats Header strip */}
                <div
                  style={{
                    padding: '14px 24px',
                    backgroundColor: 'var(--bg-surface)',
                    borderBottom: '1px solid var(--border-subtle)',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: '10px'
                  }}
                >
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Sessions</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
                      {history.statistics.total_sessions}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Mistakes Tagged</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--accent-rose)' }}>
                      {history.statistics.total_mistakes_tagged}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Vocab Tracked</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
                      {history.statistics.vocab_items_tracked}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Streak</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--accent-amber)' }}>
                      {history.user.streak_days || 1} days
                    </div>
                  </div>
                </div>

                {/* Sub-Tabs: Sessions / Mistakes / Vocab */}
                <div
                  style={{
                    padding: '0 24px',
                    borderBottom: '1px solid var(--border-subtle)',
                    backgroundColor: 'var(--bg-surface-subtle)',
                    display: 'flex',
                    gap: '20px'
                  }}
                >
                  <button
                    onClick={() => setHistoryTab('sessions')}
                    style={{
                      padding: '12px 4px',
                      border: 'none',
                      background: 'none',
                      fontSize: '0.86rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      color: historyTab === 'sessions' ? 'var(--primary)' : 'var(--text-muted)',
                      borderBottom: historyTab === 'sessions' ? '2px solid var(--primary)' : '2px solid transparent',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <MessageSquare size={15} />
                    <span>Conversation Transcripts ({history.sessions?.length || 0})</span>
                  </button>

                  <button
                    onClick={() => setHistoryTab('mistakes')}
                    style={{
                      padding: '12px 4px',
                      border: 'none',
                      background: 'none',
                      fontSize: '0.86rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      color: historyTab === 'mistakes' ? 'var(--primary)' : 'var(--text-muted)',
                      borderBottom: historyTab === 'mistakes' ? '2px solid var(--primary)' : '2px solid transparent',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <AlertCircle size={15} />
                    <span>Classified Mistakes ({history.mistake_tags?.length || 0})</span>
                  </button>

                  <button
                    onClick={() => setHistoryTab('vocab')}
                    style={{
                      padding: '12px 4px',
                      border: 'none',
                      background: 'none',
                      fontSize: '0.86rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      color: historyTab === 'vocab' ? 'var(--primary)' : 'var(--text-muted)',
                      borderBottom: historyTab === 'vocab' ? '2px solid var(--primary)' : '2px solid transparent',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <BookOpen size={15} />
                    <span>Memory & Vocab Queue ({history.vocab_sample?.length || 0})</span>
                  </button>
                </div>

                {/* Tab 1: Conversation Transcripts */}
                {historyTab === 'sessions' && (
                  <div style={{ padding: '20px 24px' }}>
                    {(!history.sessions || history.sessions.length === 0) ? (
                      <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                        No session transcripts recorded yet for this learner.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {history.sessions.map((sess, sIdx) => {
                          const isExpanded = expandedSessionId === sess.id;
                          const turns = sess.conversation_turns || [];

                          return (
                            <div
                              key={sess.id || sIdx}
                              style={{
                                borderRadius: 'var(--radius-lg)',
                                border: '1px solid var(--border-subtle)',
                                overflow: 'hidden',
                                backgroundColor: 'var(--bg-surface)'
                              }}
                            >
                              {/* Accordion header */}
                              <div
                                onClick={() => setExpandedSessionId(isExpanded ? null : sess.id)}
                                style={{
                                  padding: '14px 18px',
                                  backgroundColor: 'var(--bg-surface-subtle)',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                  cursor: 'pointer',
                                  userSelect: 'none'
                                }}
                              >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                  <span
                                    style={{
                                      padding: '2px 8px',
                                      borderRadius: '6px',
                                      backgroundColor: sess.mode === 'placement' ? 'var(--accent-violet-light)' : 'var(--primary-light)',
                                      color: sess.mode === 'placement' ? 'var(--accent-violet)' : 'var(--primary)',
                                      fontSize: '0.74rem',
                                      fontWeight: 700,
                                      textTransform: 'uppercase'
                                    }}
                                  >
                                    {sess.mode}
                                  </span>
                                  <span style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-main)' }}>
                                    Session {sess.id}
                                  </span>
                                  <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                                    · {turns.length} turns recorded
                                  </span>
                                </div>

                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  {sess.is_ended && (
                                    <span style={{ fontSize: '0.74rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                                      Completed
                                    </span>
                                  )}
                                  {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                                </div>
                              </div>

                              {/* Dialogue Turns Body */}
                              {isExpanded && (
                                <div style={{ padding: '18px', backgroundColor: 'var(--bg-page)' }}>
                                  {turns.length === 0 ? (
                                    <div style={{ color: 'var(--text-muted)', fontSize: '0.84rem' }}>
                                      No dialogue turns logged for this session.
                                    </div>
                                  ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                      {turns.map((turn, tIdx) => {
                                        const isLearner = turn.role === 'learner';
                                        return (
                                          <div
                                            key={tIdx}
                                            style={{
                                              display: 'flex',
                                              justifyContent: isLearner ? 'flex-end' : 'flex-start',
                                              width: '100%'
                                            }}
                                          >
                                            <div
                                              style={{
                                                maxWidth: '82%',
                                                padding: '10px 14px',
                                                borderRadius: isLearner ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                                                backgroundColor: isLearner ? 'var(--primary)' : 'var(--bg-surface)',
                                                color: isLearner ? '#ffffff' : 'var(--text-main)',
                                                border: isLearner ? 'none' : '1px solid var(--border-subtle)',
                                                boxShadow: 'var(--shadow-xs)',
                                                fontSize: '0.88rem',
                                                lineHeight: 1.45
                                              }}
                                            >
                                              <div
                                                style={{
                                                  fontSize: '0.7rem',
                                                  fontWeight: 700,
                                                  marginBottom: '3px',
                                                  color: isLearner ? 'rgba(255,255,255,0.75)' : 'var(--text-muted)'
                                                }}
                                              >
                                                {isLearner ? 'Learner Turn' : 'Loop Agent'}
                                              </div>
                                              <div>{turn.text}</div>
                                            </div>
                                          </div>
                                        );
                                      })}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 2: Classified Mistakes */}
                {historyTab === 'mistakes' && (
                  <div style={{ padding: '20px 24px' }}>
                    {(!history.mistake_tags || history.mistake_tags.length === 0) ? (
                      <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                        No mistakes classified yet for this learner. Great fluency!
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                        {history.mistake_tags.map((m, mIdx) => (
                          <div
                            key={m.id || mIdx}
                            style={{
                              padding: '16px',
                              borderRadius: 'var(--radius-md)',
                              border: '1px solid var(--border-subtle)',
                              backgroundColor: 'var(--bg-surface)'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                              <span
                                style={{
                                  padding: '2px 8px',
                                  borderRadius: '6px',
                                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                  color: 'var(--accent-rose)',
                                  fontSize: '0.74rem',
                                  fontWeight: 700,
                                  textTransform: 'uppercase'
                                }}
                              >
                                {m.error_type?.replace('_', ' ')}
                              </span>
                              <span style={{ fontSize: '0.74rem', color: 'var(--text-dim)' }}>
                                Severity: {m.severity || 'medium'}
                              </span>
                            </div>

                            <div style={{ marginBottom: '6px' }}>
                              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Learner utterance: </span>
                              <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-main)' }}>
                                "{m.example_turn}"
                              </span>
                            </div>

                            {m.correction && (
                              <div style={{ marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <CheckCircle2 size={15} style={{ color: 'var(--accent-emerald)' }} />
                                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Target form: </span>
                                <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                                  {m.correction}
                                </span>
                              </div>
                            )}

                            {m.explanation && (
                              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', backgroundColor: 'var(--bg-surface-subtle)', padding: '8px 12px', borderRadius: '6px', marginTop: '6px' }}>
                                <strong>Grammar Rule: </strong>{m.explanation}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 3: Vocabulary Queue */}
                {historyTab === 'vocab' && (
                  <div style={{ padding: '20px 24px' }}>
                    {(!history.vocab_sample || history.vocab_sample.length === 0) ? (
                      <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                        No vocabulary items tracked yet in the FSRS memory engine.
                      </div>
                    ) : (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px' }}>
                        {history.vocab_sample.map((v, vIdx) => (
                          <div
                            key={v.id || vIdx}
                            style={{
                              padding: '14px',
                              borderRadius: 'var(--radius-md)',
                              border: '1px solid var(--border-subtle)',
                              backgroundColor: 'var(--bg-surface)'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                              <span style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--text-main)' }}>
                                {v.lemma}
                              </span>
                              <span className={`badge badge-${v.cefr_level.toLowerCase()}`} style={{ fontSize: '0.68rem' }}>
                                {v.cefr_level}
                              </span>
                            </div>
                            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                              Theme: {v.theme}
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: 'var(--text-dim)' }}>
                              <span>Reps: {v.ease_factor ? Math.round(v.ease_factor * 10) / 10 : 2.5} EF</span>
                              <span>Interval: {v.interval_days || 1}d</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
