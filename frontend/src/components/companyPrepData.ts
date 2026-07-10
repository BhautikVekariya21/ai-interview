export interface CompanyRound {
  name: string;
  duration: string;
  description: string;
}

export interface CompanyProfile {
  id: string;
  name: string;
  logo: string; // emoji as placeholder
  tagline: string;
  color: string; // brand HSL
  interviewRounds: CompanyRound[];
  cultureValues: string[];
  questionThemes: string[];
  interviewerStyle: string;
  tipsToStandOut: string[];
  salaryRange: { role: string; range: string }[];
  readingList: { title: string; url: string }[];
  difficultyRating: {
    technical: number; // 1-10
    behavioral: number;
    systemDesign: number;
    overall: number;
  };
}

export const COMPANY_PROFILES: CompanyProfile[] = [
  {
    id: "meta",
    name: "Meta",
    logo: "Ⓜ",
    tagline: "Move fast. Focus on impact.",
    color: "221 83% 53%",
    interviewRounds: [
      { name: "Recruiter Screen", duration: "30 min", description: "Behavioral overview, role fit, and timeline expectations." },
      { name: "Technical Phone Screen", duration: "45 min", description: "One coding problem on CoderPad. Focus on clean code, optimal solution, and communication." },
      { name: "Onsite — Coding (×2)", duration: "45 min each", description: "Two back-to-back coding rounds. Algorithmic problems, data structure mastery, optimal time/space." },
      { name: "Onsite — System Design", duration: "45 min", description: "Design a large-scale system. Drive the conversation. Discuss trade-offs proactively." },
      { name: "Onsite — Behavioral (Jedi)", duration: "45 min", description: "Deep dive into past projects, conflict resolution, leadership, and collaboration." },
    ],
    cultureValues: [
      "Move Fast — Ship quickly, iterate rapidly",
      "Be Bold — Take smart risks",
      "Focus on Impact — Prioritize work that creates the most value",
      "Be Open — Communicate transparently",
      "Build Social Value — Think about community impact",
    ],
    questionThemes: [
      "Graph problems (social network connections)",
      "String manipulation and parsing",
      "Dynamic programming",
      "Search and ranking algorithms",
      "Rate limiting and content moderation systems",
    ],
    interviewerStyle:
      "Meta interviewers want to see you think out loud. They value communication as much as the solution. Expect interviewers to give hints if you're stuck — take them gracefully. They use a structured rubric: problem solving, coding quality, communication, and verification.",
    tipsToStandOut: [
      "Always clarify the problem before coding — ask about edge cases",
      "Write clean, production-quality code (good naming, modular functions)",
      "Discuss time and space complexity proactively after solving",
      "For system design, drive the conversation — don't wait to be asked",
      "In behavioral rounds, use the STAR method and quantify your impact",
    ],
    salaryRange: [
      { role: "E4 (Mid-level)", range: "$180K – $280K TC" },
      { role: "E5 (Senior)", range: "$300K – $500K TC" },
      { role: "E6 (Staff)", range: "$450K – $700K TC" },
    ],
    readingList: [
      { title: "Meta Interview Prep Guide (official)", url: "https://www.metacareers.com/swe-prep-onsite/" },
      { title: "Blind 75 LeetCode List", url: "https://leetcode.com/discuss/general-discussion/460599" },
      { title: "Grokking the System Design Interview", url: "https://www.designgurus.io/course/grokking-the-system-design-interview" },
    ],
    difficultyRating: { technical: 8, behavioral: 7, systemDesign: 8, overall: 8 },
  },
  {
    id: "apple",
    name: "Apple",
    logo: "",
    tagline: "Think different. Ship quality.",
    color: "0 0% 20%",
    interviewRounds: [
      { name: "Recruiter Screen", duration: "30 min", description: "Background review, role alignment, salary expectations." },
      { name: "Technical Phone Screen", duration: "60 min", description: "Coding problem + technical discussion. Often domain-specific (iOS, ML, systems)." },
      { name: "Onsite — Coding (×2-3)", duration: "45-60 min each", description: "Multiple coding rounds. Problems can be very domain-specific. Expect pair programming style." },
      { name: "Onsite — System Design", duration: "60 min", description: "Design a system relevant to the team you're joining. Depth over breadth." },
      { name: "Onsite — Domain Deep Dive", duration: "60 min", description: "Deep technical discussion about your area of expertise. Be ready to go very deep." },
      { name: "Hiring Manager Chat", duration: "30 min", description: "Culture fit, career goals, and team alignment." },
    ],
    cultureValues: [
      "Attention to Detail — Quality over quantity, always",
      "Secrecy & Focus — Work stealth, ship polished",
      "User Experience First — Every pixel matters",
      "Cross-functional Collaboration — Work across teams seamlessly",
      "Innovation Through Simplicity — Elegant solutions > complex ones",
    ],
    questionThemes: [
      "Domain-specific problems (iOS, macOS, hardware-software integration)",
      "Concurrency and multi-threading",
      "Memory management and performance optimization",
      "Object-oriented design patterns",
      "Real-time systems and low-latency computing",
    ],
    interviewerStyle:
      "Apple interviews are the most team-specific. Each team runs its own process. Expect interviewers who are deeply technical in their domain. They value depth of knowledge over breadth. Interviews can feel like a conversation between peers rather than a quiz.",
    tipsToStandOut: [
      "Research the specific team and product you're interviewing for",
      "Be ready to go very deep in your domain (don't just surface-level)",
      "Show passion for user experience and product polish",
      "Demonstrate attention to detail in your code and designs",
      "Be prepared to discuss patents or novel technical approaches",
    ],
    salaryRange: [
      { role: "ICT3 (Mid-level)", range: "$170K – $260K TC" },
      { role: "ICT4 (Senior)", range: "$280K – $440K TC" },
      { role: "ICT5 (Staff)", range: "$400K – $650K TC" },
    ],
    readingList: [
      { title: "Apple Software Engineering Roles", url: "https://www.apple.com/careers/us/software-and-services.html" },
      { title: "iOS Interview Questions (Ray Wenderlich)", url: "https://www.kodeco.com/" },
      { title: "WWDC Session Videos (free)", url: "https://developer.apple.com/videos/" },
    ],
    difficultyRating: { technical: 9, behavioral: 6, systemDesign: 7, overall: 8 },
  },
  {
    id: "amazon",
    name: "Amazon",
    logo: "📦",
    tagline: "Customer obsession. Day 1 mentality.",
    color: "33 100% 50%",
    interviewRounds: [
      { name: "Online Assessment (OA)", duration: "90 min", description: "2 coding problems + work style assessment survey." },
      { name: "Phone Screen", duration: "60 min", description: "One coding problem + one Leadership Principle behavioral question." },
      { name: "Onsite — Loop (×4-5)", duration: "55 min each", description: "Each round has 1 LP behavioral question (~20 min) + 1 technical question (~35 min). One interviewer is the Bar Raiser." },
    ],
    cultureValues: [
      "Customer Obsession — Start with the customer and work backwards",
      "Ownership — Think long-term, never say 'that's not my job'",
      "Invent and Simplify — Find new ways to simplify",
      "Are Right, A Lot — Have strong judgment and good instincts",
      "Learn and Be Curious — Never stop learning",
      "Hire and Develop the Best — Raise the performance bar",
      "Insist on the Highest Standards — Continually raise the bar",
      "Think Big — Create bold directions that inspire results",
      "Bias for Action — Speed matters, take calculated risks",
      "Dive Deep — Stay connected to details, audit frequently",
    ],
    questionThemes: [
      "BFS/DFS on grids and trees",
      "Dynamic programming (optimization, counting)",
      "Greedy algorithms",
      "OOP design (parking lot, library system)",
      "Concurrency and distributed systems",
    ],
    interviewerStyle:
      "Amazon is unique because every round mixes behavioral + technical. Interviewers are trained to probe deeply using the STAR method. The Bar Raiser has veto power and specifically looks for LP alignment. They assess 'Would I want this person on my team?' and 'Is this person raising the bar?'",
    tipsToStandOut: [
      "Prepare 2-3 STAR stories per Leadership Principle (focus on top 6 LPs)",
      "Always quantify impact in behavioral answers (%, $, time saved)",
      "For coding, optimize your solution and discuss trade-offs",
      "Show 'Ownership' — describe situations where you went beyond your role",
      "The Bar Raiser is key — be genuine, not rehearsed",
    ],
    salaryRange: [
      { role: "SDE II", range: "$160K – $320K TC" },
      { role: "SDE III (Senior)", range: "$250K – $500K TC" },
      { role: "Principal", range: "$400K – $800K TC" },
    ],
    readingList: [
      { title: "Amazon Leadership Principles", url: "https://www.amazon.jobs/en/principles" },
      { title: "Amazon Bar Raiser Process Explained", url: "https://www.aboutamazon.com/news/workplace/amazon-bar-raiser" },
      { title: "Day 1 Letter by Jeff Bezos", url: "https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders" },
    ],
    difficultyRating: { technical: 7, behavioral: 9, systemDesign: 7, overall: 8 },
  },
  {
    id: "netflix",
    name: "Netflix",
    logo: "🎬",
    tagline: "Freedom & Responsibility. Stunning colleagues.",
    color: "0 72% 51%",
    interviewRounds: [
      { name: "Recruiter Screen", duration: "45 min", description: "Deep culture fit assessment. They take Netflix culture extremely seriously." },
      { name: "Hiring Manager Screen", duration: "60 min", description: "Technical depth + team fit. Discuss past work in detail." },
      { name: "Onsite — Technical (×2-3)", duration: "60 min each", description: "System design + coding. Problems are often real Netflix challenges. Open-ended and discussion-heavy." },
      { name: "Onsite — Cross-functional", duration: "60 min", description: "Work with stakeholders from other teams. Assess collaboration and influence." },
      { name: "Onsite — Culture", duration: "60 min", description: "Deep dive into Netflix culture values. Expect challenging hypotheticals." },
    ],
    cultureValues: [
      "Judgment — Make wise decisions despite ambiguity",
      "Communication — Be concise, articulate, and listen well",
      "Curiosity — Learn rapidly, seek to understand strategy",
      "Courage — Question actions inconsistent with values",
      "Selflessness — Seek what's best for Netflix, not yourself",
      "Innovation — Re-conceptualize issues, challenge assumptions",
      "Inclusion — Collaborate effectively with diverse teams",
      "Integrity — Be candid, transparent, and non-political",
      "Impact — Accomplish amazing amounts of important work",
    ],
    questionThemes: [
      "Distributed systems and microservices",
      "Streaming and content delivery optimization",
      "A/B testing and experimentation platforms",
      "Recommendation and personalization systems",
      "Chaos engineering and resilience",
    ],
    interviewerStyle:
      "Netflix doesn't do LeetCode-style coding. They focus on real-world engineering discussions, system design, and past experience. Interviews feel like peer conversations. They want senior engineers who can operate independently with minimal oversight. The culture interview is uniquely intense.",
    tipsToStandOut: [
      "Read the Netflix Culture Deck thoroughly — it's the most important prep",
      "Be ready to discuss trade-offs in your past architectural decisions",
      "Show independence and strong opinions (loosely held)",
      "Demonstrate 'stunning colleague' qualities — helpful, passionate, honest",
      "For system design, think about scale (200M+ subscribers) and reliability",
    ],
    salaryRange: [
      { role: "Senior SWE", range: "$350K – $600K TC (all-cash)" },
      { role: "Staff SWE", range: "$500K – $800K TC (all-cash)" },
      { role: "Principal", range: "$700K – $1M+ TC (all-cash)" },
    ],
    readingList: [
      { title: "Netflix Culture Deck", url: "https://jobs.netflix.com/culture" },
      { title: "Netflix Tech Blog", url: "https://netflixtechblog.com/" },
      { title: "No Rules Rules (book by Reed Hastings)", url: "https://www.norulesrules.com/" },
    ],
    difficultyRating: { technical: 8, behavioral: 9, systemDesign: 9, overall: 9 },
  },
  {
    id: "google",
    name: "Google",
    logo: "🔍",
    tagline: "Organize the world's information.",
    color: "142 72% 45%",
    interviewRounds: [
      { name: "Recruiter Screen", duration: "30 min", description: "Background review, role matching, process overview." },
      { name: "Technical Phone Screens (×1-2)", duration: "45 min each", description: "Coding problems on Google Docs. Communication and problem-solving process matter as much as the answer." },
      { name: "Onsite — Coding (×2-3)", duration: "45 min each", description: "Algorithm-heavy problems. Emphasis on optimal solutions and demonstrating strong CS fundamentals." },
      { name: "Onsite — System Design", duration: "45 min", description: "Design a Google-scale system. They want to see you handle ambiguity and make clear trade-offs." },
      { name: "Onsite — Googleyness & Leadership", duration: "45 min", description: "Behavioral round focused on collaboration, ambiguity handling, and pushing back respectfully." },
      { name: "Hiring Committee Review", duration: "N/A", description: "Packet reviewed by a hiring committee you never meet. Feedback from all interviewers is aggregated." },
    ],
    cultureValues: [
      "Focus on the user — Everything starts with the user experience",
      "Think 10x — Aim for 10x improvement, not 10%",
      "Launch and iterate — Ship fast, get feedback, improve",
      "Share everything — Default to open, share context widely",
      "Use data — Make decisions based on data, not opinions",
      "Do the right thing — Don't be evil. Act ethically.",
    ],
    questionThemes: [
      "Algorithmic complexity (optimal solutions expected)",
      "Graph algorithms (BFS, DFS, shortest paths)",
      "Dynamic programming (multi-dimensional)",
      "String/array manipulation at scale",
      "Designing for Google scale (billions of users, petabytes of data)",
    ],
    interviewerStyle:
      "Google interviewers are trained evaluators using a structured rubric: coding, algorithms, data structures, communication, and analytical ability. They expect you to explore multiple approaches and choose the optimal one with justification. They value the journey to the solution as much as the answer.",
    tipsToStandOut: [
      "Practice coding on Google Docs (no autocomplete, no syntax highlighting)",
      "Always start with brute force, then optimize — explain why each approach is better",
      "For system design, show awareness of Google's stack (Bigtable, Spanner, MapReduce)",
      "Demonstrate 'Googleyness' — intellectual humility, collaborative problem-solving",
      "The hiring committee reviews all feedback — every round matters equally",
    ],
    salaryRange: [
      { role: "L4 (Mid-level)", range: "$180K – $320K TC" },
      { role: "L5 (Senior)", range: "$300K – $500K TC" },
      { role: "L6 (Staff)", range: "$450K – $800K TC" },
    ],
    readingList: [
      { title: "Google Careers Interview Tips", url: "https://careers.google.com/how-we-hire/" },
      { title: "Cracking the Coding Interview", url: "https://www.crackingthecodinginterview.com/" },
      { title: "Google SRE Book (free)", url: "https://sre.google/sre-book/table-of-contents/" },
    ],
    difficultyRating: { technical: 9, behavioral: 6, systemDesign: 9, overall: 9 },
  },
  {
    id: "microsoft",
    name: "Microsoft",
    logo: "🪟",
    tagline: "Empower every person and organization.",
    color: "207 90% 45%",
    interviewRounds: [
      { name: "Recruiter Screen", duration: "30 min", description: "Background review, role overview, salary expectations." },
      { name: "Technical Phone Screen", duration: "45-60 min", description: "One coding problem. Often medium difficulty. Clear communication expected." },
      { name: "Onsite — Loop (×4-5)", duration: "45-60 min each", description: "Mix of coding, system design, and behavioral. One round is typically with the hiring manager ('as-appropriate' interview)." },
      { name: "As-Appropriate (AA) Interview", duration: "45 min", description: "Senior hiring manager makes the final call. Mix of technical and behavioral. Often the deciding interview." },
    ],
    cultureValues: [
      "Growth Mindset — Learn from failures, embrace challenges",
      "Customer Obsessed — Deeply understand customer needs",
      "Diverse and Inclusive — Every voice matters",
      "One Microsoft — Work across boundaries, collaborate",
      "Making a Difference — Technology for social good",
    ],
    questionThemes: [
      "Object-oriented design (design an elevator, design a file system)",
      "System design with Azure/cloud components",
      "Data structures (trees, graphs, hash maps)",
      "Behavioral questions focused on growth mindset",
      "Concurrency and thread safety",
    ],
    interviewerStyle:
      "Microsoft interviews are collaborative. Interviewers often guide you through the problem. They want to see your thought process and how you handle ambiguity. The 'as-appropriate' interview with the hiring manager is the most important — they make the final hire/no-hire decision.",
    tipsToStandOut: [
      "Show a 'growth mindset' — talk about learning from failures",
      "Be collaborative — treat the interview as pair programming",
      "For the AA interview, prepare your strongest project story",
      "Understand the product you're interviewing for (Azure, Teams, Windows, etc.)",
      "Ask thoughtful questions about the team's technical challenges",
    ],
    salaryRange: [
      { role: "SDE II (62)", range: "$160K – $260K TC" },
      { role: "Senior SDE (63)", range: "$220K – $380K TC" },
      { role: "Principal (64+)", range: "$350K – $600K TC" },
    ],
    readingList: [
      { title: "Microsoft Careers – Interview Tips", url: "https://careers.microsoft.com/v2/global/en/hiring-tips" },
      { title: "Hit Refresh by Satya Nadella", url: "https://news.microsoft.com/hitrefresh/" },
      { title: "Azure Architecture Center", url: "https://learn.microsoft.com/en-us/azure/architecture/" },
    ],
    difficultyRating: { technical: 7, behavioral: 7, systemDesign: 7, overall: 7 },
  },
];
