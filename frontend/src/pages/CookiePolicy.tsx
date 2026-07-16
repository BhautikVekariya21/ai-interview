import { Cookie, Settings, BarChart3, Shield, ToggleLeft, Mail } from "lucide-react";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";

const sections = [
  {
    icon: <Cookie className="h-5 w-5" />,
    title: "What Are Cookies",
    content: [
      "Cookies are small text files placed on your device when you visit a website. They help the site remember your preferences and improve your experience.",
      "We use both session cookies (which expire when you close your browser) and persistent cookies (which remain until they expire or you delete them).",
      "Similar technologies like local storage and session storage are also used, and this policy covers those as well.",
    ],
  },
  {
    icon: <Settings className="h-5 w-5" />,
    title: "Essential Cookies",
    content: [
      "**Authentication**: We use an `HttpOnly` authentication cookie to keep you signed in, and we may also cache non-sensitive profile data in local storage (`interviewer_auth`) to speed up page loads.",
      "**Session State**: Interview progress, question index, and timer state are stored in session storage to preserve your work if you accidentally refresh the page.",
      "**Theme Preference**: Your dark/light mode preference is stored in local storage so the interface loads with your chosen theme.",
      "These cookies are strictly necessary for the Service to function and cannot be disabled.",
    ],
  },
  {
    icon: <BarChart3 className="h-5 w-5" />,
    title: "Analytics Cookies",
    content: [
      "We use anonymized analytics to understand how users interact with our platform and identify areas for improvement.",
      "No personally identifiable information is collected through analytics cookies.",
      "Analytics data is aggregated and cannot be used to identify individual users.",
      "We do not use third-party advertising trackers or sell any data to advertisers.",
    ],
  },
  {
    icon: <Shield className="h-5 w-5" />,
    title: "Third-Party Cookies",
    content: [
      "We do not use any third-party advertising or payment tracking cookies.",
      "We do not embed social media tracking pixels or third-party advertising scripts.",
      "No data from our cookies is shared with third-party advertisers.",
    ],
  },
  {
    icon: <ToggleLeft className="h-5 w-5" />,
    title: "Managing Cookies",
    content: [
      "You can control and delete cookies through your browser settings. Most browsers allow you to block or delete cookies.",
      "Blocking essential cookies may prevent you from using certain features of the Service, such as staying logged in.",
      "Clearing local storage may remove cached profile data and preferences, while clearing authentication cookies will sign you out.",
      "For more information about managing cookies, visit your browser's help documentation.",
    ],
  },
  {
    icon: <Mail className="h-5 w-5" />,
    title: "Contact Us",
    content: [
      "If you have questions about our use of cookies, please contact us at: **privacy@interviewer.ai**",
      "This Cookie Policy was last updated on April 7, 2026.",
    ],
  },
];

export default function CookiePolicy() {
  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute right-0 top-0 h-[500px] w-[500px] rounded-xl bg-info/10 blur-[140px]" />
      </div>

      <main className="relative mx-auto max-w-4xl px-4 pt-28 pb-20 md:px-6">
        <div className="mb-12 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <Cookie className="h-3.5 w-3.5" /> Cookie Policy
          </span>
          <h1 className="mt-5 text-4xl font-extrabold tracking-tight md:text-5xl">
            Cookie <span className="text-foreground">Policy</span>
          </h1>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground md:text-lg">
            Learn how we use cookies and similar technologies to enhance your experience.
          </p>
          <p className="mt-2 text-sm text-muted-foreground">Effective date: April 7, 2026</p>
        </div>

        <div className="space-y-6">
          {sections.map((section) => (
            <div key={section.title} className="rounded-2xl border border-border bg-card shadow-sm p-6 transition-all duration-300 hover:border-brand/20">
              <h2 className="flex items-center gap-3 text-lg font-bold tracking-tight">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-primary">
                  {section.icon}
                </div>
                {section.title}
              </h2>
              <ul className="mt-4 space-y-3">
                {section.content.map((item, i) => (
                  <li key={i} className="text-sm leading-relaxed text-muted-foreground pl-1">
                    <span dangerouslySetInnerHTML={{ __html: item.replace(/\*\*(.*?)\*\*/g, '<strong class="text-foreground">$1</strong>') }} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </main>

      <Footer />
    </div>
  );
}
