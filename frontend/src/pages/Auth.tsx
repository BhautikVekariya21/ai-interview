import { FormEvent, ReactNode, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  BadgeCheck,
  ArrowUpRight,
  CheckCircle2,
  Crown,
  Eye,
  EyeOff,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/components/AuthProvider";
import LogoStack from "@/components/LogoStack";
import Seo from "@/components/Seo";
import { SignIn, SignUp } from "@clerk/react";
import { appPath } from "@/lib/paths";

type AuthMode = "signin" | "signup" | "reset" | "verify";

const signinFeatures = [
  {
    icon: Sparkles,
    title: "Resume-tailored interviews",
    text: "AI reads your resume and generates questions specific to your skills and experience level.",
  },
  {
    icon: ShieldCheck,
    title: "Private & secure",
    text: "Your uploads, sessions, and scores stay tied to your profile — never shared.",
  },
  {
    icon: BadgeCheck,
    title: "Track your progress",
    text: "Review past interviews, compare scores, and see how you improve over time.",
  },
];

const signupFeatures = [
  {
    icon: Zap,
    title: "Start in seconds",
    text: "Upload a resume, get AI-generated questions, and start your mock interview instantly.",
  },
  {
    icon: Crown,
    title: "100% Free & Unlimited",
    text: "No credit card required. Practice with unlimited interviews and get full analysis.",
  },
  {
    icon: CheckCircle2,
    title: "AI-powered feedback",
    text: "Get detailed scores, strengths, improvements, and ideal answer references.",
  },
];

export default function Auth() {
  const [searchParams] = useSearchParams();
  const initialMode = searchParams.get("mode") === "signup"
    ? "signup"
    : searchParams.get("mode") === "reset"
      ? "reset"
      : searchParams.get("mode") === "verify"
        ? "verify"
        : "signin";
  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const resetTokenFromUrl = searchParams.get("token") || "";
  const verifyTokenFromUrl = searchParams.get("token") || "";

  // Form fields
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resetEmail, setResetEmail] = useState("");
  const [resetToken, setResetToken] = useState(resetTokenFromUrl);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [verifyStatus, setVerifyStatus] = useState<"pending" | "success" | "error">("pending");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  const { verifyEmail, forgotPassword, resetPassword, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleAuthError = (message: string) => {
    toast({
      variant: "destructive",
      title: showForgotPassword
        ? "Reset link failed"
        : mode === "reset"
          ? "Password reset failed"
          : "Something went wrong",
      description: message,
    });
  };

  const handleForgotPassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      await forgotPassword(resetEmail);
      toast({
        title: "Check your email",
        description: "If an account exists for that email, a password reset link is on its way.",
      });
      setShowForgotPassword(false);
    } catch (error) {
      handleAuthError(error instanceof Error ? error.message : "Could not start password reset.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!resetToken.trim()) {
      handleAuthError("Reset token is required.");
      return;
    }
    if (password.length < 8) {
      handleAuthError("Password must be at least 8 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      handleAuthError("Passwords do not match. Please re-enter.");
      return;
    }

    setIsSubmitting(true);
    try {
      await resetPassword(resetToken.trim(), password);
      toast({ title: "Password reset complete", description: "You can now sign in with your new password." });
      setMode("signin");
      setPassword("");
      setConfirmPassword("");
      setResetToken("");
    } catch (error) {
      handleAuthError(error instanceof Error ? error.message : "Could not reset password.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const switchMode = (newMode: AuthMode) => {
    setMode(newMode);
    setShowForgotPassword(false);
    setPassword("");
    setConfirmPassword("");
    setShowPassword(false);
    setShowConfirm(false);
  };

  useEffect(() => {
    if (!isLoading && isAuthenticated) navigate("/app");
  }, [isAuthenticated, isLoading, navigate]);

  useEffect(() => {
    if (mode !== "verify" || !verifyTokenFromUrl) return;
    let cancelled = false;
    setVerifyStatus("pending");
    verifyEmail(verifyTokenFromUrl)
      .then(() => {
        if (cancelled) return;
        setVerifyStatus("success");
        toast({ title: "Email verified", description: "You can now sign in." });
      })
      .catch(() => {
        if (cancelled) return;
        setVerifyStatus("error");
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, verifyTokenFromUrl]);

  const features = mode === "signup" ? signupFeatures : signinFeatures;

  // Shared Clerk appearance so Google/GitHub + email fields render clearly.
  // Which methods appear is controlled in the Clerk Dashboard (see README note).
  const clerkAppearance = {
    elements: {
      rootBox: "w-full",
      // Keep Clerk's fields away from the card boundary. The smaller mobile
      // padding preserves room on narrow screens while md+ gets a more
      // comfortable inset for the social buttons and form controls.
      card: "shadow-none border-0 bg-transparent w-full box-border p-4 md:p-6",
      headerTitle: "hidden",
      headerSubtitle: "hidden",
      socialButtonsBlockButton:
        "h-12 rounded-xl border border-border bg-card hover:bg-muted/60 text-foreground font-semibold px-5 [--clerk-socialButtonsBlockButtonGap:14px]",
      socialButtonsProviderIcon: "w-5 h-5 shrink-0",
      dividerLine: "bg-border",
      dividerText: "text-muted-foreground text-xs",
      formFieldInput:
        "h-11 rounded-xl border border-border bg-card text-foreground",
      formButtonPrimary:
        "h-11 rounded-xl bg-black text-white hover:bg-brand-hover font-bold normal-case",
      footerActionLink: "text-brand font-semibold hover:text-brand-hover",
      identityPreviewEditButton: "text-brand",
      formFieldLabel: "text-xs font-bold text-foreground",
      footer: "bg-transparent pb-6",
    },
  } as const;

  return (
    <div className="relative min-h-[100dvh] overflow-y-auto w-full bg-[#f6f7f1] text-foreground font-sans selection:bg-brand selection:text-white flex flex-col pt-16 md:pt-0 md:justify-center dark:bg-background">
      <Seo
        title="Sign In or Create an Account"
        description="Log in or create a free interviewer.ai account to start practicing technical interviews with an AI that adapts to your resume and grades your code."
        path="/auth"
      />
      <div aria-hidden="true" className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-44 left-[8%] h-[32rem] w-[32rem] rounded-full bg-lime-200/40 blur-3xl dark:bg-lime-500/10" />
        <div className="absolute -bottom-52 right-[3%] h-[34rem] w-[34rem] rounded-full bg-emerald-200/35 blur-3xl dark:bg-emerald-500/10" />
        <div className="absolute inset-0 opacity-[0.035] [background-image:linear-gradient(to_right,#1e1f1b_1px,transparent_1px),linear-gradient(to_bottom,#1e1f1b_1px,transparent_1px)] [background-size:36px_36px] dark:opacity-[0.07]" />
      </div>

      {/* Top Navbar specifically for Auth Page */}
      <div className="pointer-events-none absolute top-0 left-0 right-0 h-20 flex items-center justify-between px-5 md:px-8 z-20">
        <Link to="/" className="pointer-events-auto flex items-center gap-2.5">
          <LogoStack badge className="h-9 w-9 shadow-lg shadow-black/10" />
          <span className="text-[20px] font-bold tracking-tight">interviewer.ai</span>
        </Link>
        <Link to="/" className="pointer-events-auto hidden sm:inline-flex items-center gap-1.5 text-sm font-semibold text-foreground/65 transition-colors hover:text-foreground">
          Back to home <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="mx-auto w-full max-w-[1120px] p-3 lg:p-4 z-10 my-4 md:my-8">
        <div className="overflow-hidden rounded-[2rem] border border-white/70 bg-card/95 shadow-[0_24px_80px_-28px_rgba(30,31,27,0.38)] backdrop-blur-xl flex flex-col lg:flex-row min-h-[570px] dark:border-white/10">
          
          {/* Left Panel — Form */}
          <div className="flex-1 flex flex-col justify-center py-8 px-6 md:py-8 md:px-10 lg:py-8 lg:px-12">
            <div className="max-w-[400px] mx-auto w-full">
              
              <div className="mb-4">
                {!showForgotPassword && mode !== "verify" && mode !== "reset" && (
                  <div className="flex items-center gap-2 rounded-xl border border-border/70 bg-muted/60 p-1 mb-5 w-max">
                    <button
                      onClick={() => switchMode("signin")}
                      className={`rounded-lg px-5 py-1.5 text-sm font-semibold transition-all ${
                        mode === "signin"
                          ? "bg-foreground text-background shadow-sm"
                          : "text-foreground/70 hover:text-foreground"
                      }`}
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => switchMode("signup")}
                      className={`rounded-lg px-5 py-1.5 text-sm font-semibold transition-all ${
                        mode === "signup"
                          ? "bg-foreground text-background shadow-sm"
                          : "text-foreground/70 hover:text-foreground"
                      }`}
                    >
                      Create Account
                    </button>
                  </div>
                )}

                <div className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.16em] text-brand">
                  <span className="h-1.5 w-1.5 rounded-full bg-brand animate-pulse" />
                  Interview prep, reimagined
                </div>
                <h1 className="text-3xl lg:text-[2.1rem] font-bold tracking-[-0.04em] mb-2">
                  {showForgotPassword
                    ? "Reset your password"
                    : mode === "verify"
                      ? "Verifying your email"
                    : mode === "reset"
                      ? "Create a new password"
                    : mode === "signin"
                      ? "Welcome back"
                      : "Create your account"}
                </h1>
                <p className="text-sm text-foreground/65 font-medium leading-relaxed max-w-[360px]">
                  {showForgotPassword
                    ? "Enter your email and we'll send a secure reset link."
                    : mode === "verify"
                      ? "Confirming your email address."
                    : mode === "reset"
                      ? "Paste your reset token and choose a new password."
                    : mode === "signin"
                      ? "Sign in to continue your interview prep."
                      : "Join engineers preparing smarter with AI."}
                </p>
              </div>

              {showForgotPassword ? (
                /* ───── Forgot Password ───── */
                <form className="space-y-5" onSubmit={handleForgotPassword}>
                  <FieldGroup
                    label="Email address"
                    input={
                      <Input
                        type="email"
                        placeholder="name@example.com"
                        value={resetEmail}
                        onChange={(e) => setResetEmail(e.target.value)}
                        className="h-12 rounded-xl border-border bg-card"
                        required
                      />
                    }
                  />
                  <div className="rounded-xl border border-border bg-muted/50 p-4 text-sm font-medium leading-6 text-foreground/70">
                    We'll send a secure recovery link to reset your password without losing any interview history.
                  </div>
                  <Button type="submit" size="lg" className="h-12 w-full rounded-xl bg-black text-white hover:bg-brand-hover font-bold" disabled={isSubmitting}>
                    {isSubmitting ? "Sending..." : "Send Reset Link"}
                  </Button>
                  <Button type="button" variant="ghost" size="lg" className="h-12 w-full rounded-xl font-bold hover:bg-black/5" onClick={() => setShowForgotPassword(false)}>
                    Back to sign in
                  </Button>
                </form>
              ) : mode === "verify" ? (
                /* ───── Email Verification ───── */
                <div className="space-y-5">
                  <div
                    className={`rounded-xl border p-4 text-sm font-medium leading-6 ${
                      verifyStatus === "success"
                        ? "border-green-500/20 bg-green-500/10 text-green-900"
                        : verifyStatus === "error"
                          ? "border-red-500/20 bg-red-500/10 text-red-900"
                          : "border-border bg-muted/50 text-foreground/70"
                    }`}
                  >
                    {verifyStatus === "success"
                      ? "Your email is verified. You can now sign in to your account."
                      : verifyStatus === "error"
                        ? "This verification link is invalid or has expired. Request a new one from the sign-in screen."
                        : "Verifying your email address…"}
                  </div>
                  <Button
                    type="button"
                    size="lg"
                    className="h-12 w-full rounded-xl bg-black text-white hover:bg-brand-hover font-bold"
                    onClick={() => switchMode("signin")}
                  >
                    Continue to sign in
                  </Button>
                </div>
              ) : mode === "reset" ? (
                <form className="space-y-5" onSubmit={handleResetPassword}>
                  <FieldGroup
                    label="Reset token"
                    input={
                      <Input
                        type="text"
                        placeholder="Paste your reset token"
                        value={resetToken}
                        onChange={(e) => setResetToken(e.target.value)}
                        className="h-12 rounded-xl border-border bg-card"
                        required
                      />
                    }
                  />
                  <FieldGroup
                    label="New password"
                    input={
                      <div className="relative">
                        <Input
                          type={showPassword ? "text" : "password"}
                          placeholder="Minimum 8 characters"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          className="h-12 rounded-xl border-border bg-card pr-11"
                          required
                          minLength={8}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    }
                  />
                  <FieldGroup
                    label="Confirm new password"
                    input={
                      <div className="relative">
                        <Input
                          type={showConfirm ? "text" : "password"}
                          placeholder="Re-enter your new password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          className="h-12 rounded-xl border-border bg-card pr-11"
                          required
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirm(!showConfirm)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                        >
                          {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    }
                  />
                  <Button type="submit" size="lg" className="h-12 w-full rounded-xl bg-black text-white font-bold hover:bg-brand-hover" disabled={isSubmitting}>
                    {isSubmitting ? "Resetting password..." : "Save New Password"}
                  </Button>
                  <Button type="button" variant="ghost" size="lg" className="h-12 w-full rounded-xl font-bold hover:bg-black/5" onClick={() => switchMode("signin")}>
                    Back to sign in
                  </Button>
                </form>
              ) : mode === "signin" ? (
                /* ───── Clerk Sign In (Google / GitHub / email / forgot password) ───── */
                <div className="w-full pt-2 pb-8">
                  {!import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ? (
                    <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm font-medium text-red-900 dark:text-red-200">
                      Clerk is not configured. Add{" "}
                      <code className="font-mono text-xs">VITE_CLERK_PUBLISHABLE_KEY</code> to the
                      repo-root <code className="font-mono text-xs">.env</code>, then restart{" "}
                      <code className="font-mono text-xs">npm run dev</code>.
                    </div>
                  ) : (
                    <SignIn
                      routing="hash"
                      fallbackRedirectUrl={appPath("/app")}
                      signUpUrl={appPath("/auth?mode=signup")}
                      appearance={clerkAppearance}
                    />
                  )}
                </div>
              ) : (
                /* ───── Clerk Sign Up (Google / GitHub / email+password) ───── */
                <div className="w-full pt-2 pb-8">
                  {!import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ? (
                    <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm font-medium text-red-900 dark:text-red-200">
                      Clerk is not configured. Add{" "}
                      <code className="font-mono text-xs">VITE_CLERK_PUBLISHABLE_KEY</code> to the
                      repo-root <code className="font-mono text-xs">.env</code>, then restart{" "}
                      <code className="font-mono text-xs">npm run dev</code>.
                    </div>
                  ) : (
                    <SignUp
                      routing="hash"
                      fallbackRedirectUrl={appPath("/app")}
                      signInUrl={appPath("/auth")}
                      appearance={clerkAppearance}
                    />
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel — Features */}
          <aside className="hidden lg:flex w-[480px] flex-col relative overflow-hidden border-l border-white/10 bg-[#1e2418] py-10 px-10 justify-center text-[#f7f8f0]">
            <div aria-hidden="true" className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-lime-400/20 blur-3xl" />
            <div aria-hidden="true" className="absolute -bottom-24 -left-24 h-80 w-80 rounded-full bg-emerald-400/15 blur-3xl" />
            <div className="relative z-10 flex flex-col">
              <div className="mb-5">
                <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-lime-200 mb-5">
                  <span className="h-1.5 w-1.5 rounded-full bg-lime-300" />
                  {mode === "signin" ? "Secure & Private" : "Get Started Free"}
                </div>
                <h2 className="mb-3 text-3xl leading-[1.08] font-bold tracking-[-0.045em] text-white">
                  {mode === "signin" ? "Pick up where you left off." : "Your AI Interview Coach."}
                </h2>
                <p className="text-sm text-white/65 font-medium leading-relaxed">
                  {mode === "signin"
                    ? "Log in to view your detailed scoring dashboards, resume past interviews, and generate new role challenges."
                    : "Create a free account and start practicing with the most advanced AI-powered mock interviews today."}
                </p>
              </div>

              <div className="space-y-3">
                {features.map(({ icon: Icon, title, text }) => (
                  <div key={title} className="flex gap-4 items-start rounded-2xl border border-white/10 bg-white/[0.055] p-3.5 transition-colors hover:bg-white/[0.09]">
                    <div className="h-10 w-10 shrink-0 rounded-xl bg-lime-300 text-[#1e2418] flex items-center justify-center shadow-lg shadow-lime-500/10">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white mb-0.5">{title}</h3>
                      <p className="text-xs font-medium text-white/60 leading-relaxed">{text}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 flex items-center gap-3 border-t border-white/10 pt-5">
                <div className="flex -space-x-2" aria-hidden="true">
                  {['bg-amber-300', 'bg-sky-300', 'bg-rose-300'].map((color) => <span key={color} className={`flex h-7 w-7 items-center justify-center rounded-full border-2 border-[#1e2418] ${color} text-[9px] font-black text-[#1e2418]`}>✓</span>)}
                </div>
                <p className="text-xs font-medium text-white/60"><span className="font-bold text-white">Built for focused practice.</span> Your next interview starts here.</p>
              </div>
            </div>
          </aside>

        </div>
      </div>
    </div>
  );
}

function FieldGroup({ label, input }: { label: string; input: ReactNode }) {
  return (
    <div className="space-y-1">
      <Label className="text-xs font-bold text-foreground">
        {label}
      </Label>
      {input}
    </div>
  );
}
