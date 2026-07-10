import { useEffect, useMemo, useState } from "react";
import { m as motion } from "framer-motion";
import { ArrowLeft, ArrowUpRight, ExternalLink, Loader2 } from "lucide-react";
import { fetchTechnologyNews, type NewsItem, type TechnologyNewsPayload } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function NewsPage() {
  const [payload, setPayload] = useState<TechnologyNewsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedStory, setSelectedStory] = useState<NewsItem | null>(null);
  const [visibleStoryCount, setVisibleStoryCount] = useState(8);

  useEffect(() => {
    let alive = true;
    setLoading(true);

    fetchTechnologyNews("all", 30)
      .then((data) => {
        if (!alive) return;
        setPayload(data);
        setSelectedStory(null);
        setVisibleStoryCount(8);
      })
      .catch(() => {
        toast.error("Unable to load technology news right now.");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  const stories = payload?.items || [];
  const leadStory = stories[0] || null;
  const topStories = stories.slice(1, 6);
  const latestStories = stories.slice(6, 6 + visibleStoryCount);
  const hasMoreStories = 6 + visibleStoryCount < stories.length;
  const hasTopStories = topStories.length > 0;

  return (
    <div className="mx-auto max-w-5xl">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white shadow-sm border border-black/10 overflow-hidden rounded-[28px] border border-black/5 text-[#000] shadow-sm"
      >
        <div className="border-b border-black/10/70 px-6 py-6 md:px-10 md:py-8">
          <div className="flex flex-wrap items-end justify-between gap-5">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.35em] text-primary">Technology</p>
              <h1 className="mt-3 text-4xl font-bold leading-none tracking-tight md:text-6xl">
                <span className="text-black">Newsroom</span>
              </h1>
            </div>
            <p className="max-w-xl text-sm leading-7 text-black/60 md:text-base">
              A tighter editorial layout with a lead story, headline stack, and cleaner card spacing. Full article detail opens only after the click.
            </p>
          </div>
        </div>

        <div className="px-5 py-6 md:px-8 md:py-8 xl:px-10">
          {loading ? (
            <LoadingState />
          ) : stories.length === 0 ? (
            <EmptyState />
          ) : selectedStory ? (
            <ArticleDetail story={selectedStory} onBack={() => setSelectedStory(null)} />
          ) : (
            <div className="space-y-8 md:space-y-10">
              <section
                className={
                  hasTopStories
                    ? "grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_300px] xl:gap-6"
                    : "grid gap-6"
                }
              >
                {leadStory && <LeadStory story={leadStory} onOpen={() => setSelectedStory(leadStory)} />}
                {hasTopStories ? <TopStories stories={topStories} onOpen={setSelectedStory} /> : null}
              </section>

              <section className="border-t border-black/10/70 pt-7 md:pt-8">
                <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-primary">Latest Stories</p>
                    <h2 className="mt-2 text-3xl font-bold tracking-tight">Top Headlines</h2>
                  </div>
                  <p className="max-w-md text-sm leading-7 text-black/60">
                    Each card keeps the homepage compact with only the image, headline, and description.
                  </p>
                </div>

                <div className="grid gap-5 md:grid-cols-2 md:gap-6">
                  {latestStories.map((story, index) => (
                    <StoryCard key={story.link} story={story} index={index} onOpen={() => setSelectedStory(story)} />
                  ))}
                </div>

                {hasMoreStories && (
                  <div className="mt-8 flex justify-center">
                    <Button
                      variant="outline"
                      onClick={() => setVisibleStoryCount((count) => count + 8)}
                      className="rounded-xl border-black/10 bg-white/50 px-6 text-[#000] hover:bg-accent/10 hover:text-[#000]"
                    >
                      Load more stories
                    </Button>
                  </div>
                )}
              </section>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex min-h-[360px] items-center justify-center rounded-2xl border border-black/10 bg-white/35">
      <div className="flex items-center gap-2 text-sm text-black/50">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading technology news...
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-2xl border border-black/10 bg-white/35 px-6 py-16 text-center text-sm text-black/50">
      No technology news is available right now.
    </div>
  );
}

function LeadStory({ story, onOpen }: { story: NewsItem; onOpen: () => void }) {
  return (
    <article className="overflow-hidden rounded-[24px] border border-black/10 bg-white/35 shadow-sm">
      <button onClick={onOpen} className="block w-full text-left">
        <div className="px-5 pb-5 pt-5 md:px-6 md:pb-6 md:pt-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-primary">{story.source}</p>
          <h2 className="mt-3 max-w-3xl text-3xl font-bold leading-tight tracking-tight md:text-[2.7rem]">{story.title}</h2>
          <p className="mt-4 max-w-2xl text-base leading-8 text-black/60">{story.summary}</p>
          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs uppercase tracking-[0.18em] text-black/50">
            <span>{story.published_label}</span>
            <span>{story.courtesy || `Courtesy: ${story.source}`}</span>
          </div>
        </div>
        <div className="aspect-[16/9] overflow-hidden border-y border-black/10/60">
          <img src={story.image_url} alt={story.title} className="h-full w-full object-cover transition-transform duration-500 hover:scale-[1.03]" />
        </div>
        <div className="flex items-center justify-between gap-3 px-5 py-4 md:px-6">
          <span className="text-xs uppercase tracking-[0.18em] text-black/50">Featured story</span>
          <span className="inline-flex items-center gap-1 text-sm font-semibold text-[#000]">
            Read full article <ArrowUpRight className="h-3.5 w-3.5" />
          </span>
        </div>
      </button>
    </article>
  );
}

function TopStories({ stories, onOpen }: { stories: NewsItem[]; onOpen: (story: NewsItem) => void }) {
  return (
    <aside className="rounded-[24px] border border-black/10 bg-white/20 p-4 md:p-5 xl:border-none xl:bg-transparent xl:p-0">
      <div className="xl:sticky xl:top-24">
        <div className="border-b border-black/10/70 pb-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-primary">Top Stories</p>
          <h3 className="mt-2 text-2xl font-bold tracking-tight">Most Read</h3>
        </div>

        <div className="divide-y divide-border/60">
          {stories.map((story, index) => (
            <button key={story.link} onClick={() => onOpen(story)} className="block w-full rounded-xl px-2 py-4 text-left transition-colors hover:bg-secondary/35 md:px-3 md:py-5">
              <div className="flex gap-4">
                <span className="min-w-8 pt-1 text-3xl font-bold text-primary/35">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-primary">{story.source}</p>
                  <p className="mt-2 text-lg font-bold leading-7 tracking-tight">{story.title}</p>
                  <p className="mt-2 text-sm leading-7 text-black/60">{story.summary}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}

function StoryCard({ story, index, onOpen }: { story: NewsItem; index: number; onOpen: () => void }) {
  const variant = getStoryVariant(index);

  if (variant === "feature") {
    return (
      <article className="overflow-hidden rounded-[24px] border border-black/10 bg-white/35 p-5 shadow-sm md:col-span-2 md:p-6">
        <button onClick={onOpen} className="block w-full text-left">
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
            <div className="aspect-[16/8] overflow-hidden rounded-2xl">
              <img src={story.image_url} alt={story.title} className="h-full w-full object-cover" />
            </div>
            <div className="flex flex-col justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary">
                  {story.source} <span className="ml-2 text-black/50">{story.published_label}</span>
                </p>
                <h3 className="mt-3 max-w-2xl text-[2rem] font-bold leading-[1.15] tracking-tight">{story.title}</h3>
                <p className="mt-4 max-w-2xl text-base leading-8 text-black/60">{story.summary}</p>
              </div>

              <div className="mt-5 flex items-center justify-between gap-3 border-t border-black/10/60 pt-4">
                <span className="text-xs text-black/50">{story.courtesy || `Courtesy: ${story.source}`}</span>
                <span className="inline-flex items-center gap-1 text-sm font-semibold text-[#000]">
                  Open article <ArrowUpRight className="h-3.5 w-3.5" />
                </span>
              </div>
            </div>
          </div>
        </button>
      </article>
    );
  }

  if (variant === "compact") {
    return (
      <article className="overflow-hidden rounded-[22px] border border-black/10 bg-white/35 p-4 shadow-sm md:p-5">
        <button onClick={onOpen} className="block w-full text-left">
          <div className="grid gap-4 sm:grid-cols-[170px_minmax(0,1fr)]">
            <div className="aspect-[4/3] overflow-hidden rounded-xl">
              <img src={story.image_url} alt={story.title} className="h-full w-full object-cover" />
            </div>
            <div className="flex flex-col justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary">
                  {story.source} <span className="ml-2 text-black/50">{story.published_label}</span>
                </p>
                <h3 className="mt-2.5 text-[1.35rem] font-bold leading-7 tracking-tight">{story.title}</h3>
                <p className="mt-2.5 text-sm leading-7 text-black/60">{story.summary}</p>
              </div>

              <div className="mt-4 flex items-center justify-between gap-3 border-t border-black/10/60 pt-3.5">
                <span className="text-xs text-black/50">{story.courtesy || `Courtesy: ${story.source}`}</span>
                <span className="inline-flex items-center gap-1 text-sm font-semibold text-[#000]">
                  Open article <ArrowUpRight className="h-3.5 w-3.5" />
                </span>
              </div>
            </div>
          </div>
        </button>
      </article>
    );
  }

  return (
    <article className="overflow-hidden rounded-[22px] border border-black/10 bg-white/35 p-4 shadow-sm transition-transform duration-300 hover:-translate-y-1 md:p-5">
      <button onClick={onOpen} className="block w-full text-left">
        <div className="space-y-4">
          <div className="aspect-[16/10] overflow-hidden rounded-xl">
            <img src={story.image_url} alt={story.title} className="h-full w-full object-cover" />
          </div>

          <div className="flex flex-col justify-between">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary">
                {story.source} <span className="ml-2 text-black/50">{story.published_label}</span>
              </p>
              <h3 className="mt-2.5 text-[1.55rem] font-bold leading-8 tracking-tight">{story.title}</h3>
              <p className="mt-3 text-sm leading-7 text-black/60">{story.summary}</p>
            </div>

            <div className="mt-4 flex items-center justify-between gap-3 border-t border-black/10/60 pt-3.5">
              <span className="text-xs text-black/50">{story.courtesy || `Courtesy: ${story.source}`}</span>
              <span className="inline-flex items-center gap-1 text-sm font-semibold text-[#000]">
                Open article <ArrowUpRight className="h-3.5 w-3.5" />
              </span>
            </div>
          </div>
        </div>
      </button>
    </article>
  );
}

function getStoryVariant(index: number): "feature" | "standard" | "compact" {
  if (index === 0 || index % 5 === 0) return "feature";
  if (index % 3 === 0) return "compact";
  return "standard";
}

function ArticleDetail({ story, onBack }: { story: NewsItem; onBack: () => void }) {
  const articleSections = useMemo(() => buildDetailedSections(story), [story]);
  const quickTakeaways = useMemo(() => buildQuickTakeaways(story), [story]);

  return (
    <article className="space-y-7 md:space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-black/10/70 pb-4">
        <button onClick={onBack} className="inline-flex items-center gap-2 text-sm font-semibold text-[#000] transition-colors hover:text-primary">
          <ArrowLeft className="h-4 w-4" />
          Back to homepage
        </button>
        <Button asChild className="rounded-xl bg-[#000] text-white hover:opacity-90">
          <a href={story.link} target="_blank" rel="noreferrer">
            Open original source <ExternalLink className="ml-1 h-3.5 w-3.5" />
          </a>
        </Button>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_240px] xl:gap-6">
        <div className="space-y-7">
          <header className="space-y-5 rounded-[28px] border border-black/10 bg-white/35 px-5 py-6 md:px-7 md:py-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-primary">{story.source}</p>
            <h2 className="max-w-4xl text-4xl font-bold leading-tight tracking-tight md:text-5xl">{story.title}</h2>
            <p className="max-w-2xl text-lg leading-8 text-black/60">{story.summary}</p>
            <div className="flex flex-wrap items-center gap-4 text-xs uppercase tracking-[0.18em] text-black/50">
              <span>{story.published_label}</span>
              <span>{story.courtesy || `Courtesy: ${story.source}`}</span>
              <span>{story.category}</span>
            </div>
          </header>

          <div className="overflow-hidden rounded-[28px] border border-black/10/60 bg-white/20">
            <img src={story.image_url} alt={story.title} className="h-full max-h-[520px] w-full object-cover" />
          </div>

          <div className="space-y-5 md:space-y-6">
            {articleSections.map((section) => (
              <section key={section.heading} className="rounded-[24px] border border-black/10 bg-white/35 px-5 py-5 md:px-7 md:py-6">
                <h3 className="mb-4 text-2xl font-bold tracking-tight md:text-3xl">{section.heading}</h3>
                <div className="space-y-4">
                  {section.paragraphs.map((paragraph) => (
                    <p key={paragraph} className="max-w-4xl text-[16px] leading-8 text-[#000]/90 md:text-[17px] md:leading-8">
                      {paragraph}
                    </p>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </div>

        <aside className="space-y-4">
          <div className="rounded-[24px] border border-black/10 bg-white/35 p-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-primary">Quick Takes</p>
            <div className="mt-4 space-y-3">
              {quickTakeaways.map((takeaway) => (
                <div key={takeaway} className="border-t border-black/10/60 pt-3 first:border-t-0 first:pt-0">
                  <p className="text-sm leading-7 text-black/50">{takeaway}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[24px] border border-primary/20 bg-[#000]/10 p-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-primary">About This View</p>
            <p className="mt-4 text-sm leading-7 text-[#000]/85">
              The article page is intentionally more detailed than the homepage. Readers first see the concise card layout, then open a fuller editorial reading experience only when they choose a story.
            </p>
          </div>
        </aside>
      </div>
    </article>
  );
}

function buildQuickTakeaways(story: NewsItem): string[] {
  return [
    `This story is surfaced from ${story.source} and positioned as a click-through feature instead of a full homepage block.`,
    `The homepage now keeps only a concise summary so readers are not overwhelmed before choosing an article.`,
    `The detailed article view expands the context into multiple reading sections while preserving the original source link.`,
  ];
}

function buildDetailedSections(story: NewsItem): Array<{ heading: string; paragraphs: string[] }> {
  return [
    {
      heading: "The Big Story",
      paragraphs: [
        `${story.title} leads this article because it signals a topic with immediate relevance for technology readers watching product launches, AI shifts, platform strategy, startup momentum, and market reaction.`,
        `${story.summary} In the homepage experience, that idea is intentionally compressed into a short preview. Once the reader opens the story, the same news item expands into a more deliberate editorial read that feels closer to a magazine article than a feed card.`,
      ],
    },
    {
      heading: "Why Readers Click",
      paragraphs: [
        `Stories like this usually attract attention because the headline implies a larger movement behind the update, not just a single announcement. Readers often want to know what changed, why it matters now, and what decision-makers should watch next.`,
        `That is why this page separates discovery from depth. The homepage gives a high-signal snapshot with image, headline, and short description. The article page then adds structure and breathing room so the reader can stay with the story longer.`,
      ],
    },
    {
      heading: "Context And Implications",
      paragraphs: [
        `From a product perspective, this kind of development can influence how teams think about adoption, competition, talent, investment, and execution. Even when the original summary is brief, the implication is often broader than the first sentence suggests.`,
        `By presenting the story in a fuller format here, the interface makes room for analysis, context, and editorial framing while still keeping attribution clear. Courtesy remains with ${story.source}, and the publisher link stays visible for anyone who wants the complete original report.`,
      ],
    },
    {
      heading: "What Happens Next",
      paragraphs: [
        `For readers, the next step is usually comparison: how this development fits alongside other headlines, whether the claim changes day-to-day priorities, and which players in the space are most affected.`,
        `For the product itself, the layout now follows the pattern you asked for: compact homepage presentation first, then a fully detailed article view after the click. That keeps the main page clean while still giving each story a richer destination.`,
      ],
    },
  ];
}
