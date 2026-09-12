import React from 'react';
import { SessionSummary as ISessionSummary } from '../api/client';
import { TrendingUp, Clock, CheckCircle2, AlertTriangle, ArrowRight, BookOpen, Sparkles, Compass } from 'lucide-react';

interface SessionSummaryProps {
  summary: ISessionSummary;
  onContinue: () => void;
  onViewProgress: () => void;
}

export const SessionSummary: React.FC<SessionSummaryProps> = ({ summary, onContinue, onViewProgress }) => {
  const formattedEta = new Date(summary.next_review_eta).toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="page-container">
      {/* Top Banner & Header */}
      <div className="action-ribbon">
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'var(--accent-emerald-light)', color: '#047857', padding: '4px 12px', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 700, marginBottom: '8px' }}>
            <CheckCircle2 size={15} /> Session Completed & Matrix Synchronized
          </div>
          <h1 style={{ fontSize: 'clamp(1.5rem, 3.5vw, 2.1rem)', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.025em' }}>
            Session Performance Digest
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.94rem', marginTop: '4px' }}>
            Multi-agent evaluation summary: spaced repetition intervals updated and linguistic slips recorded in your ledger.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button onClick={onViewProgress} className="btn-secondary" style={{ padding: '10px 20px', fontSize: '0.9rem' }}>
            View Progress Matrix
          </button>
          <button onClick={onContinue} className="btn-primary" style={{ padding: '10px 24px', fontSize: '0.9rem' }}>
            Start Next Loop <ArrowRight size={17} />
          </button>
        </div>
      </div>

      {/* 4-Stat Metric Ribbon */}
      <div className="stats-grid">
        {/* Metric 1 */}
        <div className="app-card" style={{ padding: 'clamp(16px, 3vw, 24px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Mastery Growth
            </span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--accent-emerald-light)', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <TrendingUp size={18} />
            </div>
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
            +{Math.round(summary.mastery_delta * 100)}%
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--accent-emerald)', fontWeight: 600, marginTop: '8px' }}>
            Active recall calibration delta
          </div>
        </div>

        {/* Metric 2 */}
        <div className="app-card" style={{ padding: 'clamp(16px, 3vw, 24px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Words Solidified
            </span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BookOpen size={18} />
            </div>
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {summary.words_closer_to_fluent}
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '8px' }}>
            Lexemes advanced toward long-term recall
          </div>
        </div>

        {/* Metric 3 */}
        <div className="app-card" style={{ padding: 'clamp(16px, 3vw, 24px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Next Spaced Review
            </span>
            <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--accent-violet-light)', color: 'var(--accent-violet)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Clock size={18} />
            </div>
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '6px' }}>
            {formattedEta}
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '12px' }}>
            Optimal FSRS memory decay trigger
          </div>
        </div>

        {/* Metric 4 */}
        <div className="app-card" style={{ padding: 'clamp(16px, 3vw, 24px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Linguistic Accuracy
            </span>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              backgroundColor: (summary.accuracy_percentage ?? 100) >= 80 ? 'var(--accent-emerald-light)' : (summary.accuracy_percentage ?? 100) >= 50 ? 'var(--accent-amber-light)' : '#fee2e2',
              color: (summary.accuracy_percentage ?? 100) >= 80 ? 'var(--accent-emerald)' : (summary.accuracy_percentage ?? 100) >= 50 ? 'var(--accent-amber)' : '#dc2626',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {(summary.accuracy_percentage ?? 100) >= 80 ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
            </div>
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {summary.accuracy_percentage !== undefined
              ? `${summary.accuracy_percentage}%`
              : summary.mistakes_this_session.length === 0
              ? '100%'
              : `${Math.max(0, 100 - summary.mistakes_this_session.length * 25)}%`}
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '8px' }}>
            {summary.mistakes_this_session.length === 0
              ? (summary.accuracy_percentage ?? 100) >= 80
                ? 'Flawless grammatical precision'
                : 'Session completed with basic participation'
              : `${summary.mistakes_this_session.length} slips tracked for re-testing`}
          </div>
        </div>
      </div>

      {/* 2-Column Wide Analytics Grid (Fluid 1-col on mobile/tablet) */}
      <div className="analytics-grid">
        {/* Left Column: Error Analysis Insights */}
        <div className="app-card" style={{ padding: 'clamp(18px, 3vw, 28px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '1.2rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={18} color="var(--accent-amber)" />
                Error Analysis & Coaching Feedback ({summary.mistakes_this_session.length})
              </h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '3px' }}>
                Real-time feedback identified by the diagnostic error agent
              </p>
            </div>
          </div>

          {summary.mistakes_this_session.length === 0 ? (
            <div style={{
              backgroundColor: (summary.accuracy_percentage ?? 100) >= 80 ? 'var(--accent-emerald-light)' : 'var(--accent-amber-light)',
              border: `1px solid ${(summary.accuracy_percentage ?? 100) >= 80 ? '#a7f3d0' : '#fde68a'}`,
              borderRadius: '12px',
              padding: '24px',
              display: 'flex',
              alignItems: 'center',
              gap: '16px'
            }}>
              {(summary.accuracy_percentage ?? 100) >= 80 ? (
                <CheckCircle2 size={32} color="var(--accent-emerald)" style={{ flexShrink: 0 }} />
              ) : (
                <AlertTriangle size={32} color="var(--accent-amber)" style={{ flexShrink: 0 }} />
              )}
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.05rem', color: (summary.accuracy_percentage ?? 100) >= 80 ? '#065f46' : '#92400e' }}>
                  {(summary.accuracy_percentage ?? 100) >= 80 ? 'Flawless Conversational Precision!' : 'Session Complete — Review Target Vocab'}
                </div>
                <div style={{ fontSize: '0.88rem', color: (summary.accuracy_percentage ?? 100) >= 80 ? '#047857' : '#78350f', marginTop: '4px', lineHeight: 1.5 }}>
                  {(summary.accuracy_percentage ?? 100) >= 80
                    ? 'The Error Classifier agent did not detect any grammatical mismatches, incorrect verb conjugations, or unnatural phrasing in this session.'
                    : 'Practice using target Spanish vocabulary in your upcoming sessions to raise your accuracy and retention.'}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {summary.mistakes_this_session.map((m, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-subtle)',
                    borderLeft: '4px solid var(--accent-amber)',
                    borderRadius: '10px',
                    padding: '16px 20px',
                    boxShadow: 'var(--shadow-xs)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span className="badge badge-warning" style={{ fontSize: '0.72rem', textTransform: 'uppercase' }}>
                      {m.error_type.replace('_', ' ')}
                    </span>
                    <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                      Severity: <strong>{m.severity}</strong>
                    </span>
                  </div>

                  {m.example_turn && (
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                      <strong style={{ color: 'var(--text-main)' }}>Your phrasing:</strong> "{m.example_turn}"
                    </div>
                  )}

                  {m.correction && (
                    <div style={{ fontSize: '0.92rem', color: '#047857', fontWeight: 600, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span>Target native form:</span>
                      <span style={{ backgroundColor: 'var(--accent-emerald-light)', padding: '2px 8px', borderRadius: '4px' }}>
                        {m.correction}
                      </span>
                    </div>
                  )}

                  {m.explanation && (
                    <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)', lineHeight: 1.5, borderTop: '1px dashed var(--border-subtle)', paddingTop: '6px', marginTop: '6px' }}>
                      {m.explanation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Memory Impact & Next Scenario */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Next Recommended Roleplay Card */}
          <div className="app-card" style={{ padding: '28px', backgroundColor: 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Compass size={18} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)' }}>Recommended Next Scenario</h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Dynamically selected by Curriculum Agent</span>
              </div>
            </div>

            <div className="app-panel" style={{ padding: '16px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: '0.98rem', color: 'var(--text-main)' }}>
                  {summary.next_recommended_scenario?.title || 'Ordering at a Traditional Tapas Bar'}
                </div>
                <span className={`badge badge-${(summary.next_recommended_scenario?.level || 'A1').toLowerCase()}`}>
                  Target CEFR {summary.next_recommended_scenario?.level || 'A1'}
                </span>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.45, margin: 0 }}>
                {summary.next_recommended_scenario?.description || 'Practice ordering appetizers, inquiring about ingredients, and requesting the bill in colloquial Spanish.'}
              </p>
            </div>

            <button onClick={onContinue} className="btn-primary" style={{ width: '100%', padding: '12px', fontSize: '0.94rem' }}>
              Launch Next Roleplay <ArrowRight size={17} />
            </button>
          </div>

          {/* FSRS Memory Impact Details */}
          <div className="app-card" style={{ padding: '28px' }}>
            <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)', marginBottom: '8px' }}>
              FSRS Spaced Repetition Updates
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '16px' }}>
              Every response in the conversation was evaluated for retrieval strength and cognitive ease. Vocabulary used fluently had its review interval extended, solidifying permanent long-term recall.
            </p>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <div className="suggestion-chip">
                ✓ Stability factor delta: {summary.stability_factor_delta || "+0.10x"}
              </div>
              <div className="suggestion-chip">
                ✓ Recall probability: {summary.recall_probability || 92}%
              </div>
              <div className="suggestion-chip">
                ✓ {summary.words_closer_to_fluent} {summary.words_closer_to_fluent === 1 ? 'lexeme' : 'lexemes'} advanced in FSRS
              </div>
              <div className="suggestion-chip">
                ✓ {summary.mistakes_this_session.length} {summary.mistakes_this_session.length === 1 ? 'slip' : 'slips'} tracked in memory ledger
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

