import { useState, useEffect } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import { Flame, Code2, Server, MessageSquare, CheckCircle, ChevronRight, Trophy, Zap, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CODING_PROBLEMS } from "./codingProblemsData";
import { toast } from "sonner";
import confetti from "canvas-confetti";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { evaluateAnswer, executeCodingSolution, fetchDailyStreak, completeDailyChallenge, undoDailyChallenge } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

interface Challenge {
  id: string;
  type: "dsa" | "system" | "behavioral";
  title: string;
  description: string;
  fullDescription: string;
  difficulty?: string;
  starterCode?: string;
  completed: boolean;
}

const convertJsToPythonStarter = (jsCode?: string) => {
  if (!jsCode) return "";
  const match = jsCode.match(/function\s+(\w+)\s*\(([^)]*)\)/);
  if (match) {
    const name = match[1];
    const args = match[2].split(',').map(arg => arg.trim()).join(', ');
    return `def ${name}(${args}):\n    # Your code here\n    pass`;
  }
  return "# Your code here\n";
};

export default function DailyChallengePage() {
  const { isAuthenticated } = useAuth();
  const [streak, setStreak] = useState(0);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [lastCompletedDate, setLastCompletedDate] = useState<string | null>(null);
  
  const [solvingChallenge, setSolvingChallenge] = useState<Challenge | null>(null);
  const [answer, setAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Generate deterministic daily challenges based on today's date
    const today = new Date().toISOString().split("T")[0];
    const seed = today.split("-").reduce((a, b) => a + parseInt(b), 0);
    
    // Pick daily DSA problem (Hard problems for complexity)
    const hardProblems = CODING_PROBLEMS.filter(p => p.difficulty === "Hard");
    const dsaProblem = hardProblems[seed % hardProblems.length] || CODING_PROBLEMS[seed % CODING_PROBLEMS.length];
    
    // Pick daily System Design
    const sysDesignOptions = [
      { id: "sd-1", title: "Design Twitter", desc: "Design a high-scale microblogging platform with a timeline feed." },
      { id: "sd-2", title: "Design an URL Shortener", desc: "Design a service like Bitly that handles millions of redirects per minute." },
      { id: "sd-3", title: "Design Netflix", desc: "Design a global video streaming platform with high availability." },
      { id: "sd-4", title: "Design Uber", desc: "Design a ride-sharing service handling real-time driver-rider matching." },
    ];
    const sdProblem = sysDesignOptions[seed % sysDesignOptions.length];

    // Pick daily Behavioral
    const behavioralOptions = [
      { id: "bh-1", title: "Handling Conflict", desc: "Tell me about a time you had a major disagreement with a coworker. How did you resolve it?" },
      { id: "bh-2", title: "Failing Forward", desc: "Describe a project that completely failed. What went wrong and what did you learn?" },
      { id: "bh-3", title: "Going Above and Beyond", desc: "Tell me about a time you exceeded expectations to deliver a project." },
      { id: "bh-4", title: "Leadership Under Pressure", desc: "Describe a time you had to step up as a leader in a crisis." },
    ];
    const bhProblem = behavioralOptions[seed % behavioralOptions.length];

    // Load state from local storage
    const savedStateStr = localStorage.getItem("daily_challenge_state");
    const savedState = savedStateStr ? JSON.parse(savedStateStr) : { date: today, streak: 0, completedIds: [] };

    let currentStreak = savedState.streak || 0;
    
    // Check if missed a day
    if (savedState.date !== today) {
      const lastDate = new Date(savedState.date);
      const currDate = new Date(today);
      const diffTime = Math.abs(currDate.getTime() - lastDate.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays > 1) {
        currentStreak = 0; // Lost streak
      }
    }

    setStreak(currentStreak);
    setLastCompletedDate(savedState.lastCompletedDate || null);

    const generatedChallenges: Challenge[] = [
      {
        id: "dsa-" + dsaProblem.id,
        type: "dsa",
        title: dsaProblem.title,
        description: dsaProblem.description.replace(/\*\*/g, "").substring(0, 100) + "...",
        fullDescription: dsaProblem.description.replace(/\*\*/g, ""),
        difficulty: dsaProblem.difficulty,
        starterCode: convertJsToPythonStarter(dsaProblem.starterCode),
        completed: savedState.date === today && savedState.completedIds.includes("dsa-" + dsaProblem.id),
      },
      {
        id: sdProblem.id,
        type: "system",
        title: sdProblem.title,
        description: sdProblem.desc,
        fullDescription: sdProblem.desc,
        completed: savedState.date === today && savedState.completedIds.includes(sdProblem.id),
      },
      {
        id: bhProblem.id,
        type: "behavioral",
        title: bhProblem.title,
        description: bhProblem.desc,
        fullDescription: bhProblem.desc,
        completed: savedState.date === today && savedState.completedIds.includes(bhProblem.id),
      }
    ];
    setChallenges(generatedChallenges);

    // Sync from server for authenticated users
    if (isAuthenticated) {
      fetchDailyStreak().then(serverData => {
        if (serverData.streak > 0) setStreak(serverData.streak);
        if (serverData.last_completed_date) setLastCompletedDate(serverData.last_completed_date);
        if (serverData.today_completed_ids.length > 0) {
          setChallenges(prev => prev.map(c => ({
            ...c,
            completed: serverData.today_completed_ids.includes(c.id) || c.completed,
          })));
        }
      }).catch(() => { /* use localStorage fallback */ });
    }
  }, []);

  const saveProgress = (newChallenges: Challenge[], newStreak: number, isFullyComplete: boolean) => {
    const today = new Date().toISOString().split("T")[0];
    const completedIds = newChallenges.filter(c => c.completed).map(c => c.id);
    
    localStorage.setItem("daily_challenge_state", JSON.stringify({
      date: today,
      streak: newStreak,
      completedIds,
      lastCompletedDate: isFullyComplete ? today : lastCompletedDate
    }));
  };

  const toggleComplete = (id: string) => {
    setChallenges(prev => {
      const wasCompleted = prev.find(c => c.id === id)?.completed;
      const next = prev.map(c => c.id === id ? { ...c, completed: !c.completed } : c);
      const allDone = next.every(c => c.completed);
      const previouslyDone = prev.every(c => c.completed);
      
      let nextStreak = streak;
      const today = new Date().toISOString().split("T")[0];

      if (allDone && !previouslyDone && lastCompletedDate !== today) {
        nextStreak += 1;
        setStreak(nextStreak);
        setLastCompletedDate(today);
        triggerConfetti();
        toast.success(`Daily Challenge Complete! Streak: ${nextStreak} \uD83D\uDD25`);
      } else if (!allDone && previouslyDone && lastCompletedDate === today) {
        nextStreak = Math.max(0, nextStreak - 1);
        setStreak(nextStreak);
        setLastCompletedDate(null);
      }

      saveProgress(next, nextStreak, allDone);

      // Sync with server for authenticated users
      if (isAuthenticated) {
        if (!wasCompleted) {
          completeDailyChallenge(id).then(res => {
            setStreak(res.streak);
          }).catch(() => {});
        } else {
          undoDailyChallenge(id).then(res => {
            setStreak(res.streak);
          }).catch(() => {});
        }
      }

      return next;
    });
  };

  const triggerConfetti = () => {
    const count = 200;
    const defaults = { origin: { y: 0.7 } };

    function fire(particleRatio: number, opts: any) {
      confetti({ ...defaults, ...opts, particleCount: Math.floor(count * particleRatio) });
    }

    fire(0.25, { spread: 26, startVelocity: 55 });
    fire(0.2, { spread: 60 });
    fire(0.35, { spread: 100, decay: 0.91, scalar: 0.8 });
    fire(0.1, { spread: 120, startVelocity: 25, decay: 0.92, scalar: 1.2 });
    fire(0.1, { spread: 120, startVelocity: 45 });
  };

  const submitAnswer = async () => {
    if (solvingChallenge) {
      if (!answer.trim()) {
        toast.error("Please provide an answer first!");
        return;
      }
      
      setIsSubmitting(true);
      try {
        if (solvingChallenge.type === 'dsa') {
          const originalProblemId = parseInt(solvingChallenge.id.replace("dsa-", ""), 10);
          const execResult = await executeCodingSolution(originalProblemId, {
            code: answer,
            language: "python"
          });
          
          if (execResult.success && execResult.all_passed) {
            toggleComplete(solvingChallenge.id);
            setSolvingChallenge(null);
            setAnswer("");
            toast.success(`All ${execResult.passed_tests}/${execResult.total_tests} test cases passed! ✨`);
          } else {
            toast.error(execResult.error || `Passed ${execResult.passed_tests}/${execResult.total_tests} tests. Keep trying!`);
          }
        } else {
          const result = await evaluateAnswer({
            session_id: "daily_challenge_" + Date.now(),
            question_id: solvingChallenge.id,
            question_number: 1,
            question_text: solvingChallenge.fullDescription,
            question_category: solvingChallenge.type,
            answer_text: answer
          });

          if (result.score >= 50) {
            toggleComplete(solvingChallenge.id);
            setSolvingChallenge(null);
            setAnswer("");
            toast.success(`Solution evaluated! Score: ${result.score}/100 ✨`);
          } else {
            toast.error(`Score: ${result.score}/100 - ${result.feedback || "Your answer needs more detail."}`);
          }
        }
      } catch (error) {
        toast.error("Failed to evaluate answer. Please try again.");
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  const allCompleted = challenges.length > 0 && challenges.every(c => c.completed);
  const completedCount = challenges.filter(c => c.completed).length;

  return (
    <div className="w-full max-w-[1200px] mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* Header Section */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary/10 via-background to-accent/10 border border-primary/20 shadow-lg px-8 py-10 md:py-14 text-center">
        <div className="absolute top-0 right-0 p-8 opacity-10">
          <Trophy className="w-48 h-48 text-primary" />
        </div>
        
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="relative z-10 flex flex-col items-center gap-4"
        >
          <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-primary text-primary-foreground shadow-xl shadow-primary/20 mb-2">
            <Flame className="w-8 h-8" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight text-foreground bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
            Daily Challenge
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Commit to your interview preparation. Complete 3 challenges every day to build your streak and stay interview-ready.
          </p>

          <div className="flex items-center gap-4 mt-6">
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-background border border-border shadow-sm">
              <Flame className={allCompleted ? "text-primary animate-pulse w-5 h-5" : "text-muted-foreground w-5 h-5"} />
              <span className="font-bold text-foreground">{streak} Day Streak</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-background border border-border shadow-sm">
              <CheckCircle className="text-primary w-5 h-5" />
              <span className="font-bold text-foreground">{completedCount}/3 Done</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Challenges Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AnimatePresence>
          {challenges.map((challenge, i) => {
            const icons = {
              dsa: <Code2 className="w-6 h-6 text-foreground" />,
              system: <Server className="w-6 h-6 text-foreground" />,
              behavioral: <MessageSquare className="w-6 h-6 text-foreground" />
            };

            const colors = {
              dsa: "from-primary/5 to-transparent border-border hover:border-primary/30",
              system: "from-accent/40 to-transparent border-border hover:border-primary/30",
              behavioral: "from-muted/60 to-transparent border-border hover:border-primary/30",
            };

            return (
              <motion.div
                key={challenge.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`relative flex flex-col group rounded-3xl border bg-gradient-to-br ${colors[challenge.type]} p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl`}
              >
                {/* Completed Overlay */}
                {challenge.completed && (
                  <div className="absolute inset-0 z-10 bg-background/40 backdrop-blur-[2px] rounded-3xl flex items-center justify-center transition-all">
                    <motion.div 
                      initial={{ scale: 0 }} 
                      animate={{ scale: 1 }} 
                      className="bg-primary text-primary-foreground rounded-full p-4 shadow-2xl flex flex-col items-center gap-2"
                    >
                      <CheckCircle className="w-8 h-8" />
                      <span className="text-xs font-bold uppercase tracking-widest">Completed</span>
                    </motion.div>
                  </div>
                )}

                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 rounded-2xl bg-background/80 shadow-sm border border-border backdrop-blur-sm">
                    {icons[challenge.type]}
                  </div>
                  {challenge.difficulty && (
                    <span className="text-xs font-bold px-3 py-1 rounded-full bg-muted/50 border border-border text-foreground shadow-sm">
                      {challenge.difficulty}
                    </span>
                  )}
                </div>

                <h3 className="text-xl font-bold tracking-tight text-foreground mb-2">{challenge.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed flex-1 mb-6">
                  {challenge.description}
                </p>

                <div className="flex items-center gap-3 mt-auto">
                  {!challenge.completed ? (
                    <Button 
                      onClick={() => { setSolvingChallenge(challenge); setAnswer(challenge.type === 'dsa' && challenge.starterCode ? challenge.starterCode : ""); }}
                      className="flex-1 font-bold shadow-sm bg-foreground text-background hover:bg-foreground/90 hover:scale-[1.02] transition-all"
                    >
                      Solve Challenge
                    </Button>
                  ) : (
                    <Button 
                      variant="outline"
                      onClick={() => toggleComplete(challenge.id)}
                      className="flex-1 font-bold shadow-sm"
                    >
                      Undo Completion
                    </Button>
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {allCompleted && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-3xl border border-primary/20 bg-primary/5 p-8 text-center"
        >
          <div className="inline-flex justify-center items-center w-16 h-16 rounded-full bg-primary/10 text-primary mb-4">
            <Star className="w-8 h-8 fill-primary text-primary" />
          </div>
          <h2 className="text-2xl font-black text-foreground mb-2">Incredible Work!</h2>
          <p className="text-muted-foreground">You've completed all daily challenges. Come back tomorrow for a new set of questions!</p>
        </motion.div>
      )}

      {/* Solve Modal */}
      <Dialog open={!!solvingChallenge} onOpenChange={(open) => !open && setSolvingChallenge(null)}>
        <DialogContent className="sm:max-w-[700px] max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl pt-2">{solvingChallenge?.title}</DialogTitle>
          </DialogHeader>
          <div className="py-2">
            <div className="p-4 rounded-xl bg-muted/30 border border-border mb-4">
              <p className="text-sm font-medium text-foreground whitespace-pre-wrap leading-relaxed">
                {solvingChallenge?.fullDescription}
              </p>
            </div>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Draft your solution, pseudo-code, or bullet points here..."
              className={`w-full h-48 p-4 rounded-xl border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y shadow-sm ${solvingChallenge?.type === 'dsa' ? 'font-mono text-sm' : 'font-sans'}`}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSolvingChallenge(null)}>Cancel</Button>
            <Button onClick={submitAnswer} className="font-bold" disabled={isSubmitting}>
              {isSubmitting ? "Evaluating..." : "Submit Solution"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
}
