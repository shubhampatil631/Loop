const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL)
  ? import.meta.env.VITE_API_BASE_URL
  : (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
    ? 'http://127.0.0.1:8000'
    : '';

export interface VocabItem {
  id: string;
  lemma: string;
  cefr_level: 'A1' | 'A2' | 'B1' | 'B2';
  theme: string;
  ease_factor: number;
  interval_days: number;
  due_at: string;
}

export interface MistakeTag {
  id: string;
  vocab_item_id?: string | null;
  error_type: 'gender_agreement' | 'conjugation' | 'word_order' | 'false_friend' | 'other';
  severity: 'low' | 'medium' | 'high';
  example_turn: string;
  correction?: string;
  explanation?: string;
  retriggered_count?: number;
}

export interface NextScenario {
  title: string;
  description: string;
  level: string;
}

export interface SessionSummary {
  session_id: string;
  mastery_delta: number;
  next_review_eta: string;
  mistakes_this_session: MistakeTag[];
  words_closer_to_fluent: number;
  accuracy_percentage?: number;
  stability_factor_delta?: string;
  recall_probability?: number;
  next_recommended_scenario?: NextScenario;
}

export interface ProgressData {
  mastery_score: number;
  words_graduated: number;
  words_in_progress: number;
  recent_mistakes: MistakeTag[];
  streak_days: number;
  total_sessions?: number;
  total_mistakes?: number;
  accuracy_rate?: number;
  retention_rate?: number;
}

export interface LearnerSummary {
  id: string;
  user_id: string;
  name: string;
  level: 'A1' | 'A2' | 'B1' | 'B2';
  goal: string;
  streak_days: number;
  created_at: string;
  last_session_at?: string | null;
  total_sessions: number;
  total_mistakes: number;
}

export interface ConversationTurnRecord {
  role: 'agent' | 'learner';
  text: string;
  ts?: string;
}

export interface SessionRecord {
  id: string;
  mode: string;
  is_ended?: boolean;
  mastery_delta?: number;
  next_review_eta?: string;
  conversation_turns?: ConversationTurnRecord[];
  mistakes_tagged?: string[];
  created_at?: string;
}

export interface LearnerFullHistory {
  user: {
    user_id: string;
    name: string;
    level: string;
    goal: string;
    streak_days: number;
    created_at: string;
    last_session_at?: string | null;
  };
  statistics: {
    total_sessions: number;
    total_mistakes_tagged: number;
    vocab_items_tracked: number;
    vocab_graduated: number;
  };
  sessions: SessionRecord[];
  mistake_tags: MistakeTag[];
  vocab_sample: VocabItem[];
}

export interface PlatformOverview {
  database_connected: boolean;
  active_database: string;
  total_learners_registered: number;
  total_sessions_conducted: number;
  total_mistakes_classified: number;
  configured_llm_hierarchy: {
    tier_1_ollama_host: string;
    tier_1_ollama_models: string[];
    tier_2_groq_configured: boolean;
    tier_3_gemini_configured: boolean;
  };
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

const clientCache = new Map<string, CacheEntry<any>>();
const inFlightRequests = new Map<string, Promise<any>>();

export function invalidateApiCache(pattern?: string) {
  if (!pattern) {
    clientCache.clear();
    return;
  }
  for (const key of clientCache.keys()) {
    if (key.includes(pattern)) {
      clientCache.delete(key);
    }
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  ttlMs: number = 0,
  forceRefresh: boolean = false
): Promise<T> {
  const isGet = !options.method || options.method.toUpperCase() === 'GET';
  const cacheKey = `${endpoint}`;

  if (isGet && ttlMs > 0 && !forceRefresh) {
    const cached = clientCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data as T;
    }
  }

  // Deduplicate in-flight identical GET requests to avoid duplicate network fetches
  if (isGet && inFlightRequests.has(cacheKey) && !forceRefresh) {
    return inFlightRequests.get(cacheKey)!;
  }

  const fetchPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!res.ok) {
        let errorMsg = `HTTP Error ${res.status}`;
        try {
          const errData = await res.json();
          if (errData?.error?.message) {
            errorMsg = errData.error.message;
          } else if (errData?.detail) {
            errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {}
        throw new Error(errorMsg);
      }

      const data = await res.json();

      if (isGet && ttlMs > 0) {
        clientCache.set(cacheKey, {
          data,
          timestamp: Date.now(),
          ttl: ttlMs,
        });
      }

      return data as T;
    } finally {
      if (isGet) {
        inFlightRequests.delete(cacheKey);
      }
    }
  })();

  if (isGet) {
    inFlightRequests.set(cacheKey, fetchPromise);
  }

  return fetchPromise;
}

export const api = {
  invalidateCache: invalidateApiCache,

  async onboardingStart(name: string, target_language: string = 'es', goal: string = 'travel') {
    const res = await request<{ user_id: string; placement_session_id: string; greeting?: string }>('/onboarding/start', {
      method: 'POST',
      body: JSON.stringify({ name, target_language, goal }),
    });
    invalidateApiCache('/users');
    return res;
  },

  async onboardingPlacementTurn(placement_session_id: string, learner_text: string) {
    return request<{ agent_text: string; placement_complete: boolean; level?: 'A1' | 'A2' | 'B1'; notes?: string }>(
      '/onboarding/placement/turn',
      {
        method: 'POST',
        body: JSON.stringify({ placement_session_id, learner_text }),
      }
    );
  },

  async sessionStart(user_id: string, mode: 'daily_loop' | 'review_only' = 'daily_loop') {
    return request<{ session_id: string; agent_text: string; scenario?: string }>('/session/start', {
      method: 'POST',
      body: JSON.stringify({ user_id, mode }),
    });
  },

  async sessionTurn(session_id: string, learner_text: string) {
    return request<{ agent_text: string; turn_count: number; session_complete: boolean }>('/session/turn', {
      method: 'POST',
      body: JSON.stringify({ session_id, learner_text }),
    });
  },

  async sessionEnd(session_id: string) {
    const summary = await request<SessionSummary>('/session/end', {
      method: 'POST',
      body: JSON.stringify({ session_id }),
    });
    // Invalidate caches that reflect updated learner progress and statistics
    invalidateApiCache('/progress');
    invalidateApiCache('/review');
    invalidateApiCache('/users');
    return summary;
  },

  async getReviewDue(user_id: string, forceRefresh: boolean = false) {
    return request<{ due_items: VocabItem[]; count: number }>(
      `/review/due?user_id=${encodeURIComponent(user_id)}`,
      {},
      15000,
      forceRefresh
    );
  },

  async getProgress(user_id: string, forceRefresh: boolean = false) {
    return request<ProgressData>(
      `/progress?user_id=${encodeURIComponent(user_id)}`,
      {},
      15000,
      forceRefresh
    );
  },

  async getWeeklyDigest(user_id: string) {
    return request<{ summary: string; strength: string; focus_area: string }>(`/progress/digest?user_id=${encodeURIComponent(user_id)}`);
  },

  async getLearners(limit: number = 50, forceRefresh: boolean = false) {
    return request<{ count: number; learners: LearnerSummary[] }>(
      `/users?limit=${limit}`,
      {},
      30000,
      forceRefresh
    );
  },

  async getLearnerHistory(userId: string, forceRefresh: boolean = false) {
    return request<LearnerFullHistory>(
      `/users/${encodeURIComponent(userId)}/history`,
      {},
      60000,
      forceRefresh
    );
  },

  async getPlatformOverview(forceRefresh: boolean = false) {
    return request<PlatformOverview>(
      `/users/admin/overview${forceRefresh ? '?force_refresh=true' : ''}`,
      {},
      forceRefresh ? 0 : 4000,
      forceRefresh
    );
  },
};
