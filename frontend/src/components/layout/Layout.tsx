import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import {
  LayoutDashboard, FileText, TrendingUp, MessageSquare,
  Brain, Calendar, User, LogOut, Menu, X, Briefcase, ChevronRight,
  Linkedin, FolderGit2, Mic, Building2, GraduationCap, Heart, Sun, Moon, Bot,
  BarChart3, Settings as SettingsIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/stores/authStore";
import { useThemeStore } from "@/stores/themeStore";
import { authApi } from "@/services/api";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/",          icon: LayoutDashboard, label: "Dashboard" },
  { to: "/chat",      icon: Bot,             label: "AI Assistant" },
  { to: "/resume",    icon: FileText,        label: "Resume Analyzer" },
  { to: "/skills",    icon: TrendingUp,      label: "Skill Gap" },
  { to: "/interview", icon: MessageSquare,   label: "Interview Center" },
  { to: "/quiz",      icon: Brain,           label: "Quiz Center" },
  { to: "/planner",   icon: Calendar,        label: "Study Planner" },
];

const phase2NavItems = [
  { to: "/linkedin",  icon: Linkedin,        label: "LinkedIn Optimizer" },
  { to: "/projects",  icon: FolderGit2,      label: "Project Ideas" },
  { to: "/english",   icon: Mic,             label: "English Coach" },
];

const phase3NavItems = [
  { to: "/company",    icon: Building2,      label: "Company Research" },
  { to: "/internship", icon: GraduationCap,  label: "Internship Research" },
  { to: "/wellness",   icon: Heart,          label: "Wellness Coach" },
];

const accountNavItems = [
  { to: "/analytics", icon: BarChart3,    label: "Analytics" },
  { to: "/profile",   icon: User,         label: "Profile" },
  { to: "/settings",  icon: SettingsIcon, label: "Settings" },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { user, logout } = useAuthStore();
  const { theme, toggle: toggleTheme } = useThemeStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    try { await authApi.logout(); } catch {}
    logout();
    navigate("/login");
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside className={cn(
        "flex flex-col bg-card border-r transition-all duration-300 z-20",
        sidebarOpen ? "w-64" : "w-16"
      )}>
        {/* Logo */}
        <div className="flex items-center gap-3 p-4 h-16 border-b">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
            <Briefcase className="w-4 h-4 text-white" />
          </div>
          {sidebarOpen && (
            <div className="overflow-hidden">
              <p className="font-bold text-sm leading-tight">AI Career</p>
              <p className="text-xs text-muted-foreground">Copilot</p>
            </div>
          )}
          <Button
            variant="ghost" size="icon"
            className={cn("ml-auto flex-shrink-0", !sidebarOpen && "mx-auto")}
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </Button>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to} to={to} end={to === "/"}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors group",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {sidebarOpen && <span className="truncate">{label}</span>}
              {sidebarOpen && <ChevronRight className="w-3 h-3 ml-auto opacity-50" />}
            </NavLink>
          ))}

          {/* Phase 2 section */}
          <Separator className="my-2" />
          {phase2NavItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to} to={to}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors group",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {sidebarOpen && <span className="truncate">{label}</span>}
              {sidebarOpen && <ChevronRight className="w-3 h-3 ml-auto opacity-50" />}
            </NavLink>
          ))}

          {/* Phase 3 section */}
          <Separator className="my-2" />
          {phase3NavItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to} to={to}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors group",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {sidebarOpen && <span className="truncate">{label}</span>}
              {sidebarOpen && <ChevronRight className="w-3 h-3 ml-auto opacity-50" />}
            </NavLink>
          ))}

          <Separator className="my-2" />
          {accountNavItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to} to={to}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {sidebarOpen && <span className="truncate">{label}</span>}
              {sidebarOpen && <ChevronRight className="w-3 h-3 ml-auto opacity-50" />}
            </NavLink>
          ))}
        </nav>

        <Separator />

        {/* Theme toggle */}
        <div className="p-2">
          <Button
            variant="ghost"
            size={sidebarOpen ? "sm" : "icon"}
            className={cn("w-full justify-start gap-3", !sidebarOpen && "justify-center")}
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? <Sun className="w-4 h-4 flex-shrink-0" /> : <Moon className="w-4 h-4 flex-shrink-0" />}
            {sidebarOpen && <span className="text-sm">{theme === "dark" ? "Light mode" : "Dark mode"}</span>}
          </Button>
        </div>

        <Separator />

        {/* User footer */}
        <div className="p-2">
          {sidebarOpen ? (
            <div className="flex items-center gap-3 p-2 rounded-md">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                <span className="text-xs font-bold text-primary">
                  {user?.name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.name}</p>
                <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
              </div>
              <Button variant="ghost" size="icon" onClick={handleLogout} title="Logout">
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <Button variant="ghost" size="icon" className="w-full" onClick={handleLogout}>
              <LogOut className="w-4 h-4" />
            </Button>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div
          key={location.pathname}
          className="max-w-6xl mx-auto p-6 animate-in fade-in slide-in-from-bottom-2 duration-300"
        >
          <Outlet />
        </div>
      </main>
    </div>
  );
}
