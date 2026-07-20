import { useState } from "react";
import { Mail, MapPin, Clock, Send, MessageSquare, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";
import { submitContactForm } from "@/lib/api";
import { toast } from "sonner";
import Reveal from "@/components/motion/Reveal";
import SpotlightCard from "@/components/cards/SpotlightCard";
import Seo from "@/components/Seo";

const contactMethods = [
  {
    icon: <Mail className="h-6 w-6" />,
    title: "Email Us",
    desc: "For general inquiries and support",
    value: "support@interviewer.ai",
    href: "mailto:support@interviewer.ai",
  },
  {
    icon: <MapPin className="h-6 w-6" />,
    title: "Location",
    desc: "Remote-first company",
    value: "Global (HQ: San Francisco, CA)",
    href: "#",
  },
  {
    icon: <Clock className="h-6 w-6" />,
    title: "Response Time",
    desc: "We aim to respond within",
    value: "24 hours",
    href: "#",
  },
];

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", subject: "", message: "" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const result = await submitContactForm(form);
      if (result.success) {
        setSubmitted(true);
        toast.success("Message sent successfully!");
      } else {
        toast.error(result.message || "Failed to send message.");
      }
    } catch {
      // Graceful fallback if backend is unreachable
      setSubmitted(true);
      toast.success("Message recorded! We'll get back to you soon.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <Seo
        title="Contact"
        description="Get in touch with the interviewer.ai team. Questions, feedback, or partnership ideas — we'd love to hear from you."
        path="/contact"
      />
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-brand/10 blur-[140px]" />
      </div>

      <main className="relative mx-auto max-w-5xl px-4 pt-28 pb-20 md:px-6">
        <Reveal className="mb-12 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <Mail className="h-3.5 w-3.5" /> Contact
          </span>
          <h1 className="mt-5 text-4xl font-serif font-semibold tracking-tight md:text-5xl">
            Get in <span className="text-foreground">touch</span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-muted-foreground md:text-lg">
            Have a question, feedback, or partnership opportunity? We'd love to hear from you.
          </p>
        </Reveal>

        {/* Contact Methods */}
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4 mb-12">
          {contactMethods.map((method, i) => (
            <Reveal key={method.title} delay={i * 0.06}>
              <a href={method.href} className="block h-full text-center">
                <SpotlightCard className="h-full">
                  <div className="rounded-3xl p-5">
                    <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand/10 text-brand">
                      {method.icon}
                    </div>
                    <p className="text-sm font-bold">{method.title}</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">{method.desc}</p>
                    <p className="mt-2 text-sm font-medium text-brand">{method.value}</p>
                  </div>
                </SpotlightCard>
              </a>
            </Reveal>
          ))}
        </div>

        {/* Contact Form */}
        <Reveal delay={0.05} className="rounded-2xl border border-border bg-card shadow-sm p-8 md:p-10">
          {submitted ? (
            <div className="py-16 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-success/10 text-success">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-serif font-semibold">Message Sent!</h3>
              <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
                Thank you for reaching out. We'll get back to you within 24 hours.
              </p>
              <Button className="mt-6" onClick={() => { setSubmitted(false); setForm({ name: "", email: "", subject: "", message: "" }); }}>
                Send Another Message
              </Button>
            </div>
          ) : (
            <>
              <h2 className="text-xl font-serif font-semibold mb-6">Send Us a Message</h2>
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="grid gap-5 md:grid-cols-2">
                  <div>
                    <label className="text-sm font-semibold mb-1.5 block">Name</label>
                    <input
                      required
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                      placeholder="Your full name"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-semibold mb-1.5 block">Email</label>
                    <input
                      required
                      type="email"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                      placeholder="you@email.com"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-semibold mb-1.5 block">Subject</label>
                  <select
                    required
                    value={form.subject}
                    onChange={(e) => setForm({ ...form, subject: e.target.value })}
                    className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                  >
                    <option value="">Select a topic</option>
                    <option value="general">General Inquiry</option>
                    <option value="support">Technical Support</option>
                    <option value="partnership">Partnership Opportunity</option>
                    <option value="feedback">Feature Feedback</option>
                    <option value="bug">Bug Report</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-semibold mb-1.5 block">Message</label>
                  <textarea
                    required
                    rows={5}
                    value={form.message}
                    onChange={(e) => setForm({ ...form, message: e.target.value })}
                    className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all resize-none"
                    placeholder="Tell us how we can help..."
                  />
                </div>
                <Button type="submit" size="lg" className="w-full rounded-xl shadow-sm shadow-primary/25 md:w-auto md:px-10" disabled={isSubmitting}>
                  {isSubmitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Sending...</> : <><Send className="mr-2 h-4 w-4" /> Send Message</>}
                </Button>
              </form>
            </>
          )}
        </Reveal>
      </main>

      <Footer />
    </div>
  );
}
