import { useState } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import { Upload, Flame, Skull, CheckCircle2, AlertTriangle, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { roastResume, type RoastResponse } from "@/lib/api";

export default function ResumeRoasterPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragover, setDragover] = useState(false);
  const [isRoasting, setIsRoasting] = useState(false);
  const [roastData, setRoastData] = useState<RoastResponse | null>(null);

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

  const handleRoast = async () => {
    if (!file) return;
    setIsRoasting(true);
    setRoastData(null);
    try {
      const response = await roastResume(file);
      if (response && response.success) {
        setRoastData(response);
      }
    } catch (err: any) {
      console.error(err);
      toast.error(err.message || err.detail || "Failed to roast resume. Are you sure it's readable?");
    } finally {
      setIsRoasting(false);
    }
  };

  const reset = () => {
    setFile(null);
    setRoastData(null);
  };

  return (
    <div className="mx-auto w-full max-w-4xl py-12 px-4">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
        <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-full mb-4">
          <Flame className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-foreground mb-4">
          AI Resume <span className="text-primary">Roaster</span>
        </h1>
        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
          Upload your resume and get a brutally honest, no-holds-barred roast from our AI recruiter.
          Find out why you're getting ghosted (it's free).
        </p>
      </motion.div>

      {/* Main Container */}
      <div className="bg-card border border-border shadow-xl min-h-[400px] rounded-3xl overflow-hidden relative">
        <AnimatePresence mode="wait">
          {!file && !isRoasting && !roastData && (
            <motion.div
              key="upload"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-10 flex flex-col items-center justify-center min-h-[400px]"
            >
              <label
                onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
                onDragLeave={() => setDragover(false)}
                onDrop={handleDrop}
                className={`w-full max-w-xl mx-auto border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-colors ${dragover ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-accent/10"}`}
              >
                <input type="file" className="hidden" accept=".pdf,.txt" onChange={handleInputChange} />
                <Upload className="w-10 h-10 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-foreground mb-2">Drop your resume here</h3>
                <p className="text-sm text-muted-foreground">Supports PDF and Text files</p>
              </label>
            </motion.div>
          )}

          {file && !isRoasting && !roastData && (
            <motion.div
              key="confirm"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="p-10 flex flex-col items-center justify-center min-h-[400px]"
            >
              <div className="bg-destructive/10 border border-destructive/20 p-6 rounded-2xl text-center max-w-md w-full">
                <Skull className="w-12 h-12 mx-auto text-destructive mb-4" />
                <h2 className="text-xl font-bold text-foreground mb-2">Ready to be roasted?</h2>
                <p className="text-sm text-muted-foreground mb-6 truncate px-4">{file.name}</p>
                <div className="flex gap-3 justify-center">
                  <Button variant="outline" onClick={reset}>Cancel</Button>
                  <Button
                    onClick={handleRoast}
                    className="bg-destructive hover:bg-destructive/90 text-destructive-foreground font-bold"
                  >
                    Light the fire 🔥
                  </Button>
                </div>
              </div>
            </motion.div>
          )}

          {isRoasting && (
            <motion.div
              key="roasting"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-10 flex flex-col items-center justify-center min-h-[400px]"
            >
              <div className="relative w-24 h-24 mb-6">
                <div className="absolute inset-0 bg-primary blur-xl opacity-20 animate-pulse rounded-full" />
                <Flame className="w-full h-full text-primary relative z-10 animate-bounce" />
              </div>
              <h2 className="text-2xl font-bold text-foreground">Reading between the lines...</h2>
              <p className="text-muted-foreground mt-2">Preparing brutal honesty.</p>
            </motion.div>
          )}

          {roastData && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-6 md:p-10"
            >
              <button onClick={reset} className="flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-6 transition-colors">
                <ArrowLeft className="w-4 h-4 mr-2" /> Try another resume
              </button>
              
              <div className="grid md:grid-cols-[1fr_300px] gap-8">
                <div>
                  <div className="bg-card border border-border shadow-sm p-6 rounded-2xl mb-8 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-5 transform translate-x-4 -translate-y-4 group-hover:scale-110 transition-transform">
                      <Skull className="w-24 h-24 text-foreground" />
                    </div>
                    <h3 className="text-destructive font-bold uppercase tracking-wider text-xs mb-3">The Brutal Truth</h3>
                    <p className="text-lg md:text-xl leading-relaxed text-foreground opacity-90 font-medium relative z-10">"{roastData.brutal_roast}"</p>
                  </div>

                  <div className="grid sm:grid-cols-2 gap-6">
                    <div className="bg-destructive/10 border border-destructive/20 p-5 rounded-2xl">
                      <h4 className="flex items-center text-destructive font-bold mb-4">
                        <AlertTriangle className="w-5 h-5 mr-2" /> Red Flags
                      </h4>
                      <ul className="space-y-3">
                        {roastData.weaknesses.map((w, i) => (
                          <li key={i} className="text-sm text-foreground/80 flex items-start">
                            <span className="mr-2 mt-0.5 text-destructive">•</span> {w}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-success/10 border border-success/20 p-5 rounded-2xl">
                      <h4 className="flex items-center text-success font-bold mb-4">
                        <CheckCircle2 className="w-5 h-5 mr-2" /> Saving Graces
                      </h4>
                      <ul className="space-y-3">
                        {roastData.strengths.map((s, i) => (
                          <li key={i} className="text-sm text-foreground/80 flex items-start">
                            <span className="mr-2 mt-0.5 text-success">•</span> {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                <div>
                  <div className="bg-card border border-border shadow-sm p-6 rounded-2xl text-center sticky top-6">
                    <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground mb-4">Resume Score</p>
                    <div className="relative inline-flex items-center justify-center mb-2">
                       <svg className="w-32 h-32 transform -rotate-90">
                          <circle cx="64" cy="64" r="60" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-border" />
                          <circle cx="64" cy="64" r="60" stroke="currentColor" strokeWidth="8" fill="transparent" 
                            strokeDasharray={2 * Math.PI * 60}
                            strokeDashoffset={(2 * Math.PI * 60) - ((roastData.score / 10) * (2 * Math.PI * 60))}
                            className={roastData.score < 5 ? "text-destructive" : roastData.score < 7 ? "text-warning" : "text-success"} 
                            strokeLinecap="round" />
                       </svg>
                       <span className="absolute text-4xl font-extrabold text-foreground">{roastData.score}<span className="text-lg text-muted-foreground">/10</span></span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-4">
                      {roastData.score < 5 ? "Yikes. Burn it and start over." : roastData.score < 7 ? "Needs some serious medical attention." : "Not bad, but don't get cocky."}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
