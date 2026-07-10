import { useState } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import { Upload, PenTool, ArrowLeft, Copy, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { generateCoverLetter, type CoverLetterResponse } from "@/lib/api";

export default function CoverLetterGeneratorPage() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [dragover, setDragover] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<CoverLetterResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragover(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const handleGenerate = async () => {
    if (!jobDescription.trim()) {
      toast.error("Please provide a job description.");
      return;
    }
    
    setIsGenerating(true);
    setResult(null);
    try {
      const response = await generateCoverLetter(jobDescription, file || undefined);
      if (response && response.success) {
        setResult(response);
      }
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || err.detail || "Failed to generate cover letter.");
    } finally {
      setIsGenerating(false);
    }
  };

  const reset = () => {
    setFile(null);
    setJobDescription("");
    setResult(null);
    setCopied(false);
  };

  const copyToClipboard = () => {
    if (!result?.cover_letter) return;
    navigator.clipboard.writeText(result.cover_letter);
    setCopied(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mx-auto w-full max-w-5xl py-12 px-4">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
        <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-full mb-4">
          <PenTool className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-foreground mb-4">
          AI Cover Letter <span className="text-primary">Generator</span>
        </h1>
        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
          Instantly generate a highly tailored, professional cover letter designed to get past ATS and impress hiring managers. 100% free.
        </p>
      </motion.div>

      {/* Main Container */}
      <div className="bg-card border border-border shadow-xl min-h-[500px] rounded-3xl overflow-hidden relative">
        <AnimatePresence mode="wait">
          {!isGenerating && !result && (
            <motion.div
              key="input"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-6 md:p-10 flex flex-col md:flex-row gap-8"
            >
              {/* Left Column: Job Description */}
              <div className="flex-1 space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-1">1. Job Description</h3>
                  <p className="text-sm text-muted-foreground mb-4">Paste the role requirements here</p>
                  <textarea
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="e.g. We are looking for a Senior Software Engineer with 5+ years of experience in React and Node.js..."
                    className="w-full h-[300px] p-4 bg-background border border-border rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent resize-none text-foreground"
                  />
                </div>
              </div>

              {/* Right Column: Resume Upload & Submit */}
              <div className="flex-1 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-1">2. Your Resume (Optional)</h3>
                  <p className="text-sm text-muted-foreground mb-4">Upload to tailor the letter to your experience</p>
                  
                  {!file ? (
                    <label
                      onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
                      onDragLeave={() => setDragover(false)}
                      onDrop={handleDrop}
                      className={`w-full flex-col flex items-center justify-center border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors h-[180px] ${dragover ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-accent/10"}`}
                    >
                      <input type="file" className="hidden" accept=".pdf,.txt" onChange={handleInputChange} />
                      <Upload className="w-8 h-8 text-muted-foreground mb-3" />
                      <span className="text-sm font-medium text-foreground">Click or drag file</span>
                      <span className="text-xs text-muted-foreground mt-1">.pdf or .txt limit 5MB</span>
                    </label>
                  ) : (
                    <div className="w-full flex items-center justify-between bg-primary/5 border border-primary/20 rounded-xl p-6 h-[180px]">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-primary/10 rounded-full text-primary">
                          <CheckCircle2 className="w-6 h-6" />
                        </div>
                        <div className="text-left">
                          <p className="text-sm font-bold text-foreground line-clamp-1">{file.name}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">Attached successfully</p>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm" onClick={(e) => { e.preventDefault(); setFile(null); }}>Remove</Button>
                    </div>
                  )}
                </div>

                <div className="pt-4">
                  <Button
                    onClick={handleGenerate}
                    disabled={!jobDescription.trim()}
                    className="w-full h-14 text-lg font-bold shadow-lg shadow-primary/20"
                  >
                    Generate Cover Letter
                  </Button>
                </div>
              </div>
            </motion.div>
          )}

          {isGenerating && (
            <motion.div
              key="generating"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-10 flex flex-col items-center justify-center min-h-[500px]"
            >
              <div className="relative w-24 h-24 mb-6">
                <div className="absolute inset-0 bg-primary blur-xl opacity-20 animate-pulse rounded-full" />
                <PenTool className="w-full h-full text-primary relative z-10 animate-bounce" />
              </div>
              <h2 className="text-2xl font-bold text-foreground">Drafting your masterpiece...</h2>
              <p className="text-muted-foreground mt-2">Connecting your experience to their requirements.</p>
            </motion.div>
          )}

          {result && (
            <motion.div
              key="result"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="p-6 md:p-10 flex flex-col h-full"
            >
              <div className="flex items-center justify-between mb-6">
                <button onClick={reset} className="flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                  <ArrowLeft className="w-4 h-4 mr-2" /> Start over
                </button>
                
                <Button variant="outline" onClick={copyToClipboard} className="flex items-center gap-2">
                  {copied ? <CheckCircle2 className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
                  {copied ? "Copied!" : "Copy to Clipboard"}
                </Button>
              </div>

              <div className="bg-background border border-border rounded-2xl p-8 max-w-4xl mx-auto w-full prose prose-slate dark:prose-invert">
                <div className="whitespace-pre-wrap text-foreground font-medium leading-relaxed">
                  {result.cover_letter}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
