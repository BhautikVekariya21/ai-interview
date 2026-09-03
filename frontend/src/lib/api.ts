/**
 * Central API client for the AI Interview frontend.
 *
 * Every network call routes through `apiFetch`, which prefixes the configured
 * `API_BASE`, attaches the stored bearer token, and normalises error handling.
 * The base URL is read from `VITE_API_BASE_URL` and falls back to the local
 * backend (`http://localhost:8000`, matching the backend `PORT` default).
 */

import { getStoredAuthToken, type AuthUser } from "./auth";

export const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
  "http://localhost:8000";

// ────────────────────────────────────────────────────────────────────────────
//  Core fetch helper
// ────────────────────────────────────────────────────────────────────────────

interface ApiFetchInit extends RequestInit {
  /** Skip attaching the Authorization header (e.g. for public endpoints). */
  skipAuth?: boolean;
}

/**
 * Wrapper around `fetch` that targets the backend base URL, injects the bearer
 * token when available, and includes credentials so cookie auth also works.
 */
export async function apiFetch(
  path: string,
  init: ApiFetchInit = {},
): Promise<Response> {
  const { skipAuth, headers, ...rest } = init;

  const request = (token?: string) => {
    const finalHeaders = new Headers(headers ?? {});
    if (!skipAuth && token && !finalHeaders.has("Authorization")) {
      finalHeaders.set("Authorization", `Bearer ${token}`);
    }
    return fetch(`${API_BASE}${path}`, {
      ...rest,
      headers: finalHeaders,
      credentials: rest.credentials ?? "include",
    });
  };

  const token = getStoredAuthToken();
  const response = await request(token);
  // Cookie-backed refresh keeps long sessions alive without exposing refresh
  // tokens to JavaScript. Retry once only to avoid loops on a bad session.
  if (response.status === 401 && !skipAuth && path !== "/auth/refresh") {
    const refreshed = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (refreshed.ok) {
      const data = (await refreshed.json()) as { access_token?: string; token?: string };
      const nextToken = data.access_token || data.token;
      if (nextToken) {
        window.dispatchEvent(new CustomEvent("auth-token-refreshed", { detail: nextToken }));
        return request(nextToken);
      }
    }
  }
  return response;
}

/** Parse a JSON response, throwing a helpful error when the request failed. */
async function jsonOrThrow<T>(res: Response): Promise<T> {
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const detail =
      (data as { detail?: string; error?: string } | null)?.detail ||
      (data as { detail?: string; error?: string } | null)?.error ||
      res.statusText ||
      "Request failed";
    throw new Error(detail);
  }

  return data as T;
}

/** POST a JSON body through `apiFetch` and return parsed JSON. */
async function postJson<T>(
  path: string,
  body: unknown,
  init: ApiFetchInit = {},
): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  headers.set("Content-Type", "application/json");
  const res = await apiFetch(path, {
    method: "POST",
    body: JSON.stringify(body),
    ...init,
    headers,
  });
  return jsonOrThrow<T>(res);
}

// ────────────────────────────────────────────────────────────────────────────
//  Shared types
// ────────────────────────────────────────────────────────────────────────────

export type { AuthUser } from "./auth";

export interface AnalyticsSummary {
  total_interviews: number;
  average_score: number;
  best_score: number;
  trend: Array<{ date?: string; score?: number }>;
  by_mode: Record<string, number>;
  weak_topics: string[];
}

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const res = await apiFetch("/v1/analytics");
  return jsonOrThrow<AnalyticsSummary>(res);
}

export interface ForgotPasswordResponse {
  success: boolean;
  message: string;
  reset_token?: string;
  reset_url?: string;
}

export interface SimpleMessageResponse {
  success: boolean;
  message: string;
}

export interface AuthenticityReport {
  ai_generated_score?: number;
  ai_generated_label?: string;
  plagiarism_score?: number;
  plagiarism_label?: string;
  summary?: string;
  score?: number;
  label?: string;
  confidence?: number;
  highlights?: unknown[];
  suggestions?: string[];
  verdict?: "authentic" | "possibly_assisted" | "likely_ai_assisted" | string;
  llm_review?: {
    ai_assisted_likelihood?: number;
    verdict?: string;
    reasoning?: string;
    flags?: string[];
  };
  [key: string]: unknown;
}

export interface BatchAuthenticitySummary {
  average_ai_generated_score: number;
  average_ai_generated_label: string;
  average_plagiarism_score: number;
  average_plagiarism_label: string;
  highest_risk_question?: { question_number: number; summary: string };
  summary: string;
  suggestions: string[];
  [key: string]: unknown;
}

// ────────────────────────────────────────────────────────────────────────────
//  Authentication
// ────────────────────────────────────────────────────────────────────────────

interface AuthTokenResponse {
  access_token?: string;
  token?: string;
  user: AuthUser;
}

export interface StoredAuthResult {
  token: string;
  user: AuthUser;
}

function normaliseAuthResponse(data: AuthTokenResponse): StoredAuthResult {
  return {
    token: data.access_token || data.token || "",
    user: data.user,
  };
}

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<StoredAuthResult> {
  const data = await postJson<AuthTokenResponse>("/auth/login", payload, {
    skipAuth: true,
  });
  return normaliseAuthResponse(data);
}

/** Exchange a verified Clerk session for the backend session used by app APIs. */
export async function exchangeClerkSession(
  clerkToken: string,
  payload: { email: string; full_name: string },
): Promise<StoredAuthResult> {
  const data = await postJson<AuthTokenResponse>("/auth/clerk/session", payload, {
    skipAuth: true,
    headers: { Authorization: `Bearer ${clerkToken}` },
  });
  return normaliseAuthResponse(data);
}

export async function signupUser(payload: {
  email: string;
  password: string;
  full_name: string;
  captcha_token?: string;
}): Promise<SimpleMessageResponse> {
  return postJson<SimpleMessageResponse>("/auth/signup", payload, {
    skipAuth: true,
  });
}

export async function verifyEmail(token: string): Promise<SimpleMessageResponse> {
  return postJson<SimpleMessageResponse>(
    "/auth/verify-email",
    { token },
    { skipAuth: true },
  );
}

export async function resendVerification(
  email: string,
): Promise<SimpleMessageResponse> {
  return postJson<SimpleMessageResponse>(
    "/auth/resend-verification",
    { email },
    { skipAuth: true },
  );
}

/**
 * Redirect the browser to the backend OAuth entrypoint. Returns a never-resolving
 * promise because the navigation unloads the page.
 */
export function oauthLogin(provider: "google" | "github" | string): Promise<never> {
  window.location.href = `${API_BASE}/auth/oauth/${provider}`;
  return new Promise<never>(() => {
    /* navigation in progress — intentionally never resolves */
  });
}

export async function logoutUser(token?: string): Promise<void> {
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  try {
    await apiFetch("/auth/logout", { method: "POST", headers });
  } catch {
    // Logout should always succeed client-side even if the call fails.
  }
}

export async function deleteUserAccount(): Promise<void> {
  const res = await apiFetch("/auth/account", { method: "DELETE" });
  await jsonOrThrow<unknown>(res);
}

export async function forgotPassword(
  email: string,
): Promise<ForgotPasswordResponse> {
  return postJson<ForgotPasswordResponse>(
    "/auth/forgot-password",
    { email },
    { skipAuth: true },
  );
}

export async function resetPassword(
  token: string,
  newPassword: string,
): Promise<void> {
  await postJson<unknown>(
    "/auth/reset-password",
    { token, new_password: newPassword },
    { skipAuth: true },
  );
}

export async function updateUserProfile(payload: {
  full_name?: string;
  email?: string;
  current_password?: string;
  new_password?: string;
}): Promise<StoredAuthResult> {
  const headers = new Headers({ "Content-Type": "application/json" });
  const res = await apiFetch("/auth/profile", {
    method: "PATCH",
    headers,
    body: JSON.stringify(payload),
  });
  const data = await jsonOrThrow<AuthTokenResponse>(res);
  return normaliseAuthResponse(data);
}

export async function fetchCurrentUser(token?: string): Promise<AuthUser> {
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await apiFetch("/auth/me", { headers });
  const data = await jsonOrThrow<{ user: AuthUser }>(res);
  return data.user;
}

// ────────────────────────────────────────────────────────────────────────────
//  Resume parsing & question generation
// ────────────────────────────────────────────────────────────────────────────

export interface AtsReport {
  score: number;
  label: string;
  has_job_description: boolean;
  summary?: string;
  sub_scores?: {
    keyword_match?: number | null;
    structure?: number;
    impact?: number;
    parse_quality?: number;
  };
  keyword_match?: {
    matched?: string[];
    missing?: string[];
    coverage?: number | null;
  };
  suggestions?: string[];
  [key: string]: unknown;
}

export interface ResumeParseResult {
  parse_time: number;
  confidence_score: number;
  data: Record<string, unknown>;
  plagiarism_report: AuthenticityReport | null;
  ats_report: AtsReport | null;
}

export async function uploadResume(file: File, jobDescription?: string): Promise<ResumeParseResult> {
  const form = new FormData();
  form.append("file", file);
  if (jobDescription && jobDescription.trim()) {
    form.append("job_description", jobDescription.trim());
  }
  const res = await apiFetch("/parse-resume", { method: "POST", body: form });
  const data = await jsonOrThrow<{
    processing_time_ms?: number;
    parse_time?: number;
    confidence_score?: number;
    data?: Record<string, unknown>;
    plagiarism_report?: AuthenticityReport | null;
    ats_report?: AtsReport | null;
  }>(res);

  const parsed = data.data ?? {};
  const rawConfidence =
    typeof data.confidence_score === "number"
      ? data.confidence_score
      : Number((parsed as { overall_parse_confidence?: number }).overall_parse_confidence ?? 0);
  // Backend emits a 0–1 confidence; the UI rounds a 0–100 percentage.
  const confidencePercent = rawConfidence <= 1 ? rawConfidence * 100 : rawConfidence;

  return {
    parse_time:
      typeof data.parse_time === "number"
        ? data.parse_time
        : (data.processing_time_ms ?? 0) / 1000,
    confidence_score: confidencePercent,
    data: parsed,
    plagiarism_report: data.plagiarism_report ?? null,
    ats_report: data.ats_report ?? null,
  };
}

export interface GeneratedQuestionDto {
  id: number;
  question: string;
  category: string;
  difficulty: string;
  /** Set only on coding questions: the bank problem the generator picked,
      so the sandbox can open that problem instead of its own default. */
  problem_id?: string | null;
}

export interface GenerateQuestionsResult {
  questions?: { questions?: GeneratedQuestionDto[] } & Record<string, unknown>;
  [key: string]: unknown;
}

export async function generateQuestions(
  file: File,
  jobDescription: string,
  difficulty: string,
  categories: string[],
  biasFree: boolean,
  numQuestions: number,
): Promise<GenerateQuestionsResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("job_description", jobDescription ?? "");
  form.append("difficulty", difficulty ?? "");
  form.append("categories", (categories ?? []).join(","));
  form.append("bias_free", String(Boolean(biasFree)));

  const res = await apiFetch(
    `/generate-questions?num_questions=${encodeURIComponent(numQuestions)}`,
    { method: "POST", body: form },
  );
  return jsonOrThrow<GenerateQuestionsResult>(res);
}

// ────────────────────────────────────────────────────────────────────────────
//  Answer evaluation
// ────────────────────────────────────────────────────────────────────────────

export interface EvaluateAnswerRequest {
  session_id: string;
  question_id: string;
  question_number: number;
  question_text: string;
  question_category: string;
  answer_text: string;
  resume_context?: Record<string, unknown>;
  generate_followup?: boolean;
}

export interface EvaluationResult {
  success: boolean;
  score: number;
  grade: string;
  strengths: string[];
  improvements: string[];
  feedback: string;
  ideal_answer?: string;
  followup_question?: string;
  follow_up_question?: string;
  authenticity_report?: AuthenticityReport;
  word_count: number;
  processing_time_ms: number;
  error?: string;
}

export async function evaluateAnswer(
  payload: EvaluateAnswerRequest,
): Promise<EvaluationResult> {
  return postJson<EvaluationResult>("/evaluation/evaluate", payload);
}

/**
 * Preferred evaluation path (requests a follow-up alongside the score). Callers
 * fall back to {@link evaluateAnswer} when this rejects.
 */
export async function evaluateAndNext(
  payload: EvaluateAnswerRequest,
): Promise<EvaluationResult> {
  return postJson<EvaluationResult>("/evaluation/evaluate", {
    ...payload,
    generate_followup: payload.generate_followup ?? true,
  });
}

export interface BatchQaPair {
  question: string;
  answer: string;
  category: string;
  question_id: string;
}

export interface BatchEvaluationResult {
  success: boolean;
  session_id: string;
  candidate_name: string;
  total_questions: number;
  answered_questions: number;
  overall_score: number;
  overall_grade: string;
  recommendation: string;
  hire_decision: string;
  category_breakdown: Record<string, unknown>;
  evaluations: Record<string, unknown>[];
  summary: string;
  strengths_overall: string[];
  improvements_overall: string[];
  plagiarism_summary: BatchAuthenticitySummary | null;
  interview_duration_estimate: string | number;
}

export async function evaluateBatch(
  sessionId: string,
  qaPairs: BatchQaPair[],
): Promise<BatchEvaluationResult> {
  return postJson<BatchEvaluationResult>("/evaluation/evaluate-batch", {
    session_id: sessionId,
    qa_pairs: qaPairs,
  });
}

export async function getQuestionHint(
  questionText: string,
): Promise<{ hint: string }> {
  return postJson<{ hint: string }>("/evaluation/hint", {
    question_text: questionText,
  });
}

export interface CodeRunResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exit_code: number | null;
  timed_out: boolean;
}

/** Run code-pad Python on the backend and return stdout/stderr. */
export async function runCode(code: string): Promise<CodeRunResult> {
  return postJson<CodeRunResult>("/execute/run", { code });
}

// ─����──────────────────────────────────────────────────────────────────────────
//  Text-to-speech & speech-to-text
// ───────────────────────��─��──────────────────────────────────────────────────

async function blobOrThrow(res: Response): Promise<Blob> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = (await res.json()) as { detail?: string; error?: string };
      detail = data.detail || data.error || detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail || "Audio request failed");
  }
  return res.blob();
}

export async function textToSpeech(
  text: string,
  voiceId?: string,
  accent?: string,
): Promise<Blob> {
  const res = await apiFetch("/tts/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      voice_id: voiceId ?? null,
      accent: accent ?? null,
    }),
  });
  return blobOrThrow(res);
}

export async function fetchQuestionSpeech(
  text: string,
  questionNumber: number,
  totalQuestions: number,
  voiceId?: string,
): Promise<Blob> {
  const params = new URLSearchParams({
    question_text: text,
    total_questions: String(totalQuestions),
  });
  if (voiceId) params.set("voice_id", voiceId);
  const res = await apiFetch(
    `/tts/interview/question/${questionNumber}?${params.toString()}`,
    { method: "POST" },
  );
  return blobOrThrow(res);
}

export interface IntroSpeechResult {
  blob: Blob;
  scriptText: string;
}

export async function fetchInterviewIntroSpeech(
  candidateName: string,
  numQuestions: number,
  resumeData?: Record<string, unknown>,
  voiceId?: string,
): Promise<IntroSpeechResult> {
  const res = await apiFetch("/tts/interview/intro/with-resume", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_name: candidateName,
      num_questions: numQuestions,
      resume_data: resumeData ?? null,
      voice_id: voiceId ?? null,
    }),
  });
  const blob = await blobOrThrow(res);
  const scriptText = res.headers.get("X-Script-Text") ?? "";
  return { blob, scriptText };
}

export async function fetchInterviewOutroSpeech(
  candidateName: string,
  numQuestions: number,
  evaluationData?: Record<string, unknown>,
  voiceId?: string,
): Promise<Blob> {
  const body = JSON.stringify({
    candidate_name: candidateName,
    num_questions: numQuestions,
    evaluation_data: evaluationData ?? null,
    voice_id: voiceId ?? null,
  });

  // Prefer the evaluation-aware outro; fall back to the generic outro.
  const withEval = await apiFetch("/tts/interview/outro/with-evaluation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  if (withEval.ok) return withEval.blob();

  const generic = await apiFetch("/tts/interview/outro", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  return blobOrThrow(generic);
}

export interface VoicePreset {
  id: string;
  [key: string]: unknown;
}

export async function fetchVoicePresets(): Promise<VoicePreset[]> {
  const res = await apiFetch("/tts/voices");
  const data = await jsonOrThrow<{ voices?: VoicePreset[] }>(res);
  return data.voices ?? [];
}

export async function transcribeAudio(
  audioBlob: Blob,
  mimeType: string,
): Promise<{ text: string } & Record<string, unknown>> {
  const form = new FormData();
  const extension = mimeType.includes("webm")
    ? "webm"
    : mimeType.includes("ogg")
      ? "ogg"
      : mimeType.includes("wav")
        ? "wav"
        : "mp3";
  form.append("file", audioBlob, `recording.${extension}`);
  const res = await apiFetch("/asr/transcribe", { method: "POST", body: form });
  return jsonOrThrow<{ text: string } & Record<string, unknown>>(res);
}

/**
 * Play an audio blob in the browser. Not a network call — resolves when playback
 * finishes and rejects if the audio element errors.
 */
export function playAudioWithFeedback(blob: Blob): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    const cleanup = () => URL.revokeObjectURL(url);
    audio.onended = () => {
      cleanup();
      resolve();
    };
    audio.onerror = () => {
      cleanup();
      reject(new Error("Audio playback failed"));
    };
    audio.play().catch((err) => {
      cleanup();
      reject(err instanceof Error ? err : new Error("Audio playback failed"));
    });
  });
}

// ────────────────────────────────────────────────────────────────────────────
//  Confidence analytics
// ────────────────────────────────────────────────────────────────────────────

export interface ConfidenceQaPair {
  question: string;
  answer: string;
  category: string;
  question_number: number;
}

export interface OverallMetrics {
  confidence_score: number;
  confidence_label: string;
  vocabulary_richness: number;
  speaking_pace_wpm: number;
  pace_label: string;
  filler_percentage: number;
  total_fillers: number;
  total_words: number;
  momentum: number;
  questions_answered: number;
  questions_total: number;
}

export interface ConfidenceCoachingTip {
  category: string;
  icon: string;
  title: string;
  tip: string;
}

export interface ConfidenceReport {
  success: boolean;
  overall: OverallMetrics;
  trajectory: number[];
  per_question: Record<string, unknown>[];
  filler_breakdown: { word: string; count: number }[];
  coaching: ConfidenceCoachingTip[];
}

export async function analyzeConfidence(
  qaPairs: ConfidenceQaPair[],
  durationSeconds: number,
): Promise<ConfidenceReport> {
  return postJson<ConfidenceReport>("/confidence/analyze", {
    qa_pairs: qaPairs,
    interview_duration_seconds: durationSeconds,
  });
}

export interface HeatmapSegment {
  text: string;
  score: number;
  start_pct: number;
  end_pct: number;
  filler_words: string[];
  flags: string[];
}

export interface HeatmapQuestion {
  question_number: number;
  question: string;
  segments: HeatmapSegment[];
  weakest_segment_index?: number;
  skipped: boolean;
}

export interface HeatmapReport {
  success: boolean;
  questions: HeatmapQuestion[];
}

export async function getInterviewHeatmap(
  qaPairs: ConfidenceQaPair[],
): Promise<HeatmapReport> {
  return postJson<HeatmapReport>("/confidence/heatmap", { qa_pairs: qaPairs });
}

// ────────────────────────────────────────────────────────────────────────────
//  Technology news
// ────────────────────────────────────────────────────────────────────────────

export interface NewsItem {
  source: string;
  title: string;
  summary: string;
  published_label: string;
  courtesy?: string;
  image_url: string;
  link: string;
  category: string;
}

export interface TechnologyNewsPayload {
  items: NewsItem[];
}

export async function fetchTechnologyNews(
  category: string,
  limit: number,
): Promise<TechnologyNewsPayload> {
  const params = new URLSearchParams({
    category,
    limit: String(limit),
  });
  const res = await apiFetch(`/news/technology?${params.toString()}`);
  return jsonOrThrow<TechnologyNewsPayload>(res);
}

// ────────────────────────────────────────────────────────────────────────────
//  Interview history
// ────────────────────────────────────────────────────────────────────────────

export interface HistoryEntry {
  id?: string;
  candidateName: string;
  date: string;
  finalScores: { overall: number; completionRate: number };
  finalGrade: string;
  totalQuestions: number;
  details_json?: string;
}

export async function getInterviewHistory(): Promise<HistoryEntry[]> {
  const res = await apiFetch("/history/");
  const data = await jsonOrThrow<HistoryEntry[] | { items?: HistoryEntry[] }>(res);
  if (Array.isArray(data)) return data;
  return data.items ?? [];
}

export async function clearInterviewHistory(): Promise<void> {
  const res = await apiFetch("/history/", { method: "DELETE" });
  await jsonOrThrow<unknown>(res);
}

export async function saveInterviewHistory(
  entry: {
    candidateName: string;
    finalScores: { overall: number; completionRate: number };
    finalGrade: string;
    totalQuestions: number;
    date?: string;
    details_json?: string;
  } & Record<string, unknown>,
): Promise<HistoryEntry> {
  return postJson<HistoryEntry>("/history/", entry);
}

// ────────────────────────────────────────────────────────────────────────────
//  Contact form
// ────────────────────────────────────────────────────────────��───────────────

export async function submitContactForm(payload: {
  name: string;
  email: string;
  subject: string;
  message: string;
}): Promise<{ success: boolean; message: string; submission_id?: string }> {
  return postJson<{ success: boolean; message: string; submission_id?: string }>(
    "/contact/submit",
    payload,
    { skipAuth: true },
  );
}

// ──���─────────────────────────────────────────────────────────────────────────
//  Community blog
// ────────────────────────────────────────────────────────────────────────────

export interface BlogPost {
  id: string;
  author_name: string;
  title: string;
  category: string;
  excerpt: string;
  content: string;
  created_at?: string;
}

export interface BlogFeedback {
  id: string;
  author_name: string;
  rating: number;
  comment: string;
  created_at?: string;
}

export async function fetchBlogPosts(category?: string, limit = 50): Promise<BlogPost[]> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  params.set("limit", String(limit));
  const res = await apiFetch(`/blog/posts?${params.toString()}`, { skipAuth: true });
  const data = await jsonOrThrow<BlogPost[] | { items?: BlogPost[] }>(res);
  return Array.isArray(data) ? data : data.items ?? [];
}

export interface BlogFeedItem {
  id: string;
  title: string;
  excerpt: string;
  link: string;
  image_url: string;
  source: string;
  courtesy?: string;
  read_time: string;
  published_label: string;
  category: string;
}

export interface BlogFeedPayload {
  items: BlogFeedItem[];
  categories: string[];
  sources: string[];
}

export async function fetchBlogFeed(category?: string, limit = 30): Promise<BlogFeedPayload> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  params.set("limit", String(limit));
  const res = await apiFetch(`/blog/feed?${params.toString()}`, { skipAuth: true });
  return jsonOrThrow<BlogFeedPayload>(res);
}

export async function createBlogPost(payload: {
  title: string;
  category: string;
  excerpt: string;
  content: string;
}): Promise<BlogPost> {
  return postJson<BlogPost>("/blog/posts", payload);
}

export async function fetchBlogFeedback(postId: string): Promise<BlogFeedback[]> {
  const res = await apiFetch(`/blog/posts/${encodeURIComponent(postId)}/feedback`, { skipAuth: true });
  const data = await jsonOrThrow<BlogFeedback[] | { items?: BlogFeedback[] }>(res);
  return Array.isArray(data) ? data : data.items ?? [];
}

export async function submitBlogFeedback(
  postId: string,
  payload: { rating: number; comment: string },
): Promise<BlogFeedback> {
  return postJson<BlogFeedback>(`/blog/posts/${encodeURIComponent(postId)}/feedback`, payload);
}

export interface SubscribeResult {
  status: string;
  already_subscribed?: boolean;
}

export async function subscribeNewsletter(email: string): Promise<SubscribeResult> {
  return postJson<SubscribeResult>("/blog/subscribe", { email }, { skipAuth: true });
}

// ────────────────────────────────────────────────────────────────────────────
//  App reviews (feedback forum)
// ────────────────────────────────────────────────────────────────────────────

export interface AppReview {
  id: string;
  author_name: string;
  rating: number;
  title: string;
  review: string;
  created_at?: string;
}

export interface AppReviewList {
  items: AppReview[];
  total: number;
  average: number;
}

export async function fetchAppReviews(limit = 50): Promise<AppReviewList> {
  const res = await apiFetch(`/reviews/?limit=${limit}`, { skipAuth: true });
  return jsonOrThrow<AppReviewList>(res);
}

export async function submitAppReview(payload: {
  rating: number;
  title: string;
  review: string;
}): Promise<AppReview> {
  return postJson<AppReview>("/reviews/", payload);
}

// ────────────────────────────────────────────────────────────────────────────
//  Cloud session sync
// ────────────────────────────────────────────────────────────────────────────

export async function loadCloudSession(
  token: string | null,
): Promise<{ session: Record<string, unknown> | null }> {
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await apiFetch("/user-data/session", { headers });
  return jsonOrThrow<{ session: Record<string, unknown> | null }>(res);
}

export async function saveCloudSession(
  token: string | null,
  session: Record<string, unknown>,
): Promise<void> {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await apiFetch("/user-data/session", {
    method: "PUT",
    headers,
    body: JSON.stringify({ session }),
  });
  await jsonOrThrow<unknown>(res);
}

// ───────────────────────������───���───────────────────────────────────────────────
//  AI Panel Interview (Module 13)
// ────────────────────────────────────────────────────────────────────────────

export interface PanelPersona {
  id: string;
  name: string;
  role: string;
  emoji: string;
  accent: string;
  temperament: string;
}

export interface PanelReaction {
  success: boolean;
  persona_id: string;
  name: string;
  role: string;
  emoji: string;
  accent: string;
  reaction: string;
  follow_up: string;
  impression: "impressed" | "neutral" | "unconvinced";
  lean: number;
}

export interface PanelMember {
  persona_id: string;
  name: string;
  role: string;
  emoji: string;
  accent: string;
  argument: string;
  vote: "hire" | "no_hire" | "borderline";
  confidence: number;
  one_line: string;
}

export interface PanelVerdict {
  decision: string;
  hire_votes: number;
  total_votes: number;
  confidence: number;
  summary: string;
}

export interface PanelDeliberation {
  success: boolean;
  candidate_name: string;
  average_score: number;
  members: PanelMember[];
  verdict: PanelVerdict;
}

export interface PanelTranscriptItem {
  question: string;
  answer: string;
  category?: string;
}

export async function fetchPanelPersonas(): Promise<PanelPersona[]> {
  const res = await apiFetch("/api/v1/panel/personas", { skipAuth: true });
  const data = await jsonOrThrow<{ personas: PanelPersona[] }>(res);
  return data.personas ?? [];
}

export async function fetchPanelReaction(payload: {
  persona_id: string;
  question: string;
  answer: string;
  category?: string;
}): Promise<PanelReaction> {
  const res = await apiFetch("/api/v1/panel/react", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category: "T", ...payload }),
  });
  return jsonOrThrow<PanelReaction>(res);
}

export async function fetchPanelDeliberation(payload: {
  candidate_name: string;
  transcript: PanelTranscriptItem[];
}): Promise<PanelDeliberation> {
  const res = await apiFetch("/api/v1/panel/deliberate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<PanelDeliberation>(res);
}

// ────────────────────────────────────────────────────────────────────────────
//  RAG (Module 14): retrieval-grounded questions, similarity proctoring,
//  adaptive difficulty, company context, and final report.
// ────────────────────────────────────────────────────────────────────────────

export interface RagViolationEvent {
  type: string;
  severity: string;
  message: string;
  similarity: number;
  matched_source_type: string;
}

export interface RagSimilarityResult {
  flagged: boolean;
  threshold: number;
  max_similarity: number;
  matches: Array<{
    chunk_id: string;
    source_type: string;
    text: string;
    similarity: number;
    distance: number;
  }>;
  violation: RagViolationEvent | null;
}

/**
 * Check an answer for near-duplicate similarity against past candidates' answers
 * and the canned reference set. When `flagged`, the returned `violation` should
 * be surfaced with the existing proctoring toast pattern.
 */
export async function detectAnswerSimilarity(payload: {
  answer: string;
  role: string;
  candidate_id?: string;
  threshold?: number;
}): Promise<RagSimilarityResult> {
  const res = await apiFetch("/rag/detect-similarity", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<RagSimilarityResult>(res);
}

export interface RagDifficultyResult {
  recommended_difficulty: "easy" | "medium" | "hard" | "expert" | string;
  reason: string;
}

export async function adjustQuestionDifficulty(payload: {
  role: string;
  recent_answers: string[];
  current_difficulty?: string;
}): Promise<RagDifficultyResult> {
  const res = await apiFetch("/rag/adjust-difficulty", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<RagDifficultyResult>(res);
}

export interface RagReportResult {
  session_id: string;
  role: string;
  candidate_name: string | null;
  overall_score: number | null;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendation: string;
  per_question_notes: Array<Record<string, unknown>>;
  evidence: Array<Record<string, unknown>>;
}

export async function generateRagReport(payload: {
  session_id: string;
  role: string;
  qa_pairs: Array<{ question: string; answer?: string; score?: number }>;
  candidate_name?: string;
}): Promise<RagReportResult> {
  const res = await apiFetch("/rag/generate-report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<RagReportResult>(res);
}

export interface RagCompanyContextResult {
  company_id: string;
  chunks_indexed: number;
}

/**
 * Upload role-specific company docs (tech stack, standards). They are embedded
 * into a per-company FAISS namespace and folded into retrieval when a matching
 * `company_id` is passed to question generation.
 */
export async function uploadCompanyContext(payload: {
  company_id: string;
  documents: string[];
  role?: string;
}): Promise<RagCompanyContextResult> {
  const res = await apiFetch("/rag/company-context", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<RagCompanyContextResult>(res);
}

// ────────────────────────────────────────────────────────────────────────────
//  Code Execution Sandbox (Module 16)
// ────────────────────────────────────────────────────────────────────────────

/** Languages the sandbox can request a starter for. Mirrors
    `static_harness.starter_languages()` plus the dynamic runners. */
export type SupportedCodingLang =
  | "python"
  | "javascript"
  | "typescript"
  | "java"
  | "cpp"
  | "csharp"
  | "go"
  | "rust"
  | "ruby"
  | "php"
  | "swift"
  | "objectivec"
  | "erlang"
  | "haskell"
  | "sql";

/** One column of a database table in a schema figure. */
export interface SchemaColumnSpec {
  name: string;
  type: string;
  /** PK / UQ / FK badge, or empty for a plain column. */
  key?: string;
}

/** One table of a database schema figure, with a few seeded rows. */
export interface SchemaTableSpec {
  name: string;
  columns: SchemaColumnSpec[];
  rows?: Array<Array<string | number | null>>;
  /** Rows the seed inserts beyond those shown, so the figure can say so
      instead of silently truncating. */
  more?: number;
}

/** The table a database query must return, for `kind === "sql_example"`.
    `columns` is empty when headers could not be read cleanly off the
    reference query — better unlabelled than mislabelled. */
export interface SqlResultSpec {
  columns: string[];
  rows: Array<Array<string | number | null>>;
  more?: number;
}

/** Figure spec for one example, drawn by `ProblemDiagram`. Computed by the
    backend from the example's own input, so it cannot disagree with the text. */
export interface DiagramSpec {
  kind:
    | "bars"
    | "array"
    | "grid"
    | "linked"
    | "string"
    | "tree"
    | "schema"
    | "sql_example";
  values?: Array<string | number | null>;
  rows?: string[][];
  label?: string;
  /** Present for `kind === "schema"` and `"sql_example"` — the problem's
      database tables, seeded with this example's own rows. */
  tables?: SchemaTableSpec[];
  /** Present only for `kind === "sql_example"` — the expected result table. */
  result?: SqlResultSpec;
}

export interface CodingProblem {
  id: string;
  title: string;
  difficulty: "Easy" | "Medium" | "Hard";
  category: string;
  tags: string[];
  companies: string[];
  description: string;
  /** Newline-separated. One clause per line, so the pane renders them as a list. */
  constraints: string;
  /** Replayed from the graded test cases, so an example can never disagree with
      what the judge asserts. `explanation` is present only where a generated
      statement supplied one; `diagram` only on the first example, and only
      where the input has a shape worth drawing. */
  examples: Array<{
    input: string;
    output: string;
    explanation?: string;
    diagram?: DiagramSpec;
  }>;
  /** The optimal-complexity nudge a judge closes with. Derived from the
      problem's own stated complexity, so it is absent when that is unknown. */
  follow_up?: string | null;
  hints?: string[];
  /** The backend emits a starter per supported language, but which languages
      are covered depends on whether a signature could be inferred for the
      problem — so every lookup is treated as possibly absent. */
  starter_code: Partial<Record<SupportedCodingLang, string>>;
  /** CREATE TABLE statements for database problems; absent for coding ones. */
  sql_schema?: string[];
  /** How the backend grades a submission. `"stdio"` marks an imported
      whole-program problem: the answer reads standard input and writes standard
      output instead of filling in a function body, which changes both the
      languages it can be graded in and what the test-case panes hold. */
  grading?: string;
  /** Imported problems grade against hidden judge suites in addition to the
      samples shown — this is how many. Present only when the fetched corpus
      carried them, so its absence means sample-only grading. */
  hidden_test_count?: number;
}

export interface TestCaseResult {
  passed: boolean;
  /** Runner output; shape depends on the problem (scalar, array, row set...). */
  actual: unknown;
  expected: unknown;
}

export interface RunCodeResponseDto {
  success: boolean;
  passed: boolean;
  runtime_ms: number;
  test_results: TestCaseResult[];
  stdout: string;
  stderr: string;
  error?: string;
}

export interface SubmitCodeResponseDto {
  success: boolean;
  passed: boolean;
  runtime_ms: number;
  test_results: TestCaseResult[];
  ai_analysis: string;
  error?: string;
  submission_id?: string | null;
  session_id?: string | null;
}

export interface CodingSubmissionDto {
  id: string;
  session_id: string;
  problem_id: string;
  problem_title: string;
  language: string;
  passed: boolean;
  tests_passed: number;
  tests_total: number;
  runtime_ms: number;
  created_at?: string | null;
}

/**
 * The default practice list — metadata only, no statements.
 *
 * The imported competition corpus is ~1,900 statements, so shipping every
 * description and starter on each practice-page open would be a multi-MB
 * payload. The list carries just enough to name and order problems; the
 * sandbox fetches a problem's full detail by id when it is opened, exactly
 * like a catalogue pick.
 */
export async function fetchCodingProblems(): Promise<CodingProblemSummary[]> {
  const res = await apiFetch("/coding/problems", { skipAuth: true });
  const data = await jsonOrThrow<{ problems: CodingProblemSummary[] }>(res);
  return data.problems;
}

/** One row of the practice problem list — metadata only, no description. */
export interface CodingProblemSummary {
  id: string;
  title: string;
  difficulty: "Easy" | "Medium" | "Hard";
  category: string;
  tags: string[];
  companies: string[];
  /** "curated" problems are hand-written; "imported" are competition
      statements; "bank" is the generated 1000-problem set. */
  source: "curated" | "imported" | "bank";
}

export interface CodingCatalogPage {
  problems: CodingProblemSummary[];
  total: number;
  offset: number;
  limit: number;
  topics: string[];
}

/**
 * Browse the whole problem catalogue (~1000 entries), not just the default
 * practice set `/coding/problems` returns. Search and paging are server-side
 * because shipping the full bank on every render is wasteful.
 */
export async function fetchCodingCatalog(params: {
  search?: string;
  difficulty?: string;
  topic?: string;
  source?: string;
  offset?: number;
  limit?: number;
} = {}): Promise<CodingCatalogPage> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.difficulty) query.set("difficulty", params.difficulty);
  if (params.topic) query.set("topic", params.topic);
  if (params.source) query.set("source", params.source);
  query.set("offset", String(params.offset ?? 0));
  query.set("limit", String(params.limit ?? 100));
  const res = await apiFetch(`/coding/problems/catalog?${query.toString()}`, {
    skipAuth: true,
  });
  return jsonOrThrow<CodingCatalogPage>(res);
}

export async function fetchCodingProblem(id: string): Promise<CodingProblem> {
  const res = await apiFetch(`/coding/problems/${encodeURIComponent(id)}`, { skipAuth: true });
  return jsonOrThrow<CodingProblem>(res);
}

export async function runCodingSolution(
  problemId: string,
  language: string,
  code: string,
): Promise<RunCodeResponseDto> {
  return postJson<RunCodeResponseDto>("/coding/run", {
    problem_id: problemId,
    language,
    code,
  });
}

export async function submitCodingSolution(
  problemId: string,
  language: string,
  code: string,
  sessionId?: string,
): Promise<SubmitCodeResponseDto> {
  return postJson<SubmitCodeResponseDto>("/coding/submit", {
    problem_id: problemId,
    language,
    code,
    session_id: sessionId ?? null,
  });
}

/** Submissions recorded against one interview sitting, newest first. */
export async function fetchCodingSubmissions(
  sessionId: string,
  limit = 100,
): Promise<CodingSubmissionDto[]> {
  const res = await apiFetch(
    `/coding/submissions?session_id=${encodeURIComponent(sessionId)}&limit=${limit}`,
  );
  const data = await jsonOrThrow<{ items: CodingSubmissionDto[] }>(res);
  return data.items;
}

// ────────────────────────────────────────────────────────────────────────────
//  Proctoring — screen recording + integrity events (Module 17)
// ────────────────────────────────────────────────────────────────────────────

/** Which part of the sitting a recording or event belongs to. */
export type ProctorSurface = "interview" | "coding";

/**
 * The integrity events the backend knows how to file. Kept as a union so a typo
 * in a call site is a compile error rather than a mystery line in the log.
 */
export type ProctorEventKind =
  | "screen_share_granted"
  | "screen_share_denied"
  | "screen_share_stopped"
  | "screen_share_wrong_surface"
  | "recorder_error"
  | "upload_failed"
  | "tab_switch"
  | "window_blur"
  | "fullscreen_exit"
  | "devtools_blocked"
  | "copy_blocked"
  | "paste_blocked";

export interface ProctorConfigDto {
  enabled: boolean;
  required: boolean;
  chunk_interval_ms: number;
  max_chunk_bytes: number;
}

export interface ProctorChunkUploadDto {
  success: boolean;
  filename: string;
  chunk_index: number;
  total_bytes: number;
}

/** Whether screen recording is on, and how often to hand back a chunk. */
export async function fetchProctorConfig(): Promise<ProctorConfigDto> {
  const res = await apiFetch("/proctor/config", { skipAuth: true });
  return jsonOrThrow<ProctorConfigDto>(res);
}

/**
 * Upload one `MediaRecorder` blob. Chunks are appended server-side into a single
 * file per surface, so they must be sent in order.
 *
 * `FormData` sets its own multipart boundary — passing an explicit
 * `Content-Type` here would produce an unparseable body, which is why this does
 * not go through `postJson`.
 */
export async function uploadScreenChunk(params: {
  sessionId: string;
  surface: ProctorSurface;
  chunkIndex: number;
  blob: Blob;
}): Promise<ProctorChunkUploadDto> {
  const form = new FormData();
  const extension = params.blob.type.includes("mp4") ? "mp4" : "webm";
  form.append("file", params.blob, `chunk.${extension}`);

  const query = new URLSearchParams({
    session_id: params.sessionId,
    surface: params.surface,
    chunk_index: String(params.chunkIndex),
  });
  const res = await apiFetch(`/proctor/screen/chunk?${query}`, {
    method: "POST",
    body: form,
  });
  return jsonOrThrow<ProctorChunkUploadDto>(res);
}

export interface ProctorRecordingInfo {
  filename: string;
  surface: string;
  size_bytes: number;
  created_at: string;
  modified_at: string;
}

export interface ProctorSessionRecordings {
  session_id: string;
  recordings: ProctorRecordingInfo[];
  events: Record<string, unknown>[];
  total_bytes: number;
}

/** What was captured for one sitting — used by the Replay Studio to surface
    proctoring evidence in the replay timeline. */
export async function fetchProctorSession(
  sessionId: string,
): Promise<ProctorSessionRecordings> {
  const res = await apiFetch(`/proctor/session/${encodeURIComponent(sessionId)}`);
  return jsonOrThrow<ProctorSessionRecordings>(res);
}

/**
 * File an integrity event. Deliberately swallows its own failures: a proctoring
 * log that throws into the interview UI would turn a flaky network into a broken
 * interview, and the recording itself is the primary evidence.
 */
export async function recordProctorEvent(payload: {
  sessionId: string;
  surface: ProctorSurface;
  kind: ProctorEventKind;
  detail?: string;
  questionIndex?: number;
}): Promise<void> {
  try {
    await postJson<{ success: boolean }>("/proctor/event", {
      session_id: payload.sessionId,
      surface: payload.surface,
      kind: payload.kind,
      detail: payload.detail ?? null,
      question_index: payload.questionIndex ?? null,
      occurred_at: new Date().toISOString(),
    });
  } catch {
    // Best effort by design — see above.
  }
}

// ────────────────────────────────────────────────────────────────────────────
//  Evidence coaching — gap reports, coach tips
// ────────────────────────────────────────────────────────────────────────────

export interface GapFocusArea {
  claim: string;
  status: string;
  why: string;
  actions: string[];
}

export interface AtsGapItem {
  keyword: string;
  action: string;
}

export interface GapReportResult {
  overview: string;
  focus_areas: GapFocusArea[];
  ats_gaps: AtsGapItem[];
  next_round_probes: string[];
  resources: string[];
  generated_by: string;
}

/**
 * Build a resume-vs-reality action plan from Resume Proof Map findings plus
 * ATS keyword gaps. The backend falls back to a deterministic plan when no
 * LLM provider is configured.
 */
export async function generateGapReport(payload: {
  resume_data?: Record<string, unknown> | null;
  ats_report?: Record<string, unknown> | null;
  assessments?: Record<string, unknown>[];
  candidate_name?: string;
  target_role?: string;
}): Promise<GapReportResult> {
  return postJson<GapReportResult>("/api/v1/evidence/gap-report", payload);
}

export interface CoachTipResult {
  category: string;
  icon: string;
  title: string;
  tip: string;
}

/** A single focused delivery tip computed from the last answer's signals. */
export async function getCoachTip(payload: {
  answer_text?: string;
  word_count?: number;
  filler_percentage?: number;
  filler_count?: number;
  wpm?: number;
  confidence_score?: number;
  momentum?: string;
  question?: string;
}): Promise<CoachTipResult> {
  return postJson<CoachTipResult>("/api/v1/evidence/coach-tip", payload);
}

// ────────────────────────────────────────────────────────────────────────────
//  Interview League — ELO ratings over the graded coding corpus
// ────────────────────────────────────────────────────────────────────────────

export interface LeagueTier {
  tier: string;
  label: string;
  color: string;
}

export interface LeagueRatingResult {
  rating: number;
  tier: LeagueTier;
  games: number;
  wins: number;
  win_rate: number;
  /** True until the player has 3+ graded submissions (chess-style provisional). */
  provisional?: boolean;
  last_deltas?: number[];
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  name: string;
  rating: number;
  tier: LeagueTier;
  games: number;
  wins: number;
  win_rate: number;
  /** True until the player has 3+ graded submissions (chess-style provisional). */
  provisional?: boolean;
}

export interface LeaderboardResult {
  entries: LeaderboardEntry[];
  generated_at: string;
}

export async function getLeagueRating(): Promise<LeagueRatingResult> {
  const res = await apiFetch("/league/rating");
  return jsonOrThrow<LeagueRatingResult>(res);
}

export async function getLeagueLeaderboard(limit = 20): Promise<LeaderboardResult> {
  const res = await apiFetch(`/league/leaderboard?limit=${limit}`);
  return jsonOrThrow<LeaderboardResult>(res);
}

// ────────────────────────────────────────────────────────────────────────────
//  The Gauntlet — adaptive interview pressure engine
// ────────────────────────────────────────────────────────────────────────────

export interface GauntletPersona {
  id: string;
  name: string;
  emoji: string;
  temperament: string;
  voice_hint?: string;
}

export type GauntletAction =
  | "steady"
  | "escalate_followup"
  | "interrupt"
  | "persona_shift"
  | "time_pressure"
  | "deescalate";

export interface GauntletStepResult {
  level: number;
  level_name: string;
  action: GauntletAction | string;
  message: string;
  escalated: boolean;
  persona: GauntletPersona | null;
  evidence?: Record<string, unknown>;
}

/**
 * Compute the next adaptive-pressure move from the candidate's recent scores.
 * Stateless — the frontend holds the evidence and the engine decides the move.
 */
export async function advanceGauntlet(payload: {
  recent_scores: number[];
  current_level?: number;
  answered_count?: number;
  momentum?: string;
  max_level?: number;
}): Promise<GauntletStepResult> {
  return postJson<GauntletStepResult>("/api/v1/gauntlet/advance", payload);
}

// ────────────────────────────────────────────────────────────────────────────
//  Game Tape — replay documents with share tokens
// ────────────────────────────────────────────────────────────────────────────

/** One question's transcript row, captured at interview time. */
export interface ReplayQaPair {
  question_number: number;
  question: string;
  answer: string;
  category?: string;
  score?: number | null;
  grade?: string | null;
  feedback?: string | null;
}

export interface ReplayHeatmapSegment {
  text: string;
  score: number | null;
  start_pct: number;
  end_pct: number;
  flags: string[];
}

export type ReplayTimelineEntry =
  | {
      type: "question";
      question_number: number;
      text: string;
    }
  | {
      type: "answer";
      question_number: number;
      text: string;
      score: number | null;
      grade?: string | null;
      feedback?: string | null;
      segments: ReplayHeatmapSegment[];
    }
  | {
      type: "proctor";
      kind: string;
      label: string;
      severity: string;
      detail?: string | null;
      occurred_at?: string | null;
    };

export interface ReplayStats {
  average_score: number | null;
  answered_questions: number;
  total_questions: number;
  proctor_events_total: number;
  violations: number;
  weakest_question?: { question_number: number; score: number } | null;
}

export interface ReplayDocument {
  version: number;
  meta: Record<string, unknown>;
  timeline: ReplayTimelineEntry[];
  stats: ReplayStats;
}

export interface ReplayBuildPayload {
  meta: Record<string, unknown>;
  qa_pairs: ReplayQaPair[];
  heatmap?: { questions?: HeatmapQuestion[] } | null;
  proctor_events?: Record<string, unknown>[] | null;
}

/**
 * Normalise transcript + heatmap + proctor events into a replay document.
 * Stateless — the studio previews with this before deciding to share.
 */
export async function buildReplay(
  payload: ReplayBuildPayload,
): Promise<ReplayDocument> {
  return postJson<ReplayDocument>("/api/v1/replay/build", payload);
}

/**
 * Persist a replay and mint a share token. Re-saving the same session returns
 * the same token, so sharing twice gives one stable link.
 */
export async function saveReplay(
  payload: ReplayBuildPayload & { session_id?: string | null },
): Promise<{ token: string }> {
  return postJson<{ token: string }>("/api/v1/replay/save", payload);
}

/** Fetch a shared replay document by its token (public). */
export async function fetchReplay(
  token: string,
): Promise<{ replay: ReplayDocument }> {
  const res = await apiFetch(`/api/v1/replay/${encodeURIComponent(token)}`, {
    skipAuth: true,
  });
  return jsonOrThrow<{ replay: ReplayDocument }>(res);
}

// ────────────────────────────────────────────────────────────────────────────
//  Company Lens — employer-published exams with standardized scorecards
// ────────────────────────────────────────────────────────────────────────────

export interface LensExamQuestion {
  id: string;
  question_number: number;
  question: string;
  category: string;
  difficulty: string;
  /** Only present on the employer's exam detail — never sent to candidates. */
  ideal_answer?: string | null;
}

export interface LensAttemptSummary {
  id: string;
  candidate_name: string;
  overall_score: number;
  overall_grade: string;
  recommendation: string;
  hire_decision: string;
  attempt_token?: string | null;
  created_at?: string | null;
}

export interface LensExamSummary {
  id: string;
  title: string;
  target_role: string;
  question_count: number;
  difficulty: string;
  status: "draft" | "published" | string;
  share_token?: string | null;
  attempts: number;
  created_at?: string | null;
}

/**
 * The detail endpoint expands `attempts` from a count into the full list of
 * candidate attempts, so the summary's numeric field is omitted here.
 */
export interface LensExamDetail extends Omit<LensExamSummary, "attempts"> {
  job_description: string;
  questions: LensExamQuestion[];
  attempts: LensAttemptSummary[];
}

export interface LensAnswerResult {
  question_number: number;
  question: string;
  category: string;
  answer: string;
  score: number;
  grade: string;
  feedback: string;
  strengths: string[];
  improvements: string[];
  authenticity?: AuthenticityReport | null;
}

export interface LensScorecard {
  candidate_name: string;
  exam_title: string;
  overall_score: number;
  overall_grade: string;
  recommendation: string;
  hire_decision: string;
  summary: string;
  category_breakdown: Record<string, number>;
  answered_questions: number;
  total_questions: number;
  answers: LensAnswerResult[];
  plagiarism_summary?: BatchAuthenticitySummary | null;
  generated_by: string;
}

export interface LensShareExam {
  id: string;
  title: string;
  target_role: string;
  question_count: number;
  difficulty: string;
  questions: Array<{
    question_number: number;
    question: string;
    category: string;
    difficulty: string;
  }>;
}

export interface LensSubmitPayload {
  candidate_name: string;
  answers: Array<{ question_number: number; answer: string }>;
}

export async function createLensExam(payload: {
  title: string;
  target_role: string;
  job_description: string;
  question_count?: number;
  difficulty?: string;
}): Promise<LensExamDetail> {
  return postJson<LensExamDetail>("/api/v1/lens/exams", payload);
}

export async function listLensExams(): Promise<LensExamSummary[]> {
  const res = await apiFetch("/api/v1/lens/exams");
  const data = await jsonOrThrow<{ exams: LensExamSummary[] }>(res);
  return data.exams ?? [];
}

/**
 * Browse published exams in the public directory (no account needed). The
 * optional `role` phrase filters exams whose title, role, or job description
 * mention it — powers the directory's search box.
 */
export async function listPublishedLensExams(
  role?: string,
): Promise<LensExamSummary[]> {
  const params = new URLSearchParams();
  if (role && role.trim()) params.set("role", role.trim());
  const query = params.toString();
  const res = await apiFetch(`/api/v1/lens/directory${query ? `?${query}` : ""}`, {
    skipAuth: true,
  });
  const data = await jsonOrThrow<{ exams: LensExamSummary[] }>(res);
  return data.exams ?? [];
}

export async function getLensExam(id: string): Promise<LensExamDetail> {
  const res = await apiFetch(`/api/v1/lens/exams/${encodeURIComponent(id)}`);
  return jsonOrThrow<LensExamDetail>(res);
}

export async function publishLensExam(id: string): Promise<{ token: string }> {
  return postJson<{ token: string }>(`/api/v1/lens/exams/${encodeURIComponent(id)}/publish`, {});
}

export async function deleteLensExam(id: string): Promise<void> {
  const res = await apiFetch(`/api/v1/lens/exams/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  await jsonOrThrow<{ success: boolean }>(res);
}

/** Candidate-facing exam by share token (public). */
export async function fetchLensShareExam(token: string): Promise<LensShareExam> {
  const res = await apiFetch(`/api/v1/lens/share/${encodeURIComponent(token)}`, {
    skipAuth: true,
  });
  return jsonOrThrow<LensShareExam>(res);
}

/** Submit an exam attempt (public) and get the standardized scorecard. */
export async function submitLensExam(
  token: string,
  payload: LensSubmitPayload,
): Promise<{ scorecard: LensScorecard; attempt_token: string }> {
  return postJson<{ scorecard: LensScorecard; attempt_token: string }>(
    `/api/v1/lens/share/${encodeURIComponent(token)}/submit`,
    payload,
    { skipAuth: true },
  );
}

/** Fetch a stored scorecard by its attempt token (public). */
export async function fetchLensAttemptScorecard(
  attemptToken: string,
): Promise<{ scorecard: LensScorecard }> {
  const res = await apiFetch(`/api/v1/lens/attempts/${encodeURIComponent(attemptToken)}`, {
    skipAuth: true,
  });
  return jsonOrThrow<{ scorecard: LensScorecard }>(res);
}
