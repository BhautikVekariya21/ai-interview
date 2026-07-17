import { useEffect, useMemo, useState } from "react";
import { m as motion } from "framer-motion";
import { ArrowLeft, ArrowUpRight, ExternalLink } from "lucide-react";
import Loading from "@/components/Loading";
import { fetchTechnologyNews, type NewsItem, type TechnologyNewsPayload } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

// Curated pool used when a story arrives without a usable image, so repeated
// fallbacks don't render as the same picture on every card. Served at HD.
const FALLBACK_IMAGES = [
  "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=85",
  "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1600&q=85",
  "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1600&q=85",
  "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=1600&q=85",
  "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=1600&q=85",
  "https://images.unsplash.com/photo-1517430816045-df4b7de11d1d?auto=format&fit=crop&w=1600&q=85",
  "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1600&q=85",
  "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1600&q=85",
  "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1600&q=85",
  "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1600&q=85",
];

function fallbackImageFor(story: NewsItem): string {
  const seed = story.link || story.title || "";
  let hash = 0;
  for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  return FALLBACK_IMAGES[hash % FALLBACK_IMAGES.length];
}

// Upgrade known CDN image URLs to higher-resolution variants so cards render
// crisp instead of using the small thumbnails many RSS feeds embed.
function enhanceImageUrl(url: string): string {
  try {
    const u = new URL(url);
    const host = u.hostname;
    if (host.includes("unsplash.com")) {
      u.searchParams.set("w", "1600");
      u.searchParams.set("q", "85");
      u.searchParams.set("auto", "format");
      return u.toString();
    }
    // WordPress / Jetpack Photon CDNs (i0/i1/i2.wp.com, *.files.wordpress.com)
    if (host.includes("wp.com") || host.includes("wordpress.com")) {
      u.searchParams.set("w", "1600");
      u.searchParams.set("quality", "85");
      return u.toString();
    }
    // Common feed patterns embed dimensions in the path or query — strip small
    // width hints so the origin serves the full-size asset.
    if (u.searchParams.has("width") && Number(u.searchParams.get("width")) < 1200) {
      u.searchParams.set("width", "1600");
      return u.toString();
    }
    if (u.searchParams.has("w") && Number(u.searchParams.get("w")) < 1200) {
      u.searchParams.set("w", "1600");
      return u.toString();
    }
    return url;
  } catch {
    return url;
  }
}

function StoryImage({ story, className }: { story: NewsItem; className?: string }) {
  const fallback = fallbackImageFor(story);
  const initial =
    story.image_url && !FALLBACK_IMAGES.includes(story.image_url)
      ? enhanceImageUrl(story.image_url)
      : fallback;
  const [src, setSrc] = useState(initial);

  useEffect(() => {
    setSrc(initial);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [story.link]);

  return (
    <img
      src={src}
      alt={story.title}
      loading="lazy"
      onError={() => {
        // On error, fall back first to the un-enhanced original, then to a
        // curated HD fallback so a broken upscale never leaves an empty card.
        if (story.image_url && src === enhanceImageUrl(story.image_url) && story.image_url !== src) {
          setSrc(story.image_url);
        } else if (src !== fallback) {
          setSrc(fallback);
        }
      }}
      className={className}
    />
  );
}

export default function NewsPage() {
  const [payload, setPayload] = useState<TechnologyNewsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedStory, setSelectedStory] = useState<NewsItem | null>(null);
  const [visibleStoryCount, setVisibleStoryCount] = useState(9);

  useEffect(() => {
    let alive = true;
    setLoading(true);

    fetchTechnologyNews("all", 30)
      .then((data) => {
        if (!alive) return;
        setPayload(data);
        setSelectedStory(null);
        setVisibleStoryCount(9);
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
  const gridStories = stories.slice(1, 1 + visibleStoryCount);
  const hasMoreStories = 1 + visibleStoryCount < stories.length;

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
              The latest technology headlines — AI, startups, product launches, and industry shifts — curated from
              trusted sources and refreshed throughout the day.
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
              {leadStory && <LeadStory story={leadStory} onOpen={() => setSelectedStory(leadStory)} />}

              <section className="border-t border-border/70 pt-10 lg:pt-12">
                <div className="mb-7 flex flex-wrap items-end justify-between gap-4 lg:mb-9">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-brand">Latest Stories</p>
                    <h2 className="mt-1.5 text-2xl font-bold tracking-tight sm:text-3xl">Top Headlines</h2>
                  </div>
                </div>

                <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 lg:gap-7">
                  {gridStories.map((story) => (
                    <StoryCard key={story.link} story={story} onOpen={() => setSelectedStory(story)} />
                  ))}
                </div>

                {hasMoreStories && (
                  <div className="mt-10 flex justify-center lg:mt-12">
                    <Button
                      variant="outline"
                      onClick={() => setVisibleStoryCount((count) => count + 9)}
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
      <Loading size="lg" label="Loading technology news..." />
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
    <article className="group overflow-hidden rounded-2xl border border-border bg-background/40 shadow-sm transition-shadow hover:shadow-lg md:rounded-3xl">
      <button onClick={onOpen} className="block w-full text-left">
        <div className="relative">
          <div className="aspect-[16/9] max-h-[520px] w-full overflow-hidden">
            <StoryImage
              story={story}
              className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.04]"
            />
          </div>
          {/* Gradient scrim so overlaid text stays legible over any image */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/35 to-transparent" />
          <div className="absolute inset-x-0 bottom-0 p-5 sm:p-7 lg:p-9">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-white/80">
              <span className="rounded-full bg-brand px-2.5 py-1 text-brand-foreground">Featured</span>
              <span>{story.source}</span>
              <span className="text-white/60">{story.published_label}</span>
            </div>
            <h2 className="mt-3 max-w-3xl text-2xl font-bold leading-[1.15] tracking-tight text-white sm:text-3xl lg:text-[2.5rem] lg:leading-[1.12]">
              {story.title}
            </h2>
            <p className="mt-3 hidden max-w-2xl text-[15px] leading-7 text-white/85 line-clamp-2 sm:block">
              {story.summary}
            </p>
            <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-white">
              Read full article <ArrowUpRight className="h-4 w-4" />
            </span>
          </div>
        </div>
      </button>
    </article>
  );
}

function StoryCard({ story, onOpen }: { story: NewsItem; onOpen: () => void }) {
  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-background/40 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
      <button onClick={onOpen} className="flex h-full w-full flex-col text-left">
        <div className="aspect-[16/10] w-full overflow-hidden">
          <StoryImage
            story={story}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.05]"
          />
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-3 p-5">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-brand">
            {story.source}
            <span className="ml-2 font-medium normal-case tracking-normal text-muted-foreground">
              {story.published_label}
            </span>
          </p>
          <h3 className="line-clamp-3 text-lg font-bold leading-snug tracking-tight sm:text-xl sm:leading-7">
            {story.title}
          </h3>
          <p className="line-clamp-3 text-sm leading-6 text-muted-foreground">{story.summary}</p>

          <div className="mt-auto flex items-center justify-between gap-3 border-t border-border/60 pt-3">
            <span className="truncate text-xs text-muted-foreground">
              {story.courtesy || `Courtesy: ${story.source}`}
            </span>
            <span className="inline-flex shrink-0 items-center gap-1 text-sm font-semibold text-foreground">
              Open <ArrowUpRight className="h-3.5 w-3.5" />
            </span>
          </div>
        </div>
      </button>
    </article>
  );
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
            <StoryImage
              story={story}
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
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-brand">Source</p>
            <p className="mt-3.5 text-sm leading-6 text-foreground/85">
              This summary is surfaced from {story.source}'s public feed. Read the complete original report — with
              full quotes and context — via the source link at the top of the page.
            </p>
          </div>
        </aside>
      </div>
    </article>
  );
}

function buildQuickTakeaways(story: NewsItem): string[] {
  return [
    `${story.source} reported this story ${story.published_label ? story.published_label.toLowerCase() : "recently"}.`,
    story.summary || story.title,
    `Filed under ${story.category || "technology"} — open the original source below for the full report.`,
  ];
}

function buildDetailedSections(story: NewsItem): Array<{ heading: string; paragraphs: string[] }> {
  return [
    {
      heading: "The Story",
      paragraphs: [
        story.summary || story.title,
        `This report comes from ${story.source}. The summary above reflects the publisher's own framing of the story; the complete article, with full quotes, data, and context, is available at the original source linked on this page.`,
      ],
    },
    {
      heading: "Why It Matters",
      paragraphs: [
        `Developments like this tend to ripple beyond a single announcement — they shape how companies hire, what skills interviewers probe for, and where engineering teams focus next.`,
        `If you're preparing for interviews, stories in the ${story.category || "technology"} space are useful conversation material: expect questions about how trends like this affect system design choices, team priorities, and product strategy.`,
      ],
    },
    {
      heading: "Keep Reading",
      paragraphs: [
        `Headlines rarely carry the full picture. For the complete report — including quotes, numbers, and background — open the original article on ${story.source} using the link at the top of this page.`,
        `Attribution: this story is surfaced from ${story.source}'s public feed. ${story.courtesy || `Courtesy: ${story.source}`}.`,
      ],
    },
  ];
}
