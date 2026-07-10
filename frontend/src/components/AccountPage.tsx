import { useState } from "react";
import { m as motion } from "framer-motion";
import { AlertTriangle, KeyRound, Save, Trash2, UserCog } from "lucide-react";
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
import { toast } from "sonner";

export default function AccountPage() {
  const { user, updateProfile, deleteAccount } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const saveProfile = async () => {
    setIsSaving(true);
    try {
      await updateProfile({
        full_name: fullName.trim(),
        email: email.trim(),
        current_password: currentPassword || undefined,
        new_password: newPassword || undefined,
      });
      setCurrentPassword("");
      setNewPassword("");
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

  return (
    <div className="max-w-4xl mx-auto py-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight mb-3">
          Account <span className="text-foreground">Settings</span>
        </h1>
        <p className="text-muted-foreground text-base max-w-xl mx-auto leading-relaxed">
          Manage your profile, update login details, and control your account directly from the product.
        </p>
      </motion.div>

      <div className="grid gap-5">
        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="text-lg font-bold flex items-center gap-2 mb-5">
            <UserCog className="w-5 h-5 text-primary" /> Profile
          </h2>
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
        </div>

        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="text-lg font-bold flex items-center gap-2 mb-5">
            <KeyRound className="w-5 h-5 text-primary" /> Change Password
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="current-password">Current password</Label>
              <Input id="current-password" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">New password</Label>
              <Input id="new-password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            Leave the password fields empty if you only want to update your name or email.
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
