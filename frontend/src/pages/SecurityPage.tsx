import { Shield, Lock, Server, Key, Eye, AlertTriangle, CheckCircle2, Mail } from "lucide-react";
import PublicNavbar from "@/components/PublicNavbar";
import Footer from "@/components/Footer";

const practices = [
  {
    icon: <Lock className="h-6 w-6" />,
    title: "Encryption",
    items: [
      "TLS 1.3 encryption for all data in transit",
      "AES-256 encryption for sensitive data at rest",
      "scrypt password hashing with unique per-user salts",
      "Cryptographically secure session token generation",
    ],
  },
  {
    icon: <Server className="h-6 w-6" />,
    title: "Infrastructure",
    items: [
      "Cloud-hosted infrastructure with SOC 2 compliance",
      "DDoS protection and Web Application Firewall (WAF)",
      "Network segmentation and private subnets for databases",
      "Automated backups with point-in-time recovery",
    ],
  },
  {
    icon: <Key className="h-6 w-6" />,
    title: "Access Control",
    items: [
      "Role-based access controls (RBAC) for all internal systems",
      "Session tokens with 30-day expiry and secure rotation",
      "Rate limiting on authentication endpoints",
      "Principle of least privilege for all service accounts",
    ],
  },
  {
    icon: <Eye className="h-6 w-6" />,
    title: "Monitoring",
    items: [
      "Real-time application logging with Loguru",
      "Prometheus metrics and health endpoint monitoring",
      "OpenTelemetry distributed tracing",
      "Automated alerting for anomalous activity patterns",
    ],
  },
];

const certifications = [
  { label: "HTTPS Everywhere", status: "Active" },
  { label: "OWASP Top 10 Compliance", status: "Verified" },
  { label: "Regular Penetration Testing", status: "Quarterly" },
  { label: "Incident Response Plan", status: "Active" },
  { label: "Data Processing Agreement", status: "Available" },
];

export default function SecurityPage() {
  return (
    <div className="relative min-h-screen bg-white text-[#000]">
      <PublicNavbar />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[600px] w-[800px] -translate-x-1/2 -translate-y-1/3 rounded-xl bg-success/8 blur-[140px]" />
      </div>

      <main className="relative mx-auto max-w-5xl px-4 pt-28 pb-20 md:px-6">
        <div className="mb-12 text-center">
          <span className="inline-flex items-center gap-2 rounded-xl border border-primary/25 bg-[#000]/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-primary">
            <Shield className="h-3.5 w-3.5" /> Security
          </span>
          <h1 className="mt-5 text-4xl font-extrabold tracking-tight md:text-5xl">
            Security at <span className="text-black">interviewer.ai</span>
          </h1>
          <p className="mt-4 max-w-2xl mx-auto text-base leading-relaxed text-black/60 md:text-lg">
            We take the security of your data seriously. Here's how we protect your information at every layer.
          </p>
        </div>

        {/* Security Practices Grid */}
        <div className="grid gap-6 md:grid-cols-2 mb-12">
          {practices.map((practice) => (
            <div key={practice.title} className="rounded-2xl border border-black/5 bg-white shadow-sm border border-black/10 p-6 transition-all duration-300 hover:border-primary/20 hover:-translate-y-1">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[#000]/10 text-primary">
                {practice.icon}
              </div>
              <h3 className="text-lg font-bold tracking-tight">{practice.title}</h3>
              <ul className="mt-3 space-y-2">
                {practice.items.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-black/60">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-success" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Certifications */}
        <div className="rounded-2xl border border-black/5 bg-white shadow-sm border border-black/10 p-6 mb-12">
          <h2 className="text-xl font-bold tracking-tight mb-6 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-success/10 text-success">
              <Shield className="h-5 w-5" />
            </div>
            Security & Compliance
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
            {certifications.map((cert) => (
              <div key={cert.label} className="flex items-center justify-between rounded-xl bg-[#F9F9F9]/50 border border-black/10 px-4 py-3">
                <span className="text-sm font-medium">{cert.label}</span>
                <span className="rounded-xl bg-success/10 px-2.5 py-0.5 text-xs font-semibold text-success">{cert.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Report Vulnerability */}
        <div className="rounded-2xl border border-warning/30 bg-gradient-to-br from-warning/5 via-background to-background p-6 text-center">
          <AlertTriangle className="mx-auto h-8 w-8 text-warning mb-3" />
          <h3 className="text-lg font-bold">Report a Vulnerability</h3>
          <p className="mt-2 text-sm text-black/60 max-w-lg mx-auto">
            If you discover a security vulnerability, please report it responsibly. We appreciate your help in keeping our platform safe.
          </p>
          <a
            href="mailto:security@interviewer.ai"
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#000] px-6 py-2.5 text-sm font-semibold text-white shadow-sm shadow-primary/25 transition-all hover:bg-[#000]/90"
          >
            <Mail className="h-4 w-4" /> security@interviewer.ai
          </a>
        </div>
      </main>

      <Footer />
    </div>
  );
}
