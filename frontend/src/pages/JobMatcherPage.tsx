import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, CheckCircle2, Target, TriangleAlert } from "lucide-react";
import PublicNavbar from "@/components/PublicNavbar";
import { apiFetch } from "@/lib/api";

export default function JobMatcherPage() {
  const navigate = useNavigate();
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [resume, setResume] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError("");
    try {
      const response = await apiFetch("/v1/job-matches", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_title: jobTitle, company, job_description: jobDescription, resume }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not analyze this match");
      setResult(data);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not analyze this match"); }
    finally { setLoading(false); }
  }

  return <div className="min-h-screen bg-background text-foreground"><PublicNavbar /><main className="mx-auto max-w-6xl px-6 pb-16 pt-32">
    <div className="mb-10 max-w-2xl"><p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-brand">Career fit lab</p><h1 className="text-4xl font-bold tracking-tight md:text-6xl">Turn a job description into your practice plan.</h1><p className="mt-5 text-lg leading-7 text-muted-foreground">Compare your experience to a role, find the gaps that matter, and get interview questions tailored to this exact opportunity.</p></div>
    <div className="grid gap-6 lg:grid-cols-[1fr_0.85fr]">
      <form onSubmit={submit} className="rounded-3xl border border-border bg-card p-6 shadow-sm md:p-8"><div className="mb-6 grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium">Role<input value={jobTitle} onChange={e=>setJobTitle(e.target.value)} className="mt-2 w-full rounded-xl border border-border bg-background px-4 py-3 outline-none focus:border-brand" placeholder="Senior product designer" /></label><label className="text-sm font-medium">Company<input value={company} onChange={e=>setCompany(e.target.value)} className="mt-2 w-full rounded-xl border border-border bg-background px-4 py-3 outline-none focus:border-brand" placeholder="Acme" /></label></div><label className="text-sm font-medium">Job description<textarea required minLength={80} value={jobDescription} onChange={e=>setJobDescription(e.target.value)} className="mt-2 min-h-52 w-full resize-y rounded-xl border border-border bg-background px-4 py-3 outline-none focus:border-brand" placeholder="Paste the job description..." /></label><label className="mt-5 block text-sm font-medium">Your resume or experience<textarea required minLength={30} value={resume} onChange={e=>setResume(e.target.value)} className="mt-2 min-h-44 w-full resize-y rounded-xl border border-border bg-background px-4 py-3 outline-none focus:border-brand" placeholder="Paste your resume or a concise experience summary..." /></label>{error && <p className="mt-4 text-sm text-destructive">{error}</p>}<button disabled={loading} className="mt-6 inline-flex items-center gap-2 rounded-xl bg-brand px-5 py-3 font-semibold text-brand-foreground disabled:opacity-60">{loading ? "Analyzing..." : "Analyze match"}<ArrowRight className="h-4 w-4" /></button></form>
      <section className="rounded-3xl border border-border bg-card p-6 shadow-sm md:p-8">{!result ? <div className="flex h-full min-h-80 flex-col justify-center"><Target className="mb-5 h-10 w-10 text-brand" /><h2 className="text-2xl font-bold">Your match report</h2><p className="mt-3 leading-7 text-muted-foreground">You’ll see a fit score, strengths to emphasize, skill gaps to close, and questions to rehearse.</p></div> : <div><div className="flex items-end justify-between border-b border-border pb-6"><div><p className="text-sm text-muted-foreground">Match score</p><p className="mt-1 text-6xl font-bold text-brand">{result.match_score}<span className="text-2xl text-muted-foreground">/100</span></p></div><CheckCircle2 className="h-8 w-8 text-brand" /></div><div className="mt-6 space-y-6"><ReportList title="Strengths to lead with" items={result.strengths} icon={<CheckCircle2 className="h-4 w-4" />} /><ReportList title="Gaps to practice" items={result.skill_gaps} icon={<TriangleAlert className="h-4 w-4" />} /><ReportList title="Questions to rehearse" items={result.tailored_questions} icon={<ArrowRight className="h-4 w-4" />} /></div><button onClick={()=>navigate("/app/interview")} className="mt-8 rounded-xl border border-border px-4 py-3 text-sm font-semibold hover:bg-muted">Start a tailored interview</button></div>}</section>
    </div>
  </main></div>;
}
function ReportList({ title, items, icon }: { title: string; items?: string[]; icon: React.ReactNode }) { return <div><h3 className="mb-3 flex items-center gap-2 font-semibold">{icon}{title}</h3><ul className="space-y-2 text-sm leading-6 text-muted-foreground">{(items || []).slice(0,5).map((item,i)=><li key={i} className="rounded-xl bg-muted/50 px-3 py-2">{item}</li>)}{!items?.length && <li className="text-muted-foreground">No items returned yet.</li>}</ul></div>; }
