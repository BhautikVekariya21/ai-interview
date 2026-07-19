import { useEffect, useMemo, useState } from "react";
import { m as motion } from "framer-motion";
import {
  AlertTriangle,
  Save,
  Trash2,
  UserCog,
  BadgeCheck,
  CalendarDays,
  Mail,
  ShieldCheck,
  Fingerprint,
  Clock,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useAuth } from "@/components/AuthProvider";
import { getInterviewHistory, type HistoryEntry } from "@/lib/api";
import { toast } from "sonner";

export default function AccountPage() {
  const { user, isAuthenticated, updateProfile, deleteAccount } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    if (!isAuthenticated) {
      setHistory([]);
      return;
    }
    let cancelled = false;
    getInterviewHistory()
      .then((entries) => {
        if (!cancelled) setHistory(entries);
      })
      .catch(() => {
        if (!cancelled) setHistory([]);
      });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  const saveProfile = async () => {
    setIsSaving(true);
    try {
      await updateProfile({
        full_name: fullName.trim(),
        email: email.trim(),
      });
      toast.success("Account settings updated.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not update account settings.");
    } finally {
      setIsSaving(false);
    }
  };

  const removeAccount = async () => {
    setIsDeleting(true);
    try {
      await deleteAccount();
      toast.success("Your account has been deleted.");
      navigate("/");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not delete account.");
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (value?: string | null) => {
    if (!value) return "—";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return "—";
    return parsed.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const provider = (user?.auth_provider as string | undefined) || "email";
  const providerLabel = provider.charAt(0).toUpperCase() + provider.slice(1);

  const stats = useMemo(() => {
    const total = history.length;
    const scores = history
      .map((h) => Number(h.finalScores?.overall ?? 0))
      .filter((n) => !Number.isNaN(n));
    const avg = scores.length
      ? Math.round(scores.reduce((s, n) => s + n, 0) / scores.length)
      : 0;
    const best = scores.length ? Math.max(...scores) : 0;
    const totalQuestions = history.reduce(
      (s, h) => s + Number(h.totalQuestions ?? 0),
      0,
    );
    const lastDate = history
      .map((h) => new Date(h.date).getTime())
      .filter((t) => !Number.isNaN(t))
      .sort((a, b) => b - a)[0];
    return { total, avg, best, totalQuestions, lastDate };
  }, [history]);

  const overviewItems = [
    { icon: Mail, label: "Email", value: user?.email || "—" },
    { icon: ShieldCheck, label: "Sign-in method", value: providerLabel },
    { icon: CalendarDays, label: "Member since", value: formatDate(user?.created_at) },
    { icon: Fingerprint, label: "Account ID", value: user?.id ? String(user.id).slice(0, 12) : "—" },
    { icon: UserCog, label: "Last profile update", value: formatDate(user?.updated_at) },
    {
      icon: Clock,
      label: "Last interview",
      value: stats.lastDate ? formatDate(new Date(stats.lastDate).toISOString()) : "—",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto py-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
        <h1 className="text-4xl md:text-5xl font-serif font-bold tracking-tight leading-tight mb-3 text-[#1E1F1B]">
          Account Settings
        </h1>
        <p className="text-muted-foreground text-base max-w-2xl mx-auto leading-relaxed">
          Manage your profile, review your account details, and control your data. Everything here is
          handled directly from the product — update your name and email, check when you joined and how
          you sign in, or permanently remove your account and interview history whenever you choose.
        </p>
      </motion.div>

      <div className="grid gap-5">
        {/* Account overview — read-only snapshot */}
        <div className="rounded-2xl border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <BadgeCheck className="w-5 h-5 text-primary" /> Account Overview
            </h2>
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-success/10 text-success border border-success/20">
              <span className="w-1.5 h-1.5 rounded-full bg-success" /> Active
            </span>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {overviewItems.map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex items-start gap-3 rounded-xl border border-border/60 bg-muted/20 p-3.5">
                <div className="w-9 h-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
                  <Icon className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
                  <p className="text-sm font-medium text-foreground truncate" title={String(value)}>{value}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="text-lg font-bold flex items-center gap-2 mb-1">
            <UserCog className="w-5 h-5 text-primary" /> Profile
          </h2>
          <p className="text-sm text-muted-foreground mb-5">
            This name and email appear on your interview reports and account notifications.
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="full-name">Full name</Label>
              <Input id="full-name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            Last updated {formatDate(user?.updated_at)}.
          </p>
        </div>

        <div className="flex justify-end">
          <Button onClick={saveProfile} disabled={isSaving}>
            <Save className="w-4 h-4 mr-2" /> {isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </div>

        <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6">
          <h2 className="text-lg font-bold flex items-center gap-2 mb-3 text-destructive">
            <AlertTriangle className="w-5 h-5" /> Danger Zone
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed mb-4">
            Delete your account and all associated interview data. This action cannot be undone.
          </p>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" className="border-destructive/40 text-destructive hover:bg-destructive/10">
                <Trash2 className="w-4 h-4 mr-2" /> Delete Account
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete your account?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently remove your profile, interview history, and saved session data.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={() => void removeAccount()} disabled={isDeleting}>
                  {isDeleting ? "Deleting..." : "Delete Permanently"}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </div>
  );
}
