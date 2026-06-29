import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Sun, Moon, User as UserIcon, Bell, Save, Loader2, LogOut, Check, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import { useThemeStore } from "@/stores/themeStore";

export default function SettingsPage() {
  const { user, setUser, logout } = useAuthStore();
  const { theme, setTheme } = useThemeStore();
  const navigate = useNavigate();

  const [name, setName] = useState(user?.name || "");
  const [targetRole, setTargetRole] = useState(user?.target_role || "");
  const [saved, setSaved] = useState(false);
  const [notifReset, setNotifReset] = useState(false);

  const save = useMutation({
    mutationFn: () => authApi.updateProfile({ name, target_role: targetRole }),
    onSuccess: (data) => { setUser(data); setSaved(true); setTimeout(() => setSaved(false), 2000); },
  });

  const resetNotifications = () => {
    localStorage.removeItem("dismissedNotifs");
    setNotifReset(true);
    setTimeout(() => setNotifReset(false), 2000);
  };

  const handleLogout = async () => {
    try { await authApi.logout(); } catch { /* ignore */ }
    logout();
    navigate("/login");
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your appearance, account, and preferences</p>
      </div>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            {theme === "dark" ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />} Appearance
          </CardTitle>
          <CardDescription>Choose how the app looks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <button
              onClick={() => setTheme("light")}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors flex items-center justify-center gap-2 ${
                theme === "light" ? "border-primary bg-primary/5" : "border-muted hover:border-primary/40"
              }`}
            >
              <Sun className="w-5 h-5" /> Light
              {theme === "light" && <Check className="w-4 h-4 text-primary" />}
            </button>
            <button
              onClick={() => setTheme("dark")}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors flex items-center justify-center gap-2 ${
                theme === "dark" ? "border-primary bg-primary/5" : "border-muted hover:border-primary/40"
              }`}
            >
              <Moon className="w-5 h-5" /> Dark
              {theme === "dark" && <Check className="w-4 h-4 text-primary" />}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Account */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg"><UserIcon className="w-5 h-5" /> Account</CardTitle>
          <CardDescription>Update your name and target role</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Full Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input value={user?.email || ""} disabled className="bg-muted" />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Target Role</Label>
            <Input placeholder="e.g. AI Engineer" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
          </div>
          <Button onClick={() => save.mutate()} disabled={save.isPending}>
            {save.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving…</>
              : saved ? <><Check className="w-4 h-4 mr-2" />Saved!</>
              : <><Save className="w-4 h-4 mr-2" />Save changes</>}
          </Button>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg"><Bell className="w-5 h-5" /> Notifications</CardTitle>
          <CardDescription>Control the dashboard notification feed</CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={resetNotifications}>
            {notifReset ? <><Check className="w-4 h-4 mr-2" />Done</> : "Restore dismissed notifications"}
          </Button>
          <p className="text-xs text-muted-foreground mt-2">Brings back any notifications you previously dismissed.</p>
        </CardContent>
      </Card>

      {/* About + logout */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg"><Info className="w-5 h-5" /> About</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            AI Career Copilot — an agentic, multi-agent AI career platform. v1.0.0
          </p>
          <Button variant="destructive" onClick={handleLogout}>
            <LogOut className="w-4 h-4 mr-2" /> Log out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
