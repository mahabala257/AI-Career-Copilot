import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Calendar, Loader2, CheckCircle, BookOpen, Target } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { plannerApi } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import type { PlanResponse } from "@/types";

function DailyPlan({ plan }: { plan: PlanResponse["plan_data"] }) {
  return (
    <div className="space-y-4">
      {plan.focus_skill && (
        <div className="flex items-center gap-2 p-3 bg-primary/5 rounded-lg">
          <Target className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium">Today's Focus: {plan.focus_skill}</span>
        </div>
      )}
      {plan.sessions?.map((session) => (
        <Card key={session.session_number}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">{session.time_block}</CardTitle>
              <Badge variant="secondary">{session.duration_hours}h</Badge>
            </div>
            <CardDescription>{session.topic}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {session.tasks?.map((task, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                  <span>{task}</span>
                </div>
              ))}
            </div>
            <p className="text-xs text-primary mt-2 font-medium">🎯 Goal: {session.goal}</p>
          </CardContent>
        </Card>
      ))}
      {plan.career_action && (
        <div className="p-3 bg-green-50 rounded-lg text-sm">
          <span className="font-medium text-green-700">Career Action: </span>
          <span className="text-green-600">{plan.career_action}</span>
        </div>
      )}
      {plan.motivational_note && (
        <div className="p-3 bg-purple-50 rounded-lg text-sm text-purple-700 italic">
          💬 {plan.motivational_note}
        </div>
      )}
    </div>
  );
}

function WeeklyPlan({ plan }: { plan: PlanResponse["plan_data"] }) {
  const dayColors = ["bg-blue-50", "bg-green-50", "bg-purple-50", "bg-orange-50", "bg-pink-50", "bg-yellow-50", "bg-gray-50"];
  return (
    <div className="space-y-4">
      {plan.week_theme && (
        <div className="p-3 bg-primary/5 rounded-lg">
          <p className="font-medium text-sm">Week Theme: {plan.week_theme}</p>
          {plan.weekly_milestone && <p className="text-xs text-muted-foreground mt-1">🏆 Milestone: {plan.weekly_milestone}</p>}
        </div>
      )}
      <div className="grid gap-3">
        {plan.days?.map((day, i) => (
          <Card key={day.day}>
            <CardContent className={`pt-4 pb-4 ${dayColors[i % 7]}`}>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-semibold text-sm">{day.day}</p>
                  {day.theme && <p className="text-xs text-muted-foreground">{day.theme}</p>}
                </div>
                <div className="flex items-center gap-2">
                  {day.focus_skill && <Badge variant="secondary" className="text-xs">{day.focus_skill}</Badge>}
                  <Badge variant="outline" className="text-xs">{day.study_hours}h</Badge>
                </div>
              </div>
              <div className="space-y-1">
                {day.tasks?.slice(0, 3).map((task, ti) => (
                  <p key={ti} className="text-xs flex items-start gap-1.5">
                    <span className="text-muted-foreground mt-0.5">•</span>{task}
                  </p>
                ))}
              </div>
              {day.career_action && (
                <p className="text-xs text-green-700 mt-2">📌 {day.career_action}</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      {plan.week_project && (
        <Card>
          <CardContent className="pt-4 pb-4">
            <p className="text-sm font-medium flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-primary" />Week Project: {plan.week_project}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function MonthlyPlan({ plan }: { plan: PlanResponse["plan_data"] }) {
  return (
    <div className="space-y-4">
      {plan.month_theme && (
        <div className="p-3 bg-primary/5 rounded-lg">
          <p className="font-medium">Month Theme: {plan.month_theme}</p>
        </div>
      )}
      {plan.weeks?.map((week) => (
        <Card key={week.week_number}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Week {week.week_number}: {week.theme}</CardTitle>
              <Badge variant="secondary">{week.daily_hours}h/day</Badge>
            </div>
            <CardDescription className="flex gap-2">
              <Badge variant="info" className="text-xs">{week.primary_skill}</Badge>
              {week.secondary_skill && <Badge variant="secondary" className="text-xs">{week.secondary_skill}</Badge>}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {week.key_tasks?.map((task, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />{task}
              </div>
            ))}
            {week.milestone && (
              <div className="mt-2 p-2 bg-yellow-50 rounded text-xs text-yellow-700">
                🏆 Milestone: {week.milestone}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function StudyPlannerPage() {
  const user = useAuthStore((s) => s.user);
  const [planType, setPlanType] = useState<"daily" | "weekly" | "monthly">("weekly");
  const [targetRole, setTargetRole] = useState(user?.target_role || "");
  const [hours, setHours] = useState("2");
  const [plan, setPlan] = useState<PlanResponse | null>(null);

  const { data: savedPlans } = useQuery({ queryKey: ["current-plans"], queryFn: plannerApi.current });

  const mutation = useMutation({
    mutationFn: () => plannerApi.generate({ plan_type: planType, target_role: targetRole, available_hours: parseFloat(hours) }),
    onSuccess: setPlan,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Study Planner</h1>
        <p className="text-muted-foreground mt-1">AI-generated personalised study plans based on your skill gaps</p>
      </div>

      {/* Config */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid sm:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Plan Type</Label>
              <Select value={planType} onValueChange={(v: any) => setPlanType(v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily Plan</SelectItem>
                  <SelectItem value="weekly">Weekly Plan</SelectItem>
                  <SelectItem value="monthly">Monthly Plan</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label>Target Role</Label>
              <Input placeholder="e.g. AI Engineer" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Hours/Day</Label>
              <Input type="number" min="0.5" max="12" step="0.5" value={hours} onChange={(e) => setHours(e.target.value)} />
            </div>
          </div>
          <Button className="mt-4" onClick={() => mutation.mutate()} disabled={!targetRole.trim() || mutation.isPending}>
            {mutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Generating Plan...</> : <><Calendar className="w-4 h-4 mr-2" />Generate Plan</>}
          </Button>
        </CardContent>
      </Card>

      {/* Active plan */}
      {plan && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold capitalize">{plan.plan_type} Plan — {plan.target_role}</h2>
            <Badge variant="success">Active</Badge>
          </div>
          {plan.plan_type === "daily"   && <DailyPlan   plan={plan.plan_data} />}
          {plan.plan_type === "weekly"  && <WeeklyPlan  plan={plan.plan_data} />}
          {plan.plan_type === "monthly" && <MonthlyPlan plan={plan.plan_data} />}
        </div>
      )}

      {/* Saved plans */}
      {!plan && savedPlans?.length > 0 && (
        <div className="space-y-4">
          <h2 className="font-semibold">Your Active Plans</h2>
          <Tabs defaultValue={savedPlans[0]?.plan_type}>
            <TabsList>{savedPlans.map((p: any) => <TabsTrigger key={p.plan_id} value={p.plan_type} className="capitalize">{p.plan_type}</TabsTrigger>)}</TabsList>
            {savedPlans.map((p: any) => (
              <TabsContent key={p.plan_id} value={p.plan_type}>
                {p.plan_type === "daily"   && <DailyPlan   plan={p.plan_data} />}
                {p.plan_type === "weekly"  && <WeeklyPlan  plan={p.plan_data} />}
                {p.plan_type === "monthly" && <MonthlyPlan plan={p.plan_data} />}
              </TabsContent>
            ))}
          </Tabs>
        </div>
      )}

      {!plan && !savedPlans?.length && !mutation.isPending && (
        <Card className="min-h-[200px] flex items-center justify-center">
          <CardContent className="text-center space-y-3">
            <Calendar className="w-12 h-12 mx-auto text-muted-foreground/30" />
            <p className="text-muted-foreground">Generate your first personalised study plan</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
