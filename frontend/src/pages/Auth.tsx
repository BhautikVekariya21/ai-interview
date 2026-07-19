import { FormEvent, ReactNode, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  BadgeCheck,
  Eye,
  EyeOff,
  Github,
  KeyRound,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Sparkles,
  User,
  CheckCircle2,
  Crown,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/components/AuthProvider";
import LogoStack from "@/components/LogoStack";


type AuthMode = "signin" | "signup" | "reset" | "verify";
type OAuthProvider = "google" | "github";

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
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resetEmail, setResetEmail] = useState("");
  const [resetToken, setResetToken] = useState(resetTokenFromUrl);
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [verifyStatus, setVerifyStatus] = useState<"pending" | "success" | "error">("pending");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<OAuthProvider | null>(null);
  const { toast } = useToast();
  const { login, signup, verifyEmail, forgotPassword, resetPassword, oauthLogin, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleAuthError = (message: string) => {
    toast({
      variant: "destructive",
      title: mode === "signin" ? "Sign in failed" : "Sign up failed",
      description: message,
    });
  };

  const handleSignIn = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      await login({ email, password });
      toast({ title: "Welcome back!", description: "Your interview workspace is ready." });
      navigate("/app");
    } catch (error) {
      handleAuthError(error instanceof Error ? error.message : "Could not sign in. Check your credentials.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSignUp = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (password.length < 8) {
      handleAuthError("Password must be at least 8 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      handleAuthError("Passwords do not match. Please re-enter.");
      return;
    }
    if (!agreeTerms) {
      handleAuthError("Please accept the Terms of Service and Privacy Policy.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await signup({ email, password, full_name: fullName });
      toast({
        title: "Check your email",
        description: res.message || "We've sent a verification link to confirm your account.",
      });
      switchMode("signin");
    } catch (error) {
      handleAuthError(error instanceof Error ? error.message : "Could not create account. Try a different email.");
    } finally {
      setIsSubmitting(false);
    }
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

  const handleOAuth = (provider: OAuthProvider) => {
    setOauthLoading(provider);
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    window.location.href = `${apiBaseUrl.replace(/\/$/, "")}/auth/oauth/${provider}`;
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

  return (
    <div className="relative h-[100dvh] overflow-hidden w-full bg-background text-foreground font-sans selection:bg-brand selection:text-white flex flex-col pt-12 md:pt-0 md:justify-center">
      {/* Top Navbar specifically for Auth Page */}
      <div className="pointer-events-none absolute top-0 left-0 right-0 h-20 flex items-center px-8 z-20">
        <Link to="/" className="pointer-events-auto flex items-center gap-2.5">
          <LogoStack badge className="h-9 w-9" />
          <span className="text-[20px] font-bold tracking-tight">interviewer.ai</span>
        </Link>
      </div>

      <div className="mx-auto w-full max-w-[1100px] p-3 lg:p-4 z-10">
        <div className="bg-card overflow-hidden rounded-[2rem] border border-border shadow-sm flex flex-col lg:flex-row min-h-[500px]">
          
          {/* Left Panel — Form */}
          <div className="flex-1 flex flex-col justify-center py-6 px-6 md:py-6 md:px-8 lg:py-6 lg:px-10">
            <div className="max-w-[400px] mx-auto w-full">
              
              <div className="mb-4">
                {!showForgotPassword && mode !== "verify" && mode !== "reset" && (
                  <div className="flex items-center gap-2 rounded-xl bg-black/5 p-1 mb-3 w-max">
                    <button
                      onClick={() => switchMode("signin")}
                      className={`rounded-lg px-5 py-1.5 text-sm font-semibold transition-all ${
                        mode === "signin"
                          ? "bg-card text-foreground shadow-sm"
                          : "text-foreground/70 hover:text-foreground"
                      }`}
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => switchMode("signup")}
                      className={`rounded-lg px-5 py-1.5 text-sm font-semibold transition-all ${
                        mode === "signup"
                          ? "bg-card text-foreground shadow-sm"
                          : "text-foreground/70 hover:text-foreground"
                      }`}
                    >
                      Create Account
                    </button>
                  </div>
                )}

                <h1 className="text-2xl lg:text-3xl font-semibold tracking-tight mb-1.5">
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
                <p className="text-sm text-foreground/70 font-medium leading-relaxed">
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
                /* ───── Sign In Form ───── */
                <div className="space-y-3">
                  <SocialActions mode="signin" oauthLoading={oauthLoading} onOAuth={handleOAuth} />
                  <AuthDivider />
                  <form className="space-y-3" onSubmit={handleSignIn}>
                    <FieldGroup
                      label="Email"
                      input={
                        <Input
                          type="email"
                          placeholder="you@company.com"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          className="h-12 rounded-xl border-border bg-card"
                          required
                        />
                      }
                    />
                    <FieldGroup
                      label="Password"
                      input={
                        <div className="relative">
                          <Input
                            type={showPassword ? "text" : "password"}
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="h-12 rounded-xl border-border bg-card pr-11"
                            required
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

                    <div className="flex items-center justify-between text-sm">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" className="rounded border-border accent-[hsl(var(--brand))] text-foreground focus:ring-brand" />
                        <span className="text-foreground/70 font-medium">Remember me</span>
                      </label>
                      <button
                        type="button"
                        onClick={() => { setResetEmail(email); setShowForgotPassword(true); }}
                        className="font-bold text-foreground border-b border-border hover:border-foreground transition-colors"
                      >
                        Forgot password?
                      </button>
                    </div>

                    <Button type="submit" size="lg" className="h-12 w-full mt-2 rounded-xl bg-brand text-brand-foreground font-bold text-base hover:bg-brand-hover" disabled={isSubmitting}>
                      {isSubmitting ? (
                        <span className="flex items-center gap-2">
                          <span className="h-4 w-4 animate-spin rounded-xl border-2 border-current border-t-transparent" />
                          Signing in...
                        </span>
                      ) : "Sign In"}
                    </Button>
                  </form>
                </div>
              ) : (
                /* ───── Sign Up Form ───── */
                <div className="space-y-3">
                  <SocialActions mode="signup" oauthLoading={oauthLoading} onOAuth={handleOAuth} />
                  <AuthDivider />
                  <form className="space-y-3" onSubmit={handleSignUp}>
                    <FieldGroup
                      label="Full Name"
                      input={
                        <Input
                          type="text"
                          placeholder="John Doe"
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          className="h-12 rounded-xl border-border bg-card"
                          required
                          minLength={2}
                        />
                      }
                    />
                    <FieldGroup
                      label="Email"
                      input={
                        <Input
                          type="email"
                          placeholder="you@company.com"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          className="h-12 rounded-xl border-border bg-card"
                          required
                        />
                      }
                    />
                    <FieldGroup
                      label="Password"
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
                    
                    {/* Password strength indicator */}
                    {password && (
                      <div className="space-y-1.5 pt-1">
                        <div className="flex gap-1">
                          {[1, 2, 3, 4].map((level) => {
                            const strength = getPasswordStrength(password);
                            return (
                              <div
                                key={level}
                                className={`h-1 flex-1 rounded-xl transition-colors ${
                                  level <= strength
                                    ? strength <= 1 ? "bg-red-500" : strength <= 2 ? "bg-amber-400" : strength <= 3 ? "bg-[#3B82F6]" : "bg-green-500"
                                    : "bg-black/10"
                                }`}
                              />
                            );
                          })}
                        </div>
                        <p className="text-[10px] text-muted-foreground font-semibold tracking-wide uppercase">
                          {getPasswordLabel(getPasswordStrength(password))}
                        </p>
                      </div>
                    )}

                    {/* Terms */}
                    <label className="flex items-start gap-3 pt-2 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={agreeTerms}
                        onChange={(e) => setAgreeTerms(e.target.checked)}
                        className="mt-1 rounded border-border accent-[hsl(var(--brand))] text-foreground focus:ring-brand"
                      />
                      <span className="text-xs text-foreground/70 font-medium leading-relaxed">
                        I agree to the{" "}
                        <Link to="/terms" className="font-bold text-foreground border-b border-border hover:border-foreground transition-colors">
                          Terms of Service
                        </Link>{" "}
                        and{" "}
                        <Link to="/privacy" className="font-bold text-foreground border-b border-border hover:border-foreground transition-colors">
                          Privacy Policy
                        </Link>.
                      </span>
                    </label>

                    <Button
                      type="submit"
                      size="lg"
                      className="h-12 w-full mt-2 rounded-xl bg-brand text-brand-foreground font-bold text-base hover:bg-brand-hover"
                      disabled={isSubmitting || !agreeTerms}
                    >
                      {isSubmitting ? (
                        <span className="flex items-center gap-2">
                          <span className="h-4 w-4 animate-spin rounded-xl border-2 border-current border-t-transparent" />
                          Creating account...
                        </span>
                      ) : "Create Free Account"}
                    </Button>
                  </form>
                </div>
              )}
            </div>
          </div>

          {/* Right Panel — Features */}
          <aside className="hidden lg:flex w-[480px] flex-col relative overflow-hidden bg-muted/50 border-l border-border py-6 px-8 justify-center">
            <div className="relative z-10 flex flex-col">
              <div className="mb-5">
                <div className="inline-flex items-center gap-2 rounded-xl border border-border bg-black/5 px-2.5 py-1 text-[11px] font-bold uppercase tracking-widest text-foreground mb-4">
                  {mode === "signin" ? "Secure & Private" : "Get Started Free"}
                </div>
                <h2 className="mb-2 text-2xl lg:text-3xl font-semibold tracking-tight text-foreground">
                  {mode === "signin" ? "Pick up where you left off." : "Your AI Interview Coach."}
                </h2>
                <p className="text-base text-foreground/70 font-medium leading-relaxed">
                  {mode === "signin"
                    ? "Log in to view your detailed scoring dashboards, resume past interviews, and generate new role challenges."
                    : "Create a free account and start practicing with the most advanced AI-powered mock interviews today."}
                </p>
              </div>

              <div className="space-y-4">
                {features.map(({ icon: Icon, title, text }) => (
                  <div key={title} className="flex gap-4 items-start">
                    <div className="h-10 w-10 shrink-0 rounded-2xl bg-card border border-border flex items-center justify-center text-foreground shadow-sm">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-foreground mb-0.5">{title}</h3>
                      <p className="text-xs font-medium text-foreground/70 leading-relaxed">{text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </aside>

        </div>
      </div>
    </div>
  );
}

/* ─── Social Auth Buttons ───── */
function SocialActions({
  mode,
  oauthLoading,
  onOAuth,
}: {
  mode: AuthMode;
  oauthLoading: OAuthProvider | null;
  onOAuth: (provider: OAuthProvider) => void;
}) {
  const label = mode === "signin" ? "Sign in" : "Sign up";
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Button
        type="button"
        variant="outline"
        size="lg"
        className="h-12 justify-center rounded-xl border border-border bg-card hover:bg-black/5 gap-3 font-bold text-foreground"
        onClick={() => onOAuth("google")}
        disabled={oauthLoading !== null}
      >
        <svg className="h-5 w-5" viewBox="0 0 24 24">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
        </svg>
        {oauthLoading === "google" ? "Connecting..." : "Google"}
      </Button>
      <Button
        type="button"
        variant="outline"
        size="lg"
        className="h-12 justify-center rounded-xl border border-border bg-card hover:bg-black/5 gap-3 font-bold text-foreground"
        onClick={() => onOAuth("github")}
        disabled={oauthLoading !== null}
      >
        <Github className="h-5 w-5" />
        {oauthLoading === "github" ? "Connecting..." : "GitHub"}
      </Button>
    </div>
  );
}

function AuthDivider() {
  return (
    <div className="flex items-center gap-4 py-2">
      <Separator className="flex-1 bg-black/5" />
      <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">or with email</span>
      <Separator className="flex-1 bg-black/5" />
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

function getPasswordStrength(pwd: string): number {
  let s = 0;
  if (pwd.length >= 8) s++;
  if (/[A-Z]/.test(pwd)) s++;
  if (/[0-9]/.test(pwd)) s++;
  if (/[^A-Za-z0-9]/.test(pwd)) s++;
  return s;
}

function getPasswordLabel(s: number): string {
  if (s <= 1) return "Weak";
  if (s === 2) return "Fair";
  if (s === 3) return "Good";
  return "Strong";
}
