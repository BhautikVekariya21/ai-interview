import { useState } from "react";
import {
  Heart,
  Copy,
  Check,
  CreditCard,
  Globe,
  Coffee,
  Landmark,
  IndianRupee,
  QrCode,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";
import Reveal from "@/components/motion/Reveal";

/* ------------------------------------------------------------------ */
/* Payment destinations — update these with your real IDs and links.  */
/* ------------------------------------------------------------------ */
const UPI_ID = "bhautikvekariya1123@oksbi";
const GITHUB_SPONSORS_URL = "https://github.com/sponsors/BhautikVekariya21";
const BUY_ME_A_COFFEE_URL = "https://www.buymeacoffee.com/bhautikvekariya";
const PAYPAL_URL = "https://www.paypal.me/bhautikvekariya";
const RAZORPAY_PAGE_URL = "https://razorpay.me/@bhautikvekariya";
/* ------------------------------------------------------------------ */

type Method = {
  icon: typeof Heart;
  title: string;
  description: string;
  cta: string;
  href: string;
  badge: string;
};

const methods: Method[] = [
  {
    icon: CreditCard,
    title: "Card / Netbanking",
    description:
      "Pay securely with any debit or credit card, netbanking, or wallet through Razorpay.",
    cta: "Donate via Razorpay",
    href: RAZORPAY_PAGE_URL,
    badge: "India · Cards · Wallets",
  },
  {
    icon: Globe,
    title: "International",
    description:
      "Donating from outside India? PayPal works with cards and bank accounts in 200+ countries.",
    cta: "Donate via PayPal",
    href: PAYPAL_URL,
    badge: "Worldwide",
  },
  {
    icon: Coffee,
    title: "Buy Me a Coffee",
    description:
      "A quick, friendly way to say thanks — one-time or monthly, cards accepted worldwide.",
    cta: "Buy me a coffee",
    href: BUY_ME_A_COFFEE_URL,
    badge: "One-time · Monthly",
  },
  {
    icon: Heart,
    title: "GitHub Sponsors",
    description:
      "Sponsor ongoing development directly on GitHub — zero platform fees, cards accepted.",
    cta: "Sponsor on GitHub",
    href: GITHUB_SPONSORS_URL,
    badge: "Recurring · No fees",
  },
];

export default function SupportPage() {
  const [copied, setCopied] = useState(false);

  const copyUpiId = async () => {
    try {
      await navigator.clipboard.writeText(UPI_ID);
      setCopied(true);
      toast.success("UPI ID copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Couldn't copy — long-press the UPI ID to copy it manually.");
    }
  };

  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-brand/10 blur-[140px]" />
      </div>

      <main className="relative mx-auto max-w-4xl px-4 pt-28 pb-20 md:px-6">
        <Reveal className="mb-10 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <Heart className="h-3.5 w-3.5" /> Support
          </span>
          <h1 className="mt-5 text-4xl font-extrabold tracking-tight md:text-5xl">
            Support <span className="text-foreground">interviewer.ai</span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-muted-foreground md:text-lg">
            interviewer.ai is free to use. If it helped you land an interview or level up your prep,
            a donation of any size keeps the servers running and the features coming.
          </p>
        </Reveal>

        {/* UPI — featured for Indian users */}
        <Reveal className="mb-8 rounded-2xl border border-border bg-card p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="flex items-center gap-2 text-lg font-bold">
                <IndianRupee className="h-4 w-4 text-brand" /> UPI
              </h2>
              <p className="mt-1.5 max-w-md text-sm leading-6 text-muted-foreground">
                Instant and free from any UPI app — Google Pay, PhonePe, Paytm, BHIM, or your
                bank's app. Copy the ID below or tap to open your UPI app directly.
              </p>
            </div>
            <span className="rounded-full border border-border bg-muted px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              India · Instant
            </span>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <div className="inline-flex items-center gap-2 rounded-xl border border-border bg-background px-4 py-2.5">
              <QrCode className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-semibold tabular-nums">{UPI_ID}</span>
              <button
                onClick={copyUpiId}
                aria-label="Copy UPI ID"
                className="ml-1 rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
            <a
              href={RAZORPAY_PAGE_URL}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white shadow-sm shadow-brand/25 transition-all hover:bg-brand/90"
            >
              <IndianRupee className="h-4 w-4" /> Pay via Razorpay
            </a>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Razorpay supports UPI, cards, netbanking, and wallets — or copy the UPI ID above into any UPI app.
          </p>
        </Reveal>

        {/* Other methods */}
        <div className="grid gap-4 sm:grid-cols-2">
          {methods.map((m, i) => (
            <Reveal key={m.title} delay={i * 0.05}>
              <div className="flex h-full flex-col rounded-2xl border border-border bg-card p-5 shadow-sm">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand/10 text-brand">
                    <m.icon className="h-4 w-4" />
                  </div>
                  <span className="rounded-full border border-border bg-muted px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    {m.badge}
                  </span>
                </div>
                <h3 className="mt-3 text-base font-bold tracking-tight">{m.title}</h3>
                <p className="mt-1.5 flex-1 text-sm leading-6 text-muted-foreground">{m.description}</p>
                <a
                  href={m.href}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-4 inline-flex items-center gap-2 self-start rounded-xl border border-border bg-background px-4 py-2 text-sm font-semibold transition-colors hover:bg-muted"
                >
                  {m.cta} <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
            </Reveal>
          ))}
        </div>

        {/* Bank transfer / other */}
        <Reveal className="mt-8 rounded-2xl border border-border bg-card p-6 shadow-sm">
          <h2 className="flex items-center gap-2 text-lg font-bold">
            <Landmark className="h-4 w-4 text-brand" /> Other ways to help
          </h2>
          <p className="mt-1.5 text-sm leading-6 text-muted-foreground">
            Prefer a direct bank transfer, or want to sponsor a specific feature? Reach out through
            the{" "}
            <a href="/contact" className="font-semibold text-foreground underline underline-offset-4 hover:text-brand">
              contact page
            </a>{" "}
            and we'll share the details. Not in a position to donate? Starring the project on GitHub
            and sharing it with friends helps just as much.
          </p>
        </Reveal>
      </main>

      <Footer />
    </div>
  );
}
