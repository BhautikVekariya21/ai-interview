import { useEffect, useMemo, useState } from "react";
import { m as motion } from "framer-motion";
import { BookOpenText, ChevronDown, ExternalLink, Loader2, Sparkles } from "lucide-react";
import { fetchFAQTechnologies, fetchTechnologyFAQ, type FAQItem, type FAQPayload, type FAQTechnology } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function FAQPage() {
  const [technologies, setTechnologies] = useState<FAQTechnology[]>([]);
  const [selectedTech, setSelectedTech] = useState<string>("");
  const [faqData, setFaqData] = useState<FAQPayload | null>(null);
  const [loadingTechs, setLoadingTechs] = useState(true);
  const [loadingFaq, setLoadingFaq] = useState(false);
  const [openQuestionId, setOpenQuestionId] = useState<number | null>(null);

  useEffect(() => {
    let alive = true;
    setLoadingTechs(true);
    fetchFAQTechnologies()
      .then((items) => {
        if (!alive) return;
        setTechnologies(items);
        setSelectedTech(items[0]?.id || "");
      })
      .catch(() => {
        toast.error("Unable to load FAQ technologies right now.");
      })
      .finally(() => {
        if (alive) setLoadingTechs(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedTech) return;
    let alive = true;
    setLoadingFaq(true);
    fetchTechnologyFAQ(selectedTech)
      .then((payload) => {
        if (!alive) return;
        setFaqData(payload);
        setOpenQuestionId(payload.items[0]?.question_id ?? null);
      })
      .catch(() => {
        toast.error("Unable to load this technology FAQ right now.");
      })
      .finally(() => {
        if (alive) setLoadingFaq(false);
      });
    return () => {
      alive = false;
    };
  }, [selectedTech]);

  const currentDescription = useMemo(
    () => technologies.find((item) => item.id === selectedTech)?.description || "Browse common developer questions and answers.",
    [technologies, selectedTech],
  );

  return (
    <div className="max-w-6xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 text-center"
      >
        <span className="inline-flex items-center gap-2 rounded-xl border border-primary/20 bg-[#000]/10 px-3.5 py-1.5 text-xs font-semibold text-primary">
          <Sparkles className="h-3.5 w-3.5" /> Developer Knowledge Library
        </span>
        <h1 className="mt-4 text-4xl font-extrabold tracking-tight md:text-5xl">
          Technology <span className="text-black">FAQ</span>
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-base leading-relaxed text-black/60">
          Pick a technology and explore high-signal, frequently asked questions with real answers pulled through a public developer API.
        </p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        <section className="bg-white shadow-sm border border-black/10 rounded-2xl border border-black/5 p-5">
          <div className="mb-4 flex items-center gap-2">
            <BookOpenText className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold">Choose Technology</h2>
          </div>

          {loadingTechs ? (
            <div className="flex items-center gap-2 text-sm text-black/50">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading technologies...
            </div>
          ) : (
            <div className="space-y-2">
              {technologies.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setSelectedTech(item.id)}
                  className={`w-full rounded-xl border px-3.5 py-3 text-left transition-all duration-200 ${
                    selectedTech === item.id
                      ? "border-primary/35 bg-[#000]/12 text-[#000] shadow-[0_8px_24px_hsla(270,70%,60%,0.15)]"
                      : "border-black/10 bg-white/35 text-black/60 hover:border-primary/20 hover:bg-accent/10 hover:text-[#000]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium">{item.label}</span>
                    <span className="rounded-xl border border-black/10 bg-white/40 px-2 py-0.5 text-[10px] uppercase tracking-[0.2em] text-black/50">
                      {item.tag}
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs leading-relaxed text-black/50">{item.description}</p>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="bg-white shadow-sm border border-black/10 rounded-2xl border border-black/5 p-5 md:p-6">
          <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-primary">FAQ Feed</p>
              <h2 className="mt-1 text-2xl font-bold tracking-tight">
                {faqData?.technology.label || "Technology Answers"}
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-black/60">
                {faqData?.technology.description || currentDescription}
              </p>
            </div>
            {faqData?.source?.docs ? (
              <Button asChild variant="outline" size="sm" className="bg-white/50">
                <a href={faqData.source.docs} target="_blank" rel="noreferrer">
                  API Source <ExternalLink className="ml-1 h-3.5 w-3.5" />
                </a>
              </Button>
            ) : null}
          </div>

          {loadingFaq ? (
            <div className="flex min-h-[240px] items-center justify-center rounded-2xl border border-black/10 bg-white/35">
              <div className="flex items-center gap-2 text-sm text-black/50">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading FAQ answers...
              </div>
            </div>
          ) : faqData?.items?.length ? (
            <div className="space-y-3">
              {faqData.items.map((item) => {
                const isOpen = openQuestionId === item.question_id;
                return (
                  <motion.div
                    key={item.question_id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="overflow-hidden rounded-2xl border border-black/10 bg-white/35"
                  >
                    <button
                      onClick={() => setOpenQuestionId(isOpen ? null : item.question_id)}
                      className="flex w-full items-start justify-between gap-4 px-4 py-4 text-left transition-colors hover:bg-accent/10"
                    >
                      <div className="min-w-0">
                        <div className="mb-2 flex flex-wrap gap-2">
                          <span className="rounded-xl border border-primary/20 bg-[#000]/10 px-2.5 py-1 text-[11px] font-semibold text-primary">
                            Score {item.score}
                          </span>
                          <span className="rounded-xl border border-black/10 bg-white/40 px-2.5 py-1 text-[11px] text-black/50">
                            {item.answer_count} answers
                          </span>
                        </div>
                        <h3 className="text-sm font-semibold leading-6 text-[#000]">{item.question}</h3>
                        <p className="mt-2 text-xs leading-relaxed text-black/50">{item.answer.preview}</p>
                      </div>
                      <ChevronDown className={`mt-1 h-4 w-4 flex-shrink-0 text-black/50 transition-transform ${isOpen ? "rotate-180" : ""}`} />
                    </button>

                    {isOpen ? (
                      <div className="border-t border-black/10 px-4 py-4">
                        <div className="mb-3 flex flex-wrap gap-2">
                          {item.tags.slice(0, 4).map((tag) => (
                            <span key={tag} className="rounded-xl border border-black/10 bg-[#F9F9F9] px-2.5 py-1 text-[11px] text-black/50">
                              {tag}
                            </span>
                          ))}
                        </div>
                        <div className="whitespace-pre-wrap text-sm leading-7 text-black/60">
                          {item.answer.body_text || "No answer body was returned for this question yet."}
                        </div>
                        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                          <div className="text-xs text-black/50">
                            Answer score: <span className="font-semibold text-[#000]">{item.answer.score}</span>
                            {item.answer.is_accepted ? " • Accepted answer" : ""}
                          </div>
                          <Button asChild variant="outline" size="sm" className="bg-white/50">
                            <a href={item.link} target="_blank" rel="noreferrer">
                              Open on Stack Overflow <ExternalLink className="ml-1 h-3.5 w-3.5" />
                            </a>
                          </Button>
                        </div>
                      </div>
                    ) : null}
                  </motion.div>
                );
              })}
            </div>
          ) : (
            <div className="rounded-2xl border border-black/10 bg-white/35 px-4 py-8 text-center text-sm text-black/50">
              No FAQ items are available for this technology right now.
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
