import { useEffect } from "react";

const SITE_NAME = "interviewer.ai";
const SITE_URL = "https://interviewer.ai";
const DEFAULT_IMAGE = `${SITE_URL}/hero-illustration.png`;
const DEFAULT_DESCRIPTION =
  "Practice technical interviews with an AI that adapts to your resume, speaks in real-time, evaluates your code, and gives actionable feedback.";

export type SeoProps = {
  title: string;
  description?: string;
  /** Path only (e.g. "/features"); combined with the canonical origin. */
  path?: string;
  image?: string;
  /** Set true on gated/app pages you don't want indexed. */
  noindex?: boolean;
  /** Optional JSON-LD structured data object. */
  jsonLd?: Record<string, unknown>;
};

/** Upsert a <meta> tag keyed by name or property. */
function setMeta(attr: "name" | "property", key: string, content: string) {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}

function setLink(rel: string, href: string) {
  let el = document.head.querySelector<HTMLLinkElement>(`link[rel="${rel}"]`);
  if (!el) {
    el = document.createElement("link");
    el.setAttribute("rel", rel);
    document.head.appendChild(el);
  }
  el.setAttribute("href", href);
}

/**
 * Per-route SEO — sets document title, meta description, canonical, Open Graph,
 * Twitter card, robots directive, and optional JSON-LD. Client-side only; the
 * static tags in index.html remain the crawl fallback for the root document.
 */
export default function Seo({
  title,
  description = DEFAULT_DESCRIPTION,
  path = "/",
  image = DEFAULT_IMAGE,
  noindex = false,
  jsonLd,
}: SeoProps) {
  const fullTitle = title.includes(SITE_NAME) ? title : `${title} — ${SITE_NAME}`;
  const url = `${SITE_URL}${path}`;
  // Serialize once and depend on the string, so a fresh object literal passed
  // on every render doesn't thrash the effect (remove/re-append <script>).
  const jsonLdText = jsonLd ? JSON.stringify(jsonLd) : null;

  useEffect(() => {
    document.title = fullTitle;

    setMeta("name", "description", description);
    setMeta(
      "name",
      "robots",
      noindex
        ? "noindex,nofollow"
        : "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1",
    );
    setLink("canonical", url);

    setMeta("property", "og:site_name", SITE_NAME);
    setMeta("property", "og:type", "website");
    setMeta("property", "og:url", url);
    setMeta("property", "og:title", fullTitle);
    setMeta("property", "og:description", description);
    setMeta("property", "og:image", image);

    setMeta("name", "twitter:card", "summary_large_image");
    setMeta("name", "twitter:title", fullTitle);
    setMeta("name", "twitter:description", description);
    setMeta("name", "twitter:image", image);

    const ldId = "seo-jsonld";
    document.getElementById(ldId)?.remove();
    if (jsonLdText) {
      const script = document.createElement("script");
      script.type = "application/ld+json";
      script.id = ldId;
      script.text = jsonLdText;
      document.head.appendChild(script);
    }

    return () => {
      document.getElementById(ldId)?.remove();
    };
  }, [fullTitle, description, url, image, noindex, jsonLdText]);

  return null;
}
