import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, TrendingUp, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { resumeApi } from "@/services/api";
import { cn } from "@/lib/utils";
import type { ResumeAnalysisResponse } from "@/types";

function ScoreCircle({ score }: { score: number }) {
  const color = score >= 80 ? "text-green-500" : score >= 60 ? "text-yellow-500" : "text-red-500";
  return (
    <div className="flex flex-col items-center justify-center p-6">
      <div className={`text-6xl font-bold ${color}`}>{score}</div>
      <div className="text-sm text-muted-foreground mt-1">ATS Score / 100</div>
      <div className="mt-2">
        <Badge variant={score >= 80 ? "success" : score >= 60 ? "warning" : "destructive"}>
          {score >= 80 ? "Strong" : score >= 60 ? "Average" : "Needs Work"}
        </Badge>
      </div>
    </div>
  );
}

export default function ResumeAnalyzerPage() {
  const [file, setFile] = useState<File | null>(null);
  const [targetRole, setTargetRole] = useState("");
  const [result, setResult] = useState<ResumeAnalysisResponse | null>(null);

  const { data: history } = useQuery({ queryKey: ["resume-history"], queryFn: resumeApi.history });

  const mutation = useMutation({
    mutationFn: () => resumeApi.analyze(file!, targetRole),
    onSuccess: (data) => setResult(data),
  });

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { "application/pdf": [".pdf"] }, maxFiles: 1,
  });

  const handleAnalyze = () => {
    if (!file || !targetRole.trim()) return;
    setResult(null);
    mutation.mutate();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Resume Analyzer</h1>
        <p className="text-muted-foreground mt-1">Upload your resume and get an AI-powered ATS analysis with improvement suggestions</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Upload Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-lg">Upload Resume</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {/* Dropzone */}
              <div
                {...getRootProps()}
                className={cn(
                  "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                  isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/30 hover:border-primary/50"
                )}
              >
                <input {...getInputProps()} />
                {file ? (
                  <div className="flex items-center justify-center gap-3">
                    <FileText className="w-8 h-8 text-primary" />
                    <div className="text-left">
                      <p className="font-medium text-sm">{file.name}</p>
                      <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(0)} KB</p>
                    </div>
                    <button onClick={(e) => { e.stopPropagation(); setFile(null); }} className="ml-auto">
                      <X className="w-4 h-4 text-muted-foreground hover:text-destructive" />
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="w-10 h-10 mx-auto text-muted-foreground/50" />
                    <p className="text-sm font-medium">{isDragActive ? "Drop here" : "Drag & drop your PDF"}</p>
                    <p className="text-xs text-muted-foreground">or click to browse — max 10 MB</p>
                  </div>
                )}
              </div>

              {/* Target Role */}
              <div className="space-y-2">
                <Label htmlFor="role">Target Role *</Label>
                <Input id="role" placeholder="e.g. AI Engineer, Data Scientist" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
              </div>

              <Button className="w-full" onClick={handleAnalyze} disabled={!file || !targetRole.trim() || mutation.isPending}>
                {mutation.isPending ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Analyzing with Gemini...</>
                ) : (
                  <><TrendingUp className="w-4 h-4 mr-2" />Analyze Resume</>
                )}
              </Button>

              {mutation.isError && (
                <div className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-sm">
                  <AlertCircle className="w-4 h-4" />
                  {(mutation.error as any)?.response?.data?.detail || "Analysis failed. Please try again."}
                </div>
              )}
            </CardContent>
          </Card>

          {/* History */}
          {history?.items?.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Recent Analyses</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {history.items.slice(0, 4).map((h: any) => (
                  <div key={h.resume_id} className="flex items-center justify-between p-2 rounded hover:bg-muted/50 cursor-pointer" onClick={() => resumeApi.getById(h.resume_id).then(setResult)}>
                    <div>
                      <p className="text-sm font-medium truncate max-w-[180px]">{h.filename}</p>
                      <p className="text-xs text-muted-foreground">{new Date(h.created_at).toLocaleDateString()}</p>
                    </div>
                    {h.ats_score && <Badge variant={h.ats_score >= 70 ? "success" : "warning"}>{h.ats_score}/100</Badge>}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Results Panel */}
        <div>
          {mutation.isPending && (
            <Card>
              <CardContent className="p-6 space-y-4">
                <Skeleton className="h-8 w-32 mx-auto" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-20 w-full" />
                <p className="text-center text-sm text-muted-foreground">AI is analysing your resume...</p>
              </CardContent>
            </Card>
          )}

          {result && (
            <div className="space-y-4">
              {/* ATS Score */}
              <Card>
                <CardContent className="p-0">
                  <div className="flex items-center">
                    <ScoreCircle score={result.analysis?.ats_score ?? 0} />
                    <div className="flex-1 p-4 border-l space-y-2">
                      <p className="text-sm font-medium">For role: {result.analysis?.target_role}</p>
                      <p className="text-xs text-muted-foreground">{result.page_count} pages · {result.word_count} words</p>
                      {result.analysis?.score_breakdown && (
                        <div className="space-y-1">
                          {Object.entries(result.analysis.score_breakdown).map(([k, v]) => (
                            <div key={k} className="flex items-center gap-2">
                              <span className="text-xs text-muted-foreground w-28 capitalize">{k.replace(/_/g, " ")}</span>
                              <Progress value={v as number} className="h-1.5 flex-1" />
                              <span className="text-xs w-6 text-right">{v as number}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Skills */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-green-600">✓ Your Skills ({result.analysis?.extracted_skills?.length})</CardTitle></CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1">
                      {result.analysis?.extracted_skills?.slice(0, 10).map((s) => <Badge key={s} variant="success" className="text-xs">{s}</Badge>)}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm text-red-600">✗ Missing ({result.analysis?.missing_skills?.length})</CardTitle></CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1">
                      {result.analysis?.missing_skills?.slice(0, 8).map((s) => <Badge key={s} variant="destructive" className="text-xs">{s}</Badge>)}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Suggestions */}
              <Card>
                <CardHeader><CardTitle className="text-sm">Improvement Suggestions</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {result.analysis?.suggestions?.map((s, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                        <span>{s}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Strengths */}
              {result.analysis?.strengths?.length > 0 && (
                <Card>
                  <CardHeader><CardTitle className="text-sm">Strengths</CardTitle></CardHeader>
                  <CardContent>
                    <div className="space-y-1">
                      {result.analysis.strengths.map((s, i) => (
                        <p key={i} className="text-sm flex items-center gap-2">
                          <span className="text-green-500">★</span>{s}
                        </p>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {!result && !mutation.isPending && (
            <Card className="h-full min-h-[300px] flex items-center justify-center">
              <CardContent className="text-center space-y-3">
                <FileText className="w-12 h-12 mx-auto text-muted-foreground/30" />
                <p className="text-muted-foreground">Upload your resume and click Analyze to see results</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
