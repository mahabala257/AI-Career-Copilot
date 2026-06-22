import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { User, Save, Loader2, Award, BookOpen } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { authApi, progressApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";

export default function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const [name, setName] = useState(user?.name || "");
  const [targetRole, setTargetRole] = useState(user?.target_role || "");
  const [skillInput, setSkillInput] = useState("");
  const [skills, setSkills] = useState<string[]>(user?.current_skills || []);
  const [saved, setSaved] = useState(false);

  const { data: scoreData } = useQuery({ queryKey: ["career-score"], queryFn: progressApi.score });

  const mutation = useMutation({
    mutationFn: () => authApi.updateProfile({ name, target_role: targetRole, current_skills: skills }),
    onSuccess: (data) => { setUser(data); setSaved(true); setTimeout(() => setSaved(false), 2000); },
  });

  const addSkill = () => {
    const s = skillInput.trim();
    if (s && !skills.includes(s)) { setSkills([...skills, s]); setSkillInput(""); }
  };

  const score = scoreData?.overall_score ?? 0;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold">Profile</h1>
        <p className="text-muted-foreground mt-1">Manage your account and career goals</p>
      </div>

      {/* Career score summary */}
      <Card className="bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-200">
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center">
              <span className="text-2xl font-bold text-white">{score}</span>
            </div>
            <div>
              <p className="font-semibold">Career Readiness Score</p>
              <p className="text-sm text-muted-foreground">Complete more assessments to improve</p>
              <div className="flex gap-2 mt-1">
                {scoreData?.components && Object.entries(scoreData.components).map(([k, v]) => (
                  <Badge key={k} variant="secondary" className="text-xs capitalize">
                    {k.replace("_score", "")}: {v as number}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Profile form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg"><User className="w-5 h-5" />Personal Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Full Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input value={user?.email} disabled className="bg-muted" />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Target Role</Label>
            <Input placeholder="e.g. AI Engineer, Data Scientist" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg"><BookOpen className="w-5 h-5" />Skills</CardTitle>
          <CardDescription>Add skills to get better skill gap analysis</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input placeholder="Type a skill and press Enter or Add" value={skillInput} onChange={(e) => setSkillInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addSkill()} />
            <Button variant="outline" onClick={addSkill}>Add</Button>
          </div>
          <div className="flex flex-wrap gap-2 min-h-[40px]">
            {skills.map((s) => (
              <Badge key={s} variant="secondary" className="cursor-pointer hover:bg-destructive/10" onClick={() => setSkills(skills.filter((x) => x !== s))}>
                {s} ×
              </Badge>
            ))}
            {skills.length === 0 && <p className="text-xs text-muted-foreground">No skills added yet</p>}
          </div>
        </CardContent>
      </Card>

      <Button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="w-full sm:w-auto">
        {mutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Saving...</> :
         saved ? <><Award className="w-4 h-4 mr-2" />Saved!</> :
         <><Save className="w-4 h-4 mr-2" />Save Changes</>}
      </Button>
    </div>
  );
}
