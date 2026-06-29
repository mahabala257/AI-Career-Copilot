import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Briefcase, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/authStore";
import { authApi } from "@/services/api";

const schema = z.object({
  name: z.string().min(2, "Name required"),
  email: z.string().email("Valid email required"),
  password: z.string().min(8, "Min 8 characters"),
  target_role: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setError("");
    try {
      const res = await authApi.register(data as { name: string; email: string; password: string; target_role?: string });
      setAuth(res.user, res.tokens.access_token, res.tokens.refresh_token);
      navigate("/");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Registration failed.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-indigo-50 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="text-center space-y-3">
          <div className="mx-auto w-12 h-12 rounded-xl bg-primary flex items-center justify-center">
            <Briefcase className="w-6 h-6 text-white" />
          </div>
          <CardTitle className="text-2xl">Create Account</CardTitle>
          <CardDescription>Start your AI-powered career journey</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {[
              { id: "name", label: "Full Name", type: "text", placeholder: "Mahalakshmi Bala", field: "name" as const },
              { id: "email", label: "Email", type: "email", placeholder: "you@example.com", field: "email" as const },
              { id: "password", label: "Password", type: "password", placeholder: "Min 8 characters", field: "password" as const },
              { id: "target_role", label: "Target Role (optional)", type: "text", placeholder: "e.g. AI Engineer", field: "target_role" as const },
            ].map(({ id, label, type, placeholder, field }) => (
              <div key={id} className="space-y-2">
                <Label htmlFor={id}>{label}</Label>
                <Input id={id} type={type} placeholder={placeholder} {...register(field)} />
                {errors[field] && <p className="text-xs text-destructive">{errors[field]?.message}</p>}
              </div>
            ))}
            {error && <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">{error}</div>}
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Creating account...</> : "Create Account"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link to="/login" className="text-primary font-medium hover:underline">Sign in</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
