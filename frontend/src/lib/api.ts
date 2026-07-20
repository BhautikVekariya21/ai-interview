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

  const finalHeaders = new Headers(headers ?? {});
  if (!skipAuth) {
    const token = getStoredAuthToken();
    if (token && !finalHeaders.has("Authorization")) {
      finalHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  return fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: finalHeaders,
    credentials: rest.credentials ?? "include",
  });
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

// ────────────────────────────────────────────────────────────────────────────
//  Text-to-speech & speech-to-text
// ────────────────────────────────────────────────────────────────────────────

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
// ────────────────────────────────────────────────────────────────────────────

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

// ────────────────────────────────────────────────────────────────────────────
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

// ────────────────────────────────────────────────────────────────────────────
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
