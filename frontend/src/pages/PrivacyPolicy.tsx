import { Shield, Lock, Eye, Database, Globe, Mail } from "lucide-react";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";

const sections = [
  {
    icon: <Database className="h-5 w-5" />,
    title: "Information We Collect",
    content: [
      "**Account Information**: When you create an account, we collect your name, email address, and password (securely hashed).",
      "**Resume Data**: Resumes you upload are processed to extract structured data for interview question generation. We do not share your resume data with third parties.",
      "**Interview Data**: Your interview responses, evaluation scores, and session recordings are stored to provide you with performance history and analytics.",
      "**Usage Data**: We collect anonymized usage statistics such as pages visited, features used, and session duration to improve our platform.",
    ],
  },
  {
    icon: <Eye className="h-5 w-5" />,
    title: "How We Use Your Information",
    content: [
      "**Personalized Interview Experience**: Your resume data is used to generate tailored interview questions relevant to your skills and experience.",
      "**AI Evaluation**: Your responses are analyzed by our AI engine to provide scores, feedback, and improvement suggestions.",
      "**Service Improvement**: Anonymized, aggregated data helps us improve our AI models, user interface, and overall platform quality.",
      "**Communication**: We may send you service-related emails such as password resets and important platform updates.",
      "**Legal Compliance**: We may process your data as required by applicable law, regulation, or legal process.",
    ],
  },
  {
    icon: <Lock className="h-5 w-5" />,
    title: "Data Security",
    content: [
      "All data is transmitted over HTTPS/TLS encrypted connections.",
      "Passwords are hashed using scrypt with unique salts — we never store plaintext passwords.",
      "Database access is restricted with role-based access controls and network segmentation.",
      "We perform regular security audits and vulnerability assessments.",
      "Session tokens are cryptographically generated and expire after 30 days of inactivity.",
    ],
  },
  {
    icon: <Globe className="h-5 w-5" />,
    title: "Data Retention & Deletion",
    content: [
      "Your account data is retained for as long as your account is active.",
      "Interview history is retained for 12 months and can be manually deleted at any time from your dashboard.",
      "Upon account deletion, all personal data is permanently removed within 30 days.",
      "Anonymized, aggregated analytics data may be retained indefinitely as it cannot be traced back to individual users.",
      "You can request a complete data export at any time by contacting our support team.",
    ],
  },
  {
    icon: <Shield className="h-5 w-5" />,
    title: "Your Rights",
    content: [
      "**Right to Access**: You can view and download all data we hold about you.",
      "**Right to Rectification**: You can update your personal information at any time through your account settings.",
      "**Right to Erasure**: You can request complete deletion of your account and associated data.",
      "**Right to Data Portability**: You can export your interview history and evaluation data.",
      "**Right to Object**: You can opt out of anonymized analytics collection by contacting support.",
    ],
  },
  {
    icon: <Mail className="h-5 w-5" />,
    title: "Contact Us",
    content: [
      "If you have any questions about this Privacy Policy or our data practices, please contact us at:",
      "**Email**: privacy@interviewer.ai",
      "**Response Time**: We aim to respond to all privacy-related inquiries within 48 hours.",
      "This policy was last updated on April 7, 2026.",
    ],
  },
];

export default function PrivacyPolicy() {
  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <PublicNavbar />

      {/* Background effects */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-brand/10 blur-[140px]" />
      </div>

      <main className="relative mx-auto max-w-4xl px-4 pt-28 pb-20 md:px-6">
        {/* Header */}
        <div className="mb-12 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-brand/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <Shield className="h-3.5 w-3.5" /> Privacy Policy
          </span>
          <h1 className="mt-5 text-4xl font-extrabold tracking-tight md:text-5xl">
            Your <span className="text-foreground">privacy matters</span>
          </h1>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground md:text-lg">
            We are committed to protecting your personal data and being transparent about how we collect, use, and safeguard your information.
          </p>
          <p className="mt-2 text-sm text-muted-foreground">Effective date: April 7, 2026</p>
        </div>

        {/* Sections */}
        <div className="space-y-6">
          {sections.map((section) => (
            <div
              key={section.title}
              className="rounded-2xl border border-border bg-card shadow-sm border border-border p-6 transition-all duration-300 hover:border-primary/20"
            >
              <h2 className="flex items-center gap-3 text-lg font-bold tracking-tight">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-primary">
                  {section.icon}
                </div>
                {section.title}
              </h2>
              <ul className="mt-4 space-y-3">
                {section.content.map((item, i) => (
                  <li key={i} className="text-sm leading-relaxed text-muted-foreground pl-1">
                    <span
                      dangerouslySetInnerHTML={{
                        __html: item.replace(/\*\*(.*?)\*\*/g, '<strong class="text-foreground">$1</strong>'),
                      }}
                    />
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
