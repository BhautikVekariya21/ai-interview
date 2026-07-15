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
    <div className="mx-auto w-full max-w-[1180px]">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="overflow-hidden rounded-2xl border border-border bg-card text-foreground shadow-sm md:rounded-3xl"
      >
        {/* Header */}
        <div className="border-b border-border/70 px-5 py-7 sm:px-8 sm:py-9 lg:px-12 lg:py-11">
          <div className="flex flex-wrap items-end justify-between gap-5 lg:gap-8">
            <div className="min-w-0">
              <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-brand">Technology</p>
              <h1 className="mt-2.5 text-[2.35rem] font-bold leading-[1.05] tracking-tight sm:text-5xl lg:text-[3.5rem]">
                Newsroom
              </h1>
            </div>
            <p className="max-w-sm text-sm leading-relaxed text-muted-foreground sm:text-[15px] sm:leading-7">
              A lead story, a most-read stack, and clean editorial cards. Full article detail opens on click.
            </p>
          </div>
        </div>

        {/* Body */}
        <div className="px-5 py-7 sm:px-8 sm:py-9 lg:px-12 lg:py-11">
          {loading ? (
            <LoadingState />
          ) : stories.length === 0 ? (
            <EmptyState />
          ) : selectedStory ? (
            <ArticleDetail story={selectedStory} onBack={() => setSelectedStory(null)} />
          ) : (
            <div className="space-y-12 lg:space-y-14">
              <section
                className={
                  hasTopStories
                    ? "grid items-start gap-8 lg:grid-cols-[minmax(0,1.55fr)_minmax(260px,0.9fr)] lg:gap-10 xl:gap-12"
                    : "grid gap-8"
                }
              >
                {leadStory && <LeadStory story={leadStory} onOpen={() => setSelectedStory(leadStory)} />}
                {hasTopStories ? <TopStories stories={topStories} onOpen={setSelectedStory} /> : null}
              </section>

              <section className="border-t border-border/70 pt-10 lg:pt-12">
                <div className="mb-7 flex flex-wrap items-end justify-between gap-4 lg:mb-9">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-brand">Latest Stories</p>
                    <h2 className="mt-1.5 text-2xl font-bold tracking-tight sm:text-3xl">Top Headlines</h2>
                  </div>
                </div>

                <div className="grid gap-5 sm:gap-6 md:grid-cols-2 lg:gap-7">
                  {latestStories.map((story, index) => (
                    <StoryCard key={story.link} story={story} index={index} onOpen={() => setSelectedStory(story)} />
                  ))}
                </div>

                {hasMoreStories && (
                  <div className="mt-10 flex justify-center lg:mt-12">
                    <Button
                      variant="outline"
                      onClick={() => setVisibleStoryCount((count) => count + 8)}
                      className="h-11 rounded-xl border-border bg-card px-7 text-foreground hover:bg-accent/10 hover:text-foreground"
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
    <div className="flex min-h-[420px] items-center justify-center rounded-2xl border border-border/60 bg-muted/20">
      <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading technology news...
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-2xl border border-border/60 bg-muted/20 px-6 py-20 text-center text-sm text-muted-foreground">
      No technology news is available right now.
    </div>
  );
}

function LeadStory({ story, onOpen }: { story: NewsItem; onOpen: () => void }) {
  return (
    <article className="group overflow-hidden rounded-2xl border border-border bg-background/40 shadow-sm transition-shadow hover:shadow-md">
      <button onClick={onOpen} className="block w-full text-left">
        <div className="px-5 pb-4 pt-5 sm:px-6 sm:pb-5 sm:pt-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-brand">{story.source}</p>
          <h2 className="mt-2.5 max-w-3xl text-[1.65rem] font-bold leading-[1.2] tracking-tight sm:text-3xl lg:text-[2.15rem] lg:leading-[1.18]">
            {story.title}
          </h2>
          <p className="mt-3 max-w-2xl text-[15px] leading-7 text-muted-foreground sm:text-base sm:leading-8">
            {story.summary}
          </p>
          <div className="mt-3.5 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
            <span>{story.published_label}</span>
            <span>{story.courtesy || `Courtesy: ${story.source}`}</span>
          </div>
        </div>
        <div className="aspect-[16/9] max-h-[380px] overflow-hidden border-y border-border/60 sm:max-h-[420px]">
          <img
            src={story.image_url}
            alt={story.title}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
          />
        </div>
        <div className="flex items-center justify-between gap-3 px-5 py-3.5 sm:px-6 sm:py-4">
          <span className="text-[11px] uppercase tracking-[0.16em] text-muted-foreground">Featured story</span>
          <span className="inline-flex items-center gap-1 text-sm font-semibold text-foreground">
            Read full article <ArrowUpRight className="h-3.5 w-3.5" />
          </span>
        </div>
      </button>
    </article>
  );
}

function TopStories({ stories, onOpen }: { stories: NewsItem[]; onOpen: (story: NewsItem) => void }) {
  return (
    <aside className="rounded-2xl border border-border bg-background/40 p-4 sm:p-5 lg:border-none lg:bg-transparent lg:p-0">
      <div className="lg:sticky lg:top-24">
        <div className="border-b border-border/70 pb-3.5">
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-brand">Top Stories</p>
          <h3 className="mt-1.5 text-xl font-bold tracking-tight sm:text-2xl">Most Read</h3>
        </div>

        <div className="divide-y divide-border/60">
          {stories.map((story, index) => (
            <button
              key={story.link}
              onClick={() => onOpen(story)}
              className="block w-full rounded-xl px-1.5 py-3.5 text-left transition-colors hover:bg-secondary/40 sm:px-2 sm:py-4"
            >
              <div className="flex gap-3.5">
                <span className="min-w-7 pt-0.5 text-2xl font-bold tabular-nums text-brand/30 sm:min-w-8 sm:text-[1.75rem]">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div className="min-w-0">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-brand">{story.source}</p>
                  <p className="mt-1.5 line-clamp-2 text-[15px] font-bold leading-snug tracking-tight sm:text-base sm:leading-6">
                    {story.title}
                  </p>
                  <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-muted-foreground">{story.summary}</p>
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
      <article className="overflow-hidden rounded-2xl border border-border bg-background/40 p-4 shadow-sm transition-shadow hover:shadow-md sm:p-5 md:col-span-2 md:p-6">
        <button onClick={onOpen} className="block w-full text-left">
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1.15fr)_minmax(260px,0.85fr)] lg:gap-7">
            <div className="aspect-[16/10] min-h-[200px] overflow-hidden rounded-xl sm:min-h-[240px] lg:aspect-auto lg:min-h-[280px] lg:max-h-[320px]">
              <img src={story.image_url} alt={story.title} className="h-full w-full object-cover" />
            </div>
            <div className="flex min-h-0 flex-col justify-between gap-4">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-brand">
                  {story.source}{" "}
                  <span className="ml-2 font-medium normal-case tracking-normal text-muted-foreground">
                    {story.published_label}
                  </span>
                </p>
                <h3 className="mt-2.5 max-w-2xl text-xl font-bold leading-snug tracking-tight sm:text-2xl lg:text-[1.85rem] lg:leading-[1.2]">
                  {story.title}
                </h3>
                <p className="mt-3 max-w-2xl text-[15px] leading-7 text-muted-foreground">{story.summary}</p>
              </div>

              <div className="flex items-center justify-between gap-3 border-t border-border/60 pt-3.5">
                <span className="truncate text-xs text-muted-foreground">
                  {story.courtesy || `Courtesy: ${story.source}`}
                </span>
                <span className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-foreground">
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
      <article className="h-full overflow-hidden rounded-2xl border border-border bg-background/40 p-4 shadow-sm transition-shadow hover:shadow-md sm:p-5">
        <button onClick={onOpen} className="block h-full w-full text-left">
          <div className="grid h-full gap-4 sm:grid-cols-[150px_minmax(0,1fr)] sm:gap-5">
            <div className="aspect-[16/10] overflow-hidden rounded-xl sm:aspect-auto sm:min-h-[130px] sm:max-h-[180px]">
              <img src={story.image_url} alt={story.title} className="h-full w-full object-cover" />
            </div>
            <div className="flex min-w-0 flex-col justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-brand">
                  {story.source}{" "}
                  <span className="ml-2 font-medium normal-case tracking-normal text-muted-foreground">
                    {story.published_label}
                  </span>
                </p>
                <h3 className="mt-2 line-clamp-2 text-lg font-bold leading-snug tracking-tight">{story.title}</h3>
                <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">{story.summary}</p>
              </div>

              <div className="flex items-center justify-between gap-3 border-t border-border/60 pt-3">
                <span className="truncate text-xs text-muted-foreground">
                  {story.courtesy || `Courtesy: ${story.source}`}
                </span>
                <span className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-foreground">
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
    <article className="h-full overflow-hidden rounded-2xl border border-border bg-background/40 p-4 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md sm:p-5">
      <button onClick={onOpen} className="flex h-full w-full flex-col text-left">
        <div className="flex h-full flex-col gap-4">
          <div className="aspect-[16/10] max-h-[220px] overflow-hidden rounded-xl">
            <img src={story.image_url} alt={story.title} className="h-full w-full object-cover" />
          </div>

          <div className="flex min-h-0 flex-1 flex-col justify-between gap-3">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-brand">
                {story.source}{" "}
                <span className="ml-2 font-medium normal-case tracking-normal text-muted-foreground">
                  {story.published_label}
                </span>
              </p>
              <h3 className="mt-2 line-clamp-3 text-lg font-bold leading-snug tracking-tight sm:text-xl sm:leading-7">
                {story.title}
              </h3>
              <p className="mt-2.5 line-clamp-3 text-sm leading-6 text-muted-foreground">{story.summary}</p>
            </div>

            <div className="flex items-center justify-between gap-3 border-t border-border/60 pt-3">
              <span className="truncate text-xs text-muted-foreground">
                {story.courtesy || `Courtesy: ${story.source}`}
              </span>
              <span className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-foreground">
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
    <article className="space-y-8 lg:space-y-10">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-4">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-sm font-semibold text-foreground transition-colors hover:text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to homepage
        </button>
        <Button asChild className="h-10 rounded-xl bg-brand px-4 text-brand-foreground hover:opacity-90">
          <a href={story.link} target="_blank" rel="noreferrer">
            Open original source <ExternalLink className="ml-1 h-3.5 w-3.5" />
          </a>
        </Button>
      </div>

      <div className="grid gap-7 xl:grid-cols-[minmax(0,1fr)_minmax(220px,260px)] xl:gap-10">
        <div className="min-w-0 space-y-6 lg:space-y-7">
          <header className="space-y-4 rounded-2xl border border-border bg-background/40 px-5 py-6 sm:px-7 sm:py-8 lg:px-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-brand">{story.source}</p>
            <h2 className="max-w-3xl text-3xl font-bold leading-[1.15] tracking-tight sm:text-4xl lg:text-[2.75rem]">
              {story.title}
            </h2>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg sm:leading-8">
              {story.summary}
            </p>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">
              <span>{story.published_label}</span>
              <span>{story.courtesy || `Courtesy: ${story.source}`}</span>
              <span>{story.category}</span>
            </div>
          </header>

          <div className="overflow-hidden rounded-2xl border border-border/60 bg-background/40">
            <img
              src={story.image_url}
              alt={story.title}
              className="h-auto max-h-[480px] w-full object-cover"
            />
          </div>

          <div className="space-y-5">
            {articleSections.map((section) => (
              <section
                key={section.heading}
                className="rounded-2xl border border-border bg-background/40 px-5 py-5 sm:px-7 sm:py-6"
              >
                <h3 className="mb-3.5 text-xl font-bold tracking-tight sm:text-2xl">{section.heading}</h3>
                <div className="space-y-3.5">
                  {section.paragraphs.map((paragraph) => (
                    <p
                      key={paragraph}
                      className="max-w-3xl text-[15px] leading-7 text-foreground/90 sm:text-base sm:leading-8"
                    >
                      {paragraph}
                    </p>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </div>

        <aside className="space-y-4 xl:sticky xl:top-24 xl:self-start">
          <div className="rounded-2xl border border-border bg-background/40 p-5 sm:p-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-brand">Quick Takes</p>
            <div className="mt-3.5 space-y-3">
              {quickTakeaways.map((takeaway) => (
                <div key={takeaway} className="border-t border-border/60 pt-3 first:border-t-0 first:pt-0">
                  <p className="text-sm leading-6 text-muted-foreground">{takeaway}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-primary/20 bg-brand/10 p-5 sm:p-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-brand">About This View</p>
            <p className="mt-3.5 text-sm leading-6 text-foreground/85">
              The article page is intentionally more detailed than the homepage. Readers first see the concise card
              layout, then open a fuller editorial reading experience only when they choose a story.
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
