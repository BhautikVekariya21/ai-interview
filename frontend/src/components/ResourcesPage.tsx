import { useState, useMemo } from "react";
import EXTRA_RESOURCES from "./resourcesData";
import { m as motion } from "framer-motion";
import {
  BookOpen,
  ExternalLink,
  Github,
  Youtube,
  FileText,
  GraduationCap,
  Code2,
  Database,
  Cloud,
  Brain,
  Shield,
  Layers,
  Search,
  Filter,
  BarChart3,
  TableProperties,
  Smartphone,
  Hexagon,
  Gem,
  Cpu,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

type ResourceCategory =
  | "all"
  | "ai-ml"
  | "data-science"
  | "sql"
  | "frontend"
  | "backend"
  | "devops"
  | "databases"
  | "system-design"
  | "security"
  | "mobile"
  | "cloud"
  | "dart"
  | "kotlin"
  | "rust";

type ResourceType = "case-study" | "ebook" | "github" | "playlist" | "course";

interface Resource {
  title: string;
  description: string;
  url: string;
  type: ResourceType;
  category: ResourceCategory;
  source: string;
  tags: string[];
}

/* ------------------------------------------------------------------ */
/*  Category config                                                    */
/* ------------------------------------------------------------------ */

const CATEGORIES: {
  id: ResourceCategory;
  label: string;
  icon: React.ReactNode;
}[] = [
  { id: "all", label: "All", icon: <Layers className="w-3.5 h-3.5" /> },
  { id: "ai-ml", label: "AI / ML", icon: <Brain className="w-3.5 h-3.5" /> },
  { id: "data-science", label: "Data Science", icon: <BarChart3 className="w-3.5 h-3.5" /> },
  { id: "sql", label: "SQL", icon: <TableProperties className="w-3.5 h-3.5" /> },
  { id: "frontend", label: "Frontend", icon: <Code2 className="w-3.5 h-3.5" /> },
  { id: "backend", label: "Backend", icon: <Layers className="w-3.5 h-3.5" /> },
  { id: "devops", label: "DevOps", icon: <Cloud className="w-3.5 h-3.5" /> },
  { id: "databases", label: "Databases", icon: <Database className="w-3.5 h-3.5" /> },
  { id: "system-design", label: "System Design", icon: <Layers className="w-3.5 h-3.5" /> },
  { id: "security", label: "Security", icon: <Shield className="w-3.5 h-3.5" /> },
  { id: "mobile", label: "Mobile", icon: <Smartphone className="w-3.5 h-3.5" /> },
  { id: "cloud", label: "Cloud", icon: <Cloud className="w-3.5 h-3.5" /> },
  { id: "dart", label: "Dart / Flutter", icon: <Hexagon className="w-3.5 h-3.5" /> },
  { id: "kotlin", label: "Kotlin", icon: <Gem className="w-3.5 h-3.5" /> },
  { id: "rust", label: "Rust", icon: <Cpu className="w-3.5 h-3.5" /> },
];

/* ------------------------------------------------------------------ */
/*  Type badge styling                                                 */
/* ------------------------------------------------------------------ */

const TYPE_META: Record<
  ResourceType,
  { label: string; icon: React.ReactNode; color: string }
> = {
  "case-study": {
    label: "Case Study",
    icon: <FileText className="w-3 h-3" />,
    color: "bg-warning/10 text-warning border-warning/20",
  },
  ebook: {
    label: "eBook / Paper",
    icon: <BookOpen className="w-3 h-3" />,
    color: "bg-info/10 text-info border-info/20",
  },
  github: {
    label: "GitHub Repo",
    icon: <Github className="w-3 h-3" />,
    color: "bg-brand/10 text-primary border-primary/20",
  },
  playlist: {
    label: "Video Playlist",
    icon: <Youtube className="w-3 h-3" />,
    color: "bg-destructive/10 text-destructive border-destructive/20",
  },
  course: {
    label: "Course",
    icon: <GraduationCap className="w-3 h-3" />,
    color: "bg-success/10 text-success border-success/20",
  },
};

/* ------------------------------------------------------------------ */
/*  Curated resource data                                              */
/* ------------------------------------------------------------------ */

const RESOURCES: Resource[] = [
  /* ==================  AI / ML  ================== */
  {
    title: "MIT 6.S191 — Introduction to Deep Learning",
    description:
      "MIT's official introductory course on deep learning. Covers foundations of neural networks, CNNs, RNNs, transformers, generative models, and reinforcement learning with hands-on TensorFlow labs.",
    url: "https://www.youtube.com/playlist?list=PLtBw6njQRU-rwp5__7C0oIVt26ZgjG9NI",
    type: "playlist",
    category: "ai-ml",
    source: "MIT",
    tags: ["Deep Learning", "Neural Networks", "TensorFlow"],
  },
  {
    title: "Stanford CS229 — Machine Learning",
    description:
      "Andrew Ng's legendary Stanford course. Rigorous treatment of supervised learning, unsupervised learning, SVMs, neural networks, and best practices for building ML systems.",
    url: "https://www.youtube.com/playlist?list=PLoROMvodv4rMiGQp3WXShtMGgzqpfVfbU",
    type: "playlist",
    category: "ai-ml",
    source: "Stanford",
    tags: ["Machine Learning", "Statistics", "Supervised Learning"],
  },
  {
    title: "Stanford CS224N — NLP with Deep Learning",
    description:
      "Comprehensive Stanford course on natural language processing with deep learning. Covers word vectors, RNNs, attention, transformers, pretraining, and modern LLM architectures.",
    url: "https://www.youtube.com/playlist?list=PLoROMvodv4rMFqRtEuo6SGjY4XbRIVRd4",
    type: "playlist",
    category: "ai-ml",
    source: "Stanford",
    tags: ["NLP", "Transformers", "LLMs"],
  },
  {
    title: "Fast.ai — Practical Deep Learning for Coders",
    description:
      "A free, top-down course that teaches deep learning by building real projects first, then diving into theory. Covers computer vision, NLP, tabular data, and deployment.",
    url: "https://course.fast.ai/",
    type: "course",
    category: "ai-ml",
    source: "fast.ai",
    tags: ["PyTorch", "Practical", "Transfer Learning"],
  },
  {
    title: "Hugging Face Transformers",
    description:
      "State-of-the-art open-source library for NLP, vision, and audio models. Provides thousands of pretrained models and simple APIs for fine-tuning and inference.",
    url: "https://github.com/huggingface/transformers",
    type: "github",
    category: "ai-ml",
    source: "Hugging Face",
    tags: ["Transformers", "NLP", "Python"],
  },
  {
    title: "Papers With Code — ML State of the Art",
    description:
      "Tracks the latest ML research papers alongside their open-source implementations and benchmark results. Essential for staying current with SOTA methods.",
    url: "https://paperswithcode.com/",
    type: "case-study",
    category: "ai-ml",
    source: "Papers With Code",
    tags: ["Research", "Benchmarks", "SOTA"],
  },
  {
    title: "Dive into Deep Learning (D2L)",
    description:
      "An interactive open-source textbook with code, math, and discussion. Adopted by 500+ universities worldwide. Covers MLP, CNN, RNN, attention, optimization, and GANs.",
    url: "https://d2l.ai/",
    type: "ebook",
    category: "ai-ml",
    source: "D2L.ai",
    tags: ["Textbook", "PyTorch", "Interactive"],
  },

  /* ==================  Frontend  ================== */
  {
    title: "React Documentation — Official",
    description:
      "The new React docs with interactive examples. Covers components, hooks, state management, effects, refs, and advanced patterns like suspense and server components.",
    url: "https://react.dev/",
    type: "ebook",
    category: "frontend",
    source: "React Team",
    tags: ["React", "Hooks", "Components"],
  },
  {
    title: "Next.js by Vercel",
    description:
      "The React framework for the web. Full-stack features including server-side rendering, static generation, API routes, middleware, and the App Router architecture.",
    url: "https://github.com/vercel/next.js",
    type: "github",
    category: "frontend",
    source: "Vercel",
    tags: ["Next.js", "SSR", "React"],
  },
  {
    title: "Frontend Masters — Complete Intro to React v9",
    description:
      "Brian Holt's comprehensive React course covering modern React patterns, hooks, effects, context, portals, and real-world application architecture.",
    url: "https://frontendmasters.com/courses/complete-react-v9/",
    type: "course",
    category: "frontend",
    source: "Frontend Masters",
    tags: ["React", "JavaScript", "Hooks"],
  },
  {
    title: "TypeScript Handbook — Official",
    description:
      "The definitive guide to TypeScript from Microsoft. Covers type narrowing, generics, utility types, declaration files, and integrating TS into existing JS projects.",
    url: "https://www.typescriptlang.org/docs/handbook/",
    type: "ebook",
    category: "frontend",
    source: "Microsoft",
    tags: ["TypeScript", "Static Typing", "JavaScript"],
  },
  {
    title: "CSS for JS Developers — Josh Comeau",
    description:
      "An interactive course that teaches CSS through the lens of a JavaScript developer. Covers layout, positioning, responsive design, animations, and accessibility.",
    url: "https://css-for-js.dev/",
    type: "course",
    category: "frontend",
    source: "Josh Comeau",
    tags: ["CSS", "Layout", "Animation"],
  },
  {
    title: "Airbnb's Journey to React Server Components",
    description:
      "Detailed case study on how Airbnb incrementally adopted React Server Components at scale, the architectural challenges faced, and performance improvements achieved.",
    url: "https://medium.com/airbnb-engineering/a-deep-dive-into-airbnbs-server-driven-ui-system-842244c5f5",
    type: "case-study",
    category: "frontend",
    source: "Airbnb Engineering",
    tags: ["React", "Architecture", "Performance"],
  },

  /* ==================  Backend  ================== */
  {
    title: "MIT 6.824 — Distributed Systems",
    description:
      "MIT's graduate-level distributed systems course. Covers MapReduce, Raft consensus, fault tolerance, RPC, distributed transactions, and real-world system case studies.",
    url: "https://www.youtube.com/playlist?list=PLrw6a1wE39_tb2fErI4-WkMbsvGQk9_UB",
    type: "playlist",
    category: "backend",
    source: "MIT",
    tags: ["Distributed Systems", "Raft", "Consensus"],
  },
  {
    title: "FastAPI — Modern Python Web Framework",
    description:
      "High-performance Python web framework based on standard type hints. Automatic OpenAPI docs, async support, dependency injection, and built-in validation with Pydantic.",
    url: "https://github.com/tiangolo/fastapi",
    type: "github",
    category: "backend",
    source: "Sebastián Ramírez",
    tags: ["Python", "API", "Async"],
  },
  {
    title: "System Design Primer",
    description:
      "A comprehensive collection of system design topics for backend engineers. Covers scalability, caching, load balancing, databases, microservices, and real-world architectures.",
    url: "https://github.com/donnemartin/system-design-primer",
    type: "github",
    category: "backend",
    source: "Donne Martin",
    tags: ["System Design", "Scalability", "Architecture"],
  },
  {
    title: "Node.js Best Practices",
    description:
      "A curated list of top Node.js best practices covering project structure, error handling, testing, security, Docker, and production deployment. 90K+ stars.",
    url: "https://github.com/goldbergyoni/nodebestpractices",
    type: "github",
    category: "backend",
    source: "Yoni Goldberg",
    tags: ["Node.js", "Best Practices", "Production"],
  },
  {
    title: "Building Microservices — Sam Newman",
    description:
      "The definitive guide to designing fine-grained systems. Covers decomposition strategies, integration patterns, testing, deployment, and organizational aspects of microservices.",
    url: "https://www.oreilly.com/library/view/building-microservices-2nd/9781492034018/",
    type: "ebook",
    category: "backend",
    source: "O'Reilly",
    tags: ["Microservices", "Architecture", "Patterns"],
  },
  {
    title: "Netflix Tech Blog — Microservices at Scale",
    description:
      "Netflix's engineering team shares how they built and evolved their microservices platform to serve 200M+ subscribers with high availability and resilience.",
    url: "https://netflixtechblog.com/",
    type: "case-study",
    category: "backend",
    source: "Netflix Engineering",
    tags: ["Microservices", "Scale", "Resilience"],
  },

  /* ==================  DevOps  ================== */
  {
    title: "Stanford CS 110 — Principles of Computer Systems",
    description:
      "Covers processes, threads, networking, and systems programming. Essential foundational knowledge for understanding containerization, orchestration, and infrastructure.",
    url: "https://www.youtube.com/playlist?list=PLai-xIlqP9DLWFBR1mCb2hhJKNjrl3EqN",
    type: "playlist",
    category: "devops",
    source: "Stanford",
    tags: ["Systems", "Networking", "OS"],
  },
  {
    title: "Kubernetes The Hard Way",
    description:
      "Kelsey Hightower's hands-on guide to bootstrapping Kubernetes from scratch. Teaches what every abstraction layer does instead of using managed turnkey solutions.",
    url: "https://github.com/kelseyhightower/kubernetes-the-hard-way",
    type: "github",
    category: "devops",
    source: "Kelsey Hightower",
    tags: ["Kubernetes", "Infrastructure", "Hands-on"],
  },
  {
    title: "The Phoenix Project — DevOps Novel",
    description:
      "A novel about IT, DevOps, and business transformation. Teaches the Three Ways of DevOps through the story of a struggling IT organization's turnaround.",
    url: "https://itrevolution.com/product/the-phoenix-project/",
    type: "ebook",
    category: "devops",
    source: "IT Revolution",
    tags: ["DevOps Culture", "CI/CD", "Lean"],
  },
  {
    title: "Docker Curriculum — Prakhar Srivastav",
    description:
      "A comprehensive Docker tutorial for beginners with hands-on exercises. Covers containers, images, networking, multi-container apps with Docker Compose.",
    url: "https://docker-curriculum.com/",
    type: "course",
    category: "devops",
    source: "Prakhar Srivastav",
    tags: ["Docker", "Containers", "Compose"],
  },
  {
    title: "GitHub's Journey to Actions CI/CD",
    description:
      "How GitHub built and scaled GitHub Actions from concept to production, handling millions of workflow runs daily with a distributed architecture.",
    url: "https://github.blog/engineering/",
    type: "case-study",
    category: "devops",
    source: "GitHub Engineering",
    tags: ["CI/CD", "Automation", "Scale"],
  },

  /* ==================  Databases  ================== */
  {
    title: "CMU 15-445 — Database Systems",
    description:
      "Andy Pavlo's renowned CMU course on database internals. Covers storage engines, indexing, query processing, concurrency control, and recovery in modern DBMS architectures.",
    url: "https://www.youtube.com/playlist?list=PLSE8ODhjZXjbj8BMuIrRcacnQh20hmY9g",
    type: "playlist",
    category: "databases",
    source: "CMU",
    tags: ["SQL", "Internals", "B-Trees"],
  },
  {
    title: "Designing Data-Intensive Applications",
    description:
      "Martin Kleppmann's landmark book on data systems. Covers replication, partitioning, transactions, consistency, stream processing, and choosing the right data model.",
    url: "https://dataintensive.net/",
    type: "ebook",
    category: "databases",
    source: "O'Reilly",
    tags: ["DDIA", "Distributed", "Data Models"],
  },
  {
    title: "Redis University — Free Courses",
    description:
      "Official Redis training covering data structures, persistence, clustering, streams, and building real-time applications with Redis Stack.",
    url: "https://university.redis.io/",
    type: "course",
    category: "databases",
    source: "Redis",
    tags: ["Redis", "Caching", "In-Memory"],
  },
  {
    title: "Uber's Schemaless — A Scalable Datastore",
    description:
      "How Uber built Schemaless, a fault-tolerant, scalable datastore on top of MySQL to handle trip data at massive scale with flexible schema evolution.",
    url: "https://www.uber.com/blog/schemaless-part-one-mysql-datastore/",
    type: "case-study",
    category: "databases",
    source: "Uber Engineering",
    tags: ["MySQL", "Scale", "Architecture"],
  },
  {
    title: "PostgreSQL Exercises",
    description:
      "Free interactive PostgreSQL exercises. Practice writing SQL queries against a real dataset covering joins, aggregation, subqueries, window functions, and recursive CTEs.",
    url: "https://pgexercises.com/",
    type: "course",
    category: "databases",
    source: "PG Exercises",
    tags: ["PostgreSQL", "SQL", "Practice"],
  },

  /* ==================  System Design  ================== */
  {
    title: "MIT 6.033 — Computer System Engineering",
    description:
      "MIT's flagship systems course. Covers fault tolerance, atomicity, naming, security, networking, and the principles behind building reliable, scalable computer systems.",
    url: "https://www.youtube.com/playlist?list=PL6ogFv-ieghdoGKGg2Bik3Gl1glBTEu8c",
    type: "playlist",
    category: "system-design",
    source: "MIT",
    tags: ["Systems", "Fault Tolerance", "Networking"],
  },
  {
    title: "ByteByteGo — System Design 101",
    description:
      "Visual guides to system design concepts. Covers API design, caching strategies, message queues, database scaling, CDNs, and real-world architecture patterns.",
    url: "https://github.com/ByteByteGoHq/system-design-101",
    type: "github",
    category: "system-design",
    source: "ByteByteGo",
    tags: ["Visual", "Architecture", "Patterns"],
  },
  {
    title: "Stripe's API Design Philosophy",
    description:
      "How Stripe designs APIs that developers love. Covers versioning, error handling, idempotency, backward compatibility, and building for long-term maintainability.",
    url: "https://stripe.com/blog/payment-api-design",
    type: "case-study",
    category: "system-design",
    source: "Stripe Engineering",
    tags: ["API Design", "REST", "Developer Experience"],
  },
  {
    title: "Google SRE Book — Free Online",
    description:
      "Google's definitive guide to Site Reliability Engineering. Covers service level objectives, monitoring, alerting, incident management, and building reliable production systems.",
    url: "https://sre.google/sre-book/table-of-contents/",
    type: "ebook",
    category: "system-design",
    source: "Google",
    tags: ["SRE", "Reliability", "Production"],
  },
  {
    title: "How Discord Stores Trillions of Messages",
    description:
      "Discord's migration from MongoDB to Cassandra to ScyllaDB, the architectural decisions behind storing trillions of messages, and the performance gains achieved.",
    url: "https://discord.com/blog/how-discord-stores-trillions-of-messages",
    type: "case-study",
    category: "system-design",
    source: "Discord Engineering",
    tags: ["Storage", "Migration", "Scale"],
  },

  /* ==================  Security  ================== */
  {
    title: "Stanford CS 253 — Web Security",
    description:
      "Stanford's comprehensive web security course. Covers XSS, CSRF, SQL injection, authentication, session management, HTTPS, and modern browser security features.",
    url: "https://www.youtube.com/playlist?list=PL1y1iaEtjSYiiSGVlL1cHsXN_kvJOOhu-",
    type: "playlist",
    category: "security",
    source: "Stanford",
    tags: ["Web Security", "XSS", "CSRF"],
  },
  {
    title: "OWASP Top 10 — 2021",
    description:
      "The standard awareness document for web application security. Represents the most critical security risks including injection, broken auth, security misconfiguration, and more.",
    url: "https://owasp.org/www-project-top-ten/",
    type: "ebook",
    category: "security",
    source: "OWASP",
    tags: ["OWASP", "Vulnerabilities", "Best Practices"],
  },
  {
    title: "Awesome Security — Curated List",
    description:
      "A curated collection of security resources including tools, books, courses, and communities. Covers network security, web security, cryptography, and incident response.",
    url: "https://github.com/sbilly/awesome-security",
    type: "github",
    category: "security",
    source: "Community",
    tags: ["Tools", "Cryptography", "Network"],
  },
  {
    title: "How Cloudflare Handles DDoS Attacks",
    description:
      "Inside Cloudflare's DDoS defense architecture. How they filter 72+ million HTTP requests per second and protect 20% of all websites from volumetric and application-layer attacks.",
    url: "https://blog.cloudflare.com/tag/ddos/",
    type: "case-study",
    category: "security",
    source: "Cloudflare",
    tags: ["DDoS", "CDN", "Protection"],
  },

  /* ==================  AI / ML (additional)  ================== */
  {
    title: "Stanford CS231N — Convolutional Neural Networks",
    description:
      "Stanford's deep dive into CNNs for visual recognition. Covers image classification, object detection, segmentation, generative models, and visualization techniques.",
    url: "https://www.youtube.com/playlist?list=PL3FW7Lu3i5JvHM8ljYj-zLfQRF3EO8sYv",
    type: "playlist",
    category: "ai-ml",
    source: "Stanford",
    tags: ["Computer Vision", "CNN", "Image Recognition"],
  },
  {
    title: "Stanford CS234 — Reinforcement Learning",
    description:
      "Full Stanford course on reinforcement learning. Covers MDPs, policy gradients, Q-learning, model-based RL, exploration, and multi-agent systems.",
    url: "https://www.youtube.com/playlist?list=PLoROMvodv4rOSOPzutgyCTapiGlY2Nd8u",
    type: "playlist",
    category: "ai-ml",
    source: "Stanford",
    tags: ["Reinforcement Learning", "Q-Learning", "MDP"],
  },
  {
    title: "MIT 6.S897 — Machine Learning for Healthcare",
    description:
      "MIT course on applying ML to healthcare. Covers clinical NLP, medical imaging, causal inference, fairness, and deploying ML models in clinical settings.",
    url: "https://www.youtube.com/playlist?list=PLUl4u3cNGP60B0PQXVQyGNdCjRio7lBnR",
    type: "playlist",
    category: "ai-ml",
    source: "MIT",
    tags: ["Healthcare", "Clinical NLP", "Medical AI"],
  },
  {
    title: "LangChain — LLM Application Framework",
    description:
      "Framework for building applications powered by language models. Chains, agents, retrieval-augmented generation (RAG), memory, and tool use in production LLM apps.",
    url: "https://github.com/langchain-ai/langchain",
    type: "github",
    category: "ai-ml",
    source: "LangChain",
    tags: ["LLM", "RAG", "Agents"],
  },
  {
    title: "Andrej Karpathy — Neural Networks: Zero to Hero",
    description:
      "Karpathy's from-scratch series building neural networks in pure Python. Covers backprop, micrograd, makemore, GPT from scratch, and tokenization.",
    url: "https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ",
    type: "playlist",
    category: "ai-ml",
    source: "Andrej Karpathy",
    tags: ["From Scratch", "GPT", "Backpropagation"],
  },
  {
    title: "Scikit-learn Machine Learning Library",
    description:
      "The most widely used Python ML library. Simple APIs for classification, regression, clustering, dimensionality reduction, model selection, and preprocessing.",
    url: "https://github.com/scikit-learn/scikit-learn",
    type: "github",
    category: "ai-ml",
    source: "Scikit-learn",
    tags: ["Python", "Classical ML", "Sklearn"],
  },
  {
    title: "Google's Machine Learning Crash Course",
    description:
      "Google's free, fast-paced ML course. Covers linear regression, logistic regression, neural networks, embeddings, and ML engineering best practices with TensorFlow.",
    url: "https://developers.google.com/machine-learning/crash-course",
    type: "course",
    category: "ai-ml",
    source: "Google",
    tags: ["TensorFlow", "Beginner", "Practical"],
  },
  {
    title: "Full Stack Deep Learning",
    description:
      "Covers the full lifecycle of building ML-powered products: project setup, data management, training, deployment, testing, monitoring, and team workflows.",
    url: "https://fullstackdeeplearning.com/",
    type: "course",
    category: "ai-ml",
    source: "FSDL",
    tags: ["MLOps", "Deployment", "Production"],
  },
  {
    title: "OpenAI Cookbook",
    description:
      "Official collection of examples and guides for using the OpenAI API. Covers embeddings, fine-tuning, function calling, RAG patterns, and prompt engineering best practices.",
    url: "https://github.com/openai/openai-cookbook",
    type: "github",
    category: "ai-ml",
    source: "OpenAI",
    tags: ["GPT", "Prompt Engineering", "API"],
  },
  {
    title: "How Spotify Uses ML for Recommendations",
    description:
      "Deep dive into Spotify's recommendation engine. Covers collaborative filtering, content-based models, natural language processing of podcasts, and the Discover Weekly algorithm.",
    url: "https://engineering.atspotify.com/",
    type: "case-study",
    category: "ai-ml",
    source: "Spotify Engineering",
    tags: ["Recommendations", "Personalization", "Audio ML"],
  },

  /* ==================  Frontend (additional)  ================== */
  {
    title: "Vue.js — The Progressive Framework",
    description:
      "Approachable, performant, and versatile framework for building web UIs. Composition API, reactive state, single-file components, and a rich ecosystem.",
    url: "https://github.com/vuejs/core",
    type: "github",
    category: "frontend",
    source: "Vue.js",
    tags: ["Vue", "Reactivity", "SFC"],
  },
  {
    title: "Svelte — Cybernetically Enhanced Web Apps",
    description:
      "A radical new approach to building UIs. Svelte shifts work to compile time, producing highly optimized vanilla JS with no virtual DOM overhead.",
    url: "https://github.com/sveltejs/svelte",
    type: "github",
    category: "frontend",
    source: "Svelte",
    tags: ["Svelte", "Compiler", "Performance"],
  },
  {
    title: "JavaScript.info — The Modern Tutorial",
    description:
      "Comprehensive, free JavaScript tutorial from basics to advanced. Covers closures, prototypes, async/await, DOM, browser events, and web components.",
    url: "https://javascript.info/",
    type: "ebook",
    category: "frontend",
    source: "JavaScript.info",
    tags: ["JavaScript", "ES6+", "DOM"],
  },
  {
    title: "Storybook — UI Component Workshop",
    description:
      "Build, test, and document UI components in isolation. Supports React, Vue, Angular, Svelte, and web components. Essential for design systems and component libraries.",
    url: "https://github.com/storybookjs/storybook",
    type: "github",
    category: "frontend",
    source: "Storybook",
    tags: ["Components", "Testing", "Design System"],
  },
  {
    title: "Web.dev — Google's Web Best Practices",
    description:
      "Google's resource for modern web development. Covers performance (Core Web Vitals), accessibility, SEO, progressive web apps, and modern CSS/JS patterns.",
    url: "https://web.dev/",
    type: "course",
    category: "frontend",
    source: "Google",
    tags: ["Performance", "Accessibility", "PWA"],
  },
  {
    title: "How Figma Built a Multiplayer Editor",
    description:
      "Figma's engineering deep dive into building real-time collaborative editing with CRDTs, WebSockets, and operational transforms at scale.",
    url: "https://www.figma.com/blog/how-figmas-multiplayer-technology-works/",
    type: "case-study",
    category: "frontend",
    source: "Figma Engineering",
    tags: ["Collaboration", "CRDT", "WebSocket"],
  },
  {
    title: "Patterns.dev — Design Patterns for Modern JS",
    description:
      "Free online book covering design patterns, rendering patterns, and performance patterns for modern web applications. By Lydia Hallie and Addy Osmani.",
    url: "https://www.patterns.dev/",
    type: "ebook",
    category: "frontend",
    source: "Patterns.dev",
    tags: ["Design Patterns", "Rendering", "Performance"],
  },
  {
    title: "Testing Library — Simple Testing Utilities",
    description:
      "Lightweight testing utilities that encourage good testing practices. Tests components the way users interact with them. Supports React, Vue, Angular, and more.",
    url: "https://github.com/testing-library/react-testing-library",
    type: "github",
    category: "frontend",
    source: "Testing Library",
    tags: ["Testing", "React", "Accessibility"],
  },

  /* ==================  Backend (additional)  ================== */
  {
    title: "Stanford CS 144 — Introduction to Computer Networking",
    description:
      "Stanford's networking fundamentals course. Covers TCP/IP, routing, congestion control, DNS, HTTP, and building networked applications from packets up.",
    url: "https://www.youtube.com/playlist?list=PLoCMsyE1cvdWKsLVyf6cPwCLDIZnOj0NS",
    type: "playlist",
    category: "backend",
    source: "Stanford",
    tags: ["Networking", "TCP/IP", "HTTP"],
  },
  {
    title: "Go Programming Language",
    description:
      "Google's systems programming language designed for simplicity and concurrency. Garbage collected, statically typed, with goroutines and channels for concurrent programming.",
    url: "https://github.com/golang/go",
    type: "github",
    category: "backend",
    source: "Google",
    tags: ["Go", "Concurrency", "Systems"],
  },
  {
    title: "Rust Programming Language Book",
    description:
      "The official Rust book. Covers ownership, borrowing, lifetimes, traits, concurrency without data races, and building reliable, high-performance systems software.",
    url: "https://doc.rust-lang.org/book/",
    type: "ebook",
    category: "backend",
    source: "Rust Foundation",
    tags: ["Rust", "Memory Safety", "Performance"],
  },
  {
    title: "Clean Architecture — Robert C. Martin",
    description:
      "Uncle Bob's guide to building maintainable software architecture. Covers SOLID principles, component principles, boundaries, and the dependency rule.",
    url: "https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/",
    type: "ebook",
    category: "backend",
    source: "O'Reilly",
    tags: ["Architecture", "SOLID", "Clean Code"],
  },
  {
    title: "Spring Boot — Java Framework",
    description:
      "The most popular Java framework for building production-grade applications. Convention over configuration, embedded servers, actuator monitoring, and cloud-native support.",
    url: "https://github.com/spring-projects/spring-boot",
    type: "github",
    category: "backend",
    source: "VMware",
    tags: ["Java", "Spring", "Enterprise"],
  },
  {
    title: "How Slack Built Shared Channels",
    description:
      "Slack's engineering challenge of connecting different organizations' workspaces. Covers data isolation, permission boundaries, and cross-org real-time messaging.",
    url: "https://slack.engineering/",
    type: "case-study",
    category: "backend",
    source: "Slack Engineering",
    tags: ["Architecture", "Multi-tenant", "Real-time"],
  },
  {
    title: "gRPC — High-Performance RPC Framework",
    description:
      "Google's modern RPC framework using Protocol Buffers. Supports bidirectional streaming, flow control, and runs in any environment with pluggable auth and load balancing.",
    url: "https://github.com/grpc/grpc",
    type: "github",
    category: "backend",
    source: "Google",
    tags: ["RPC", "Protobuf", "Streaming"],
  },
  {
    title: "Apache Kafka — Distributed Event Streaming",
    description:
      "Distributed event streaming platform used by 80% of Fortune 100 companies. High-throughput, fault-tolerant, and horizontally scalable publish-subscribe messaging.",
    url: "https://github.com/apache/kafka",
    type: "github",
    category: "backend",
    source: "Apache",
    tags: ["Kafka", "Event Streaming", "Pub/Sub"],
  },

  /* ==================  DevOps (additional)  ================== */
  {
    title: "Terraform — Infrastructure as Code",
    description:
      "HashiCorp's IaC tool for provisioning and managing cloud infrastructure. Declarative configuration, multi-cloud support, state management, and module system.",
    url: "https://github.com/hashicorp/terraform",
    type: "github",
    category: "devops",
    source: "HashiCorp",
    tags: ["IaC", "Cloud", "Terraform"],
  },
  {
    title: "Prometheus — Monitoring & Alerting",
    description:
      "Open-source monitoring toolkit designed for reliability. Pull-based metrics collection, PromQL query language, multi-dimensional data model, and built-in alerting.",
    url: "https://github.com/prometheus/prometheus",
    type: "github",
    category: "devops",
    source: "CNCF",
    tags: ["Monitoring", "Metrics", "Alerting"],
  },
  {
    title: "GitHub Actions — CI/CD Workflows",
    description:
      "Comprehensive guide to GitHub Actions. Covers workflow syntax, job matrices, secrets, artifacts, caching, reusable workflows, and custom actions.",
    url: "https://docs.github.com/en/actions",
    type: "ebook",
    category: "devops",
    source: "GitHub",
    tags: ["CI/CD", "GitHub", "Automation"],
  },
  {
    title: "Ansible — IT Automation Platform",
    description:
      "Simple, agentless IT automation. Playbooks, roles, inventories, and modules for configuration management, app deployment, and orchestration across infrastructure.",
    url: "https://github.com/ansible/ansible",
    type: "github",
    category: "devops",
    source: "Red Hat",
    tags: ["Automation", "Config Management", "Agentless"],
  },
  {
    title: "How GitLab Deploys to Production",
    description:
      "GitLab's transparent engineering blog about their deployment pipeline. Covers progressive delivery, feature flags, canary deployments, and rollback strategies.",
    url: "https://about.gitlab.com/blog/categories/engineering/",
    type: "case-study",
    category: "devops",
    source: "GitLab",
    tags: ["Deployment", "Feature Flags", "Canary"],
  },
  {
    title: "The DevOps Handbook",
    description:
      "The practical companion to The Phoenix Project. Covers the technical practices of flow, feedback, and continuous learning that enable DevOps transformation.",
    url: "https://itrevolution.com/product/the-devops-handbook-second-edition/",
    type: "ebook",
    category: "devops",
    source: "IT Revolution",
    tags: ["DevOps", "Flow", "Feedback Loops"],
  },
  {
    title: "Grafana — Observability Platform",
    description:
      "Open-source analytics and monitoring platform. Connects to Prometheus, Loki, Tempo, and 100+ data sources. Beautiful dashboards, alerting, and exploration tools.",
    url: "https://github.com/grafana/grafana",
    type: "github",
    category: "devops",
    source: "Grafana Labs",
    tags: ["Dashboards", "Observability", "Visualization"],
  },
  {
    title: "Nix & NixOS — Reproducible Builds",
    description:
      "Purely functional package manager and OS. Guarantees reproducible, declarative builds and system configurations. Increasingly popular for dev environments.",
    url: "https://github.com/NixOS/nixpkgs",
    type: "github",
    category: "devops",
    source: "NixOS Foundation",
    tags: ["Nix", "Reproducibility", "Packaging"],
  },

  /* ==================  Databases (additional)  ================== */
  {
    title: "CMU 15-721 — Advanced Database Systems",
    description:
      "Andy Pavlo's advanced CMU course. Covers query compilation, vectorized execution, modern OLAP systems, in-memory databases, and cutting-edge DB research.",
    url: "https://www.youtube.com/playlist?list=PLSE8ODhjZXjYzlIK4K3p2Jh8mEHfbJVVT",
    type: "playlist",
    category: "databases",
    source: "CMU",
    tags: ["OLAP", "Query Optimization", "Advanced"],
  },
  {
    title: "MongoDB University — Free Courses",
    description:
      "Official MongoDB training. Covers CRUD operations, aggregation pipelines, indexing strategies, data modeling, schema design, and Atlas deployment.",
    url: "https://university.mongodb.com/",
    type: "course",
    category: "databases",
    source: "MongoDB",
    tags: ["MongoDB", "NoSQL", "Aggregation"],
  },
  {
    title: "Apache Spark — Unified Analytics Engine",
    description:
      "Open-source unified analytics engine for large-scale data processing. Spark SQL, DataFrames, MLlib, GraphX, and Structured Streaming in one platform.",
    url: "https://github.com/apache/spark",
    type: "github",
    category: "databases",
    source: "Apache",
    tags: ["Spark", "Big Data", "ETL"],
  },
  {
    title: "Use The Index, Luke — SQL Indexing Guide",
    description:
      "Free online guide to database indexing and SQL performance. Covers B-tree indexes, partial indexes, covering indexes, join optimization, and query plan analysis.",
    url: "https://use-the-index-luke.com/",
    type: "ebook",
    category: "databases",
    source: "Markus Winand",
    tags: ["Indexing", "SQL Performance", "B-Tree"],
  },
  {
    title: "How Pinterest Scaled MySQL to 1 Trillion Rows",
    description:
      "Pinterest's journey sharding MySQL to handle a trillion pin records. Covers shard key selection, data migration, consistency guarantees, and operational lessons.",
    url: "https://medium.com/pinterest-engineering/sharding-pinterest-how-we-scaled-our-mysql-fleet-3f341e96ca6f",
    type: "case-study",
    category: "databases",
    source: "Pinterest Engineering",
    tags: ["Sharding", "MySQL", "Scale"],
  },
  {
    title: "ClickHouse — Real-Time Analytics Database",
    description:
      "Open-source column-oriented DBMS for real-time analytics. Processes billions of rows per second with SQL and supports joins, aggregations, and materialized views.",
    url: "https://github.com/ClickHouse/ClickHouse",
    type: "github",
    category: "databases",
    source: "ClickHouse",
    tags: ["OLAP", "Columnar", "Analytics"],
  },
  {
    title: "Supabase — Open Source Firebase Alternative",
    description:
      "Provides a PostgreSQL database, authentication, instant APIs, edge functions, storage, and realtime subscriptions. Full backend from a single open-source platform.",
    url: "https://github.com/supabase/supabase",
    type: "github",
    category: "databases",
    source: "Supabase",
    tags: ["PostgreSQL", "BaaS", "Real-time"],
  },

  /* ==================  System Design (additional)  ================== */
  {
    title: "MIT 6.004 — Computation Structures",
    description:
      "MIT's foundational computer architecture course. Covers digital logic, processor design, pipelining, caching, virtual memory, and operating system basics.",
    url: "https://www.youtube.com/playlist?list=PLUl4u3cNGP62WVs95MNq3dQBqY2vGOtQ2",
    type: "playlist",
    category: "system-design",
    source: "MIT",
    tags: ["Computer Architecture", "Pipelining", "Cache"],
  },
  {
    title: "Grokking System Design Interview",
    description:
      "Comprehensive guide for system design interviews. Covers load balancers, CDNs, consistent hashing, real-world designs for Twitter, YouTube, Uber, and more.",
    url: "https://www.designgurus.io/course/grokking-the-system-design-interview",
    type: "course",
    category: "system-design",
    source: "Design Gurus",
    tags: ["Interview Prep", "Architecture", "Scale"],
  },
  {
    title: "How Instagram Serves 2 Billion Users",
    description:
      "Instagram's infrastructure evolution from a small Django app to serving 2B+ monthly active users. Covers feed ranking, stories infrastructure, and scaling Python.",
    url: "https://instagram-engineering.com/",
    type: "case-study",
    category: "system-design",
    source: "Meta Engineering",
    tags: ["Scale", "Django", "Feed Systems"],
  },
  {
    title: "Microsoft Azure Architecture Center",
    description:
      "Cloud design patterns, reference architectures, and best practices. Covers microservices, event-driven systems, CQRS, saga patterns, and cloud-native design.",
    url: "https://learn.microsoft.com/en-us/azure/architecture/",
    type: "ebook",
    category: "system-design",
    source: "Microsoft",
    tags: ["Cloud Patterns", "CQRS", "Event-Driven"],
  },
  {
    title: "How LinkedIn Handles 2M Queries Per Second",
    description:
      "LinkedIn's search infrastructure serving millions of queries per second. Covers inverted indexes, query understanding, ranking models, and real-time indexing.",
    url: "https://engineering.linkedin.com/blog",
    type: "case-study",
    category: "system-design",
    source: "LinkedIn Engineering",
    tags: ["Search", "Scale", "Real-time"],
  },
  {
    title: "Awesome Scalability — Reading List",
    description:
      "Curated reading list for building scalable, reliable systems. Covers availability, stability patterns, performance, and case studies from top tech companies.",
    url: "https://github.com/binhnguyennus/awesome-scalability",
    type: "github",
    category: "system-design",
    source: "Community",
    tags: ["Scalability", "Reliability", "Reading List"],
  },
  {
    title: "How Twitter Processes 400 Billion Events in Real-Time",
    description:
      "Twitter's event processing pipeline handling 400B+ events daily. Covers Apache Kafka, Heron stream processing, and Lambda architecture.",
    url: "https://blog.x.com/engineering",
    type: "case-study",
    category: "system-design",
    source: "X Engineering",
    tags: ["Event Processing", "Kafka", "Stream"],
  },

  /* ==================  Security (additional)  ================== */
  {
    title: "MIT 6.858 — Computer Systems Security",
    description:
      "MIT's graduate systems security course. Covers buffer overflows, privilege separation, web security, network attacks, sandboxing, and formal verification.",
    url: "https://www.youtube.com/playlist?list=PLUl4u3cNGP62K2DjQLRxDNRi0z2IRWnNh",
    type: "playlist",
    category: "security",
    source: "MIT",
    tags: ["Systems Security", "Exploits", "Sandboxing"],
  },
  {
    title: "PortSwigger Web Security Academy",
    description:
      "Free, comprehensive web security training. Hands-on labs covering SQL injection, XSS, SSRF, OAuth vulnerabilities, business logic flaws, and advanced topics.",
    url: "https://portswigger.net/web-security",
    type: "course",
    category: "security",
    source: "PortSwigger",
    tags: ["Web Security", "Hands-on Labs", "Burp Suite"],
  },
  {
    title: "Trivy — Container Security Scanner",
    description:
      "Open-source vulnerability scanner for containers, K8s, IaC, and file systems. Detects CVEs, secrets, misconfigurations, and license issues in CI/CD pipelines.",
    url: "https://github.com/aquasecurity/trivy",
    type: "github",
    category: "security",
    source: "Aqua Security",
    tags: ["Container Security", "Scanning", "DevSecOps"],
  },
  {
    title: "Cryptography Engineering — Schneier et al.",
    description:
      "Practical guide to implementing cryptographic systems. Covers block ciphers, hash functions, public-key crypto, key management, and secure protocol design.",
    url: "https://www.schneier.com/books/cryptography-engineering/",
    type: "ebook",
    category: "security",
    source: "Schneier",
    tags: ["Cryptography", "Protocols", "Implementation"],
  },
  {
    title: "How Google Does Zero Trust Security",
    description:
      "Google's BeyondCorp implementation. How they moved from perimeter-based security to a zero-trust model where every request is authenticated and authorized.",
    url: "https://cloud.google.com/beyondcorp",
    type: "case-study",
    category: "security",
    source: "Google Cloud",
    tags: ["Zero Trust", "BeyondCorp", "IAM"],
  },
  {
    title: "NIST Cybersecurity Framework",
    description:
      "The US government's framework for managing cybersecurity risk. Covers identify, protect, detect, respond, and recover functions with implementation tiers.",
    url: "https://www.nist.gov/cyberframework",
    type: "ebook",
    category: "security",
    source: "NIST",
    tags: ["Framework", "Risk Management", "Compliance"],
  },
  {
    title: "Hack The Box — Cybersecurity Training",
    description:
      "Hands-on cybersecurity training platform. Practice penetration testing, exploit development, reverse engineering, and forensics on real vulnerable machines.",
    url: "https://www.hackthebox.com/",
    type: "course",
    category: "security",
    source: "Hack The Box",
    tags: ["Pentesting", "CTF", "Hands-on"],
  },

  /* ==================  Data Science  ================== */
  {
    title: "Stanford CS109 — Probability for Computer Scientists",
    description:
      "Stanford's probability course covering distributions, Bayes' theorem, expectation, variance, and the mathematical foundations behind every data science model.",
    url: "https://www.youtube.com/playlist?list=PLoROMvodv4rOpr_A7B9SriE_iZmkanvUg",
    type: "playlist",
    category: "data-science",
    source: "Stanford",
    tags: ["Probability", "Statistics", "Foundations"],
  },
  {
    title: "MIT 18.650 — Statistics for Applications",
    description:
      "MIT's graduate statistics course. Hypothesis testing, confidence intervals, regression, PCA, and generalized linear models with rigorous mathematical treatment.",
    url: "https://www.youtube.com/playlist?list=PLUl4u3cNGP60uVBMaoNERc6knT_MgPKS0",
    type: "playlist",
    category: "data-science",
    source: "MIT",
    tags: ["Statistics", "Hypothesis Testing", "Regression"],
  },
  {
    title: "Harvard CS109 — Data Science",
    description:
      "Harvard's flagship data science course. Covers EDA, web scraping, statistical modeling, machine learning, visualization, and storytelling with data.",
    url: "https://cs109.github.io/2015/",
    type: "course",
    category: "data-science",
    source: "Harvard",
    tags: ["EDA", "Visualization", "Modeling"],
  },
  {
    title: "Python Data Science Handbook — Jake VanderPlas",
    description:
      "Free online book covering NumPy, Pandas, Matplotlib, Scikit-learn, and the entire Python data science stack with practical examples and recipes.",
    url: "https://jakevdp.github.io/PythonDataScienceHandbook/",
    type: "ebook",
    category: "data-science",
    source: "Jake VanderPlas",
    tags: ["Python", "Pandas", "NumPy"],
  },
  {
    title: "Kaggle — Learn Data Science",
    description:
      "Free micro-courses covering Pandas, data visualization, feature engineering, intro to ML, deep learning, and data cleaning with interactive notebooks.",
    url: "https://www.kaggle.com/learn",
    type: "course",
    category: "data-science",
    source: "Kaggle",
    tags: ["Hands-on", "Notebooks", "Competitions"],
  },
  {
    title: "Pandas — Python Data Analysis Library",
    description:
      "The fundamental Python library for data manipulation. DataFrames, time series, merging, reshaping, groupby, and I/O tools for CSV, Excel, SQL, and more.",
    url: "https://github.com/pandas-dev/pandas",
    type: "github",
    category: "data-science",
    source: "Pandas",
    tags: ["Pandas", "DataFrames", "ETL"],
  },
  {
    title: "Apache Airflow — Workflow Orchestration",
    description:
      "Platform to author, schedule, and monitor data pipelines. DAG-based workflows, rich UI, extensive operator library, and integrations with every major cloud.",
    url: "https://github.com/apache/airflow",
    type: "github",
    category: "data-science",
    source: "Apache",
    tags: ["Pipelines", "ETL", "Orchestration"],
  },
  {
    title: "How Netflix Uses Data Science for Content Strategy",
    description:
      "Netflix's data-driven approach to greenlighting shows. How A/B tests, viewing models, and taste communities influence billions of dollars in content investment.",
    url: "https://netflixtechblog.com/",
    type: "case-study",
    category: "data-science",
    source: "Netflix",
    tags: ["A/B Testing", "Content", "Recommendations"],
  },
  {
    title: "How Uber's Data Team Predicts Surge Pricing",
    description:
      "Uber's ML-powered demand forecasting. Geospatial modeling, time-series analysis, and real-time feature engineering to predict rider demand across every city.",
    url: "https://www.uber.com/blog/forecasting-introduction/",
    type: "case-study",
    category: "data-science",
    source: "Uber Engineering",
    tags: ["Forecasting", "Geospatial", "Time Series"],
  },
  {
    title: "How Airbnb Standardized Metric Definitions",
    description:
      "Airbnb's Minerva platform for consistent metrics. How they solved the 'multiple sources of truth' problem, enabling self-serve analytics across 6000+ employees.",
    url: "https://medium.com/airbnb-engineering/airbnb-metric-computation-with-minerva-part-2-9afe6695b486",
    type: "case-study",
    category: "data-science",
    source: "Airbnb Engineering",
    tags: ["Metrics", "Data Platform", "Self-Serve"],
  },
  {
    title: "How DoorDash Built a Real-Time Feature Store",
    description:
      "DoorDash's feature store for serving ML features at low latency. Covers feature computation, storage, versioning, and point-in-time correctness for training data.",
    url: "https://doordash.engineering/2020/11/19/building-a-gigascale-ml-feature-store-with-redis/",
    type: "case-study",
    category: "data-science",
    source: "DoorDash Engineering",
    tags: ["Feature Store", "Redis", "ML Infra"],
  },
  {
    title: "How Shopify Detects Fraud with Data Science",
    description:
      "Shopify's fraud detection pipeline processing millions of transactions. Covers graph neural networks, anomaly detection, and real-time risk scoring at checkout.",
    url: "https://shopify.engineering/",
    type: "case-study",
    category: "data-science",
    source: "Shopify Engineering",
    tags: ["Fraud Detection", "Anomaly Detection", "GNN"],
  },
  {
    title: "How Lyft Built a Real-Time ETA Prediction System",
    description:
      "Lyft's ML system for predicting accurate arrival times. Covers road segment modeling, traffic prediction, and the feedback loop between predictions and driver routing.",
    url: "https://eng.lyft.com/",
    type: "case-study",
    category: "data-science",
    source: "Lyft Engineering",
    tags: ["ETA", "Routing", "Prediction"],
  },
  {
    title: "How Stripe Trains Models on Billions of Transactions",
    description:
      "Stripe's ML infrastructure for fraud detection and revenue optimization. Covers distributed training, feature pipelines, and model serving at payments scale.",
    url: "https://stripe.com/blog/engineering",
    type: "case-study",
    category: "data-science",
    source: "Stripe Engineering",
    tags: ["Payments", "Fraud", "ML Infra"],
  },
  {
    title: "Streamlit — Data Apps in Minutes",
    description:
      "Turn Python scripts into interactive web apps. Perfect for ML demos, data exploration dashboards, and sharing analysis with non-technical stakeholders.",
    url: "https://github.com/streamlit/streamlit",
    type: "github",
    category: "data-science",
    source: "Streamlit",
    tags: ["Dashboards", "Python", "Visualization"],
  },
  {
    title: "How LinkedIn Built Its Experimentation Platform",
    description:
      "LinkedIn's A/B testing platform running thousands of experiments simultaneously. Covers statistical rigor, metric guardrails, and scaling experimentation culture.",
    url: "https://engineering.linkedin.com/blog",
    type: "case-study",
    category: "data-science",
    source: "LinkedIn Engineering",
    tags: ["A/B Testing", "Experimentation", "Statistics"],
  },

  /* ==================  SQL  ================== */
  {
    title: "Stanford CS 145 — Data Management & Data Systems",
    description:
      "Stanford's foundational database course. Covers relational model, SQL, query optimization, transactions, data warehousing, and modern analytics architectures.",
    url: "https://www.youtube.com/playlist?list=PLroEs25KGvwzmvIxYHRhoGTz9t0eT7cgz",
    type: "playlist",
    category: "sql",
    source: "Stanford",
    tags: ["Relational Model", "Query Optimization", "Data Warehousing"],
  },
  {
    title: "SQLBolt — Interactive SQL Lessons",
    description:
      "Learn SQL with interactive exercises. Covers SELECT, filtering, joins, aggregation, subqueries, UNION, and creating/modifying tables with hands-on practice.",
    url: "https://sqlbolt.com/",
    type: "course",
    category: "sql",
    source: "SQLBolt",
    tags: ["Interactive", "Beginner", "Practice"],
  },
  {
    title: "Mode SQL Tutorial — Analytics Focus",
    description:
      "SQL tutorial designed for analysts. Covers window functions, CTEs, pivoting, date functions, performance tuning, and writing production-grade analytical queries.",
    url: "https://mode.com/sql-tutorial/",
    type: "course",
    category: "sql",
    source: "Mode Analytics",
    tags: ["Window Functions", "CTEs", "Analytics"],
  },
  {
    title: "PostgreSQL Exercises — pgexercises.com",
    description:
      "Free interactive PostgreSQL exercises. Practice SQL against a real dataset covering joins, aggregation, subqueries, window functions, recursive CTEs, and date handling.",
    url: "https://pgexercises.com/",
    type: "course",
    category: "sql",
    source: "PG Exercises",
    tags: ["PostgreSQL", "Practice", "Window Functions"],
  },
  {
    title: "Use The Index, Luke — SQL Performance",
    description:
      "The definitive guide to SQL indexing and query performance. B-tree internals, partial indexes, covering indexes, join optimization, and reading execution plans.",
    url: "https://use-the-index-luke.com/",
    type: "ebook",
    category: "sql",
    source: "Markus Winand",
    tags: ["Indexing", "Performance", "Execution Plans"],
  },
  {
    title: "SQL Style Guide — Simon Holywell",
    description:
      "Best practices for writing readable, maintainable SQL. Covers naming conventions, formatting, aliasing, joins, CTEs, and standards followed by top data teams.",
    url: "https://www.sqlstyle.guide/",
    type: "ebook",
    category: "sql",
    source: "Simon Holywell",
    tags: ["Style Guide", "Best Practices", "Readability"],
  },
  {
    title: "How Shopify Migrated 1.8 Trillion Rows with Zero Downtime",
    description:
      "Shopify's massive MySQL migration moving 1.8 trillion rows across shards without service interruption. Covers online schema changes, dual-writing, and validation.",
    url: "https://shopify.engineering/mysql-database-migration",
    type: "case-study",
    category: "sql",
    source: "Shopify Engineering",
    tags: ["Migration", "MySQL", "Zero Downtime"],
  },
  {
    title: "How GitHub Migrated MySQL to Vitess at Scale",
    description:
      "GitHub's multi-year migration from traditional MySQL to Vitess for horizontal scaling. Covers schema management, query serving, and maintaining uptime during transition.",
    url: "https://github.blog/engineering/infrastructure/mysql-high-availability-at-github/",
    type: "case-study",
    category: "sql",
    source: "GitHub Engineering",
    tags: ["Vitess", "MySQL", "Horizontal Scaling"],
  },
  {
    title: "How Stripe Manages SQL Schema Changes Safely",
    description:
      "Stripe's approach to database migrations in a high-transaction environment. Covers safe migration patterns, backwards-compatible changes, and automated rollback.",
    url: "https://stripe.com/blog/online-migrations",
    type: "case-study",
    category: "sql",
    source: "Stripe Engineering",
    tags: ["Migrations", "Schema Changes", "Safety"],
  },
  {
    title: "How Notion Built Its Data Model",
    description:
      "Notion's unique block-based data model stored in PostgreSQL. How they represent pages, databases, properties, and relations in a flexible relational schema.",
    url: "https://www.notion.so/blog/data-model-behind-notion",
    type: "case-study",
    category: "sql",
    source: "Notion",
    tags: ["Data Model", "PostgreSQL", "Schema Design"],
  },
  {
    title: "How Figma Scaled PostgreSQL for Real-Time Collaboration",
    description:
      "Figma's PostgreSQL architecture supporting real-time multiplayer editing. Covers connection pooling, read replicas, query optimization, and horizontal partitioning.",
    url: "https://www.figma.com/blog/how-figma-scaled-to-multiple-databases/",
    type: "case-study",
    category: "sql",
    source: "Figma Engineering",
    tags: ["PostgreSQL", "Scaling", "Real-Time"],
  },
  {
    title: "How Instagram Sharded PostgreSQL",
    description:
      "Instagram's approach to sharding PostgreSQL to handle billions of photos. Covers shard key design, data distribution, cross-shard queries, and consistency.",
    url: "https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a71e5a5c",
    type: "case-study",
    category: "sql",
    source: "Instagram Engineering",
    tags: ["Sharding", "PostgreSQL", "ID Generation"],
  },
  {
    title: "How Slack Manages Database Query Performance",
    description:
      "Slack's approach to SQL query performance at scale. Covers slow query detection, index optimization, query rewriting, and monitoring query latencies in production.",
    url: "https://slack.engineering/scaling-datastores-at-slack-with-vitess/",
    type: "case-study",
    category: "sql",
    source: "Slack Engineering",
    tags: ["Vitess", "Query Performance", "Monitoring"],
  },
  {
    title: "How Cloudflare Uses ClickHouse for Analytics SQL",
    description:
      "How Cloudflare queries 40M+ events/second using ClickHouse SQL. Covers columnar storage, materialized views, and real-time analytics on petabyte-scale data.",
    url: "https://blog.cloudflare.com/http-analytics-for-6m-requests-per-second-using-clickhouse/",
    type: "case-study",
    category: "sql",
    source: "Cloudflare",
    tags: ["ClickHouse", "Analytics", "Columnar"],
  },
  {
    title: "How Airbnb Built a Query Engine for Minerva",
    description:
      "Airbnb's custom SQL query engine for their metrics platform. Covers query parsing, optimization, caching, and federated queries across heterogeneous data sources.",
    url: "https://medium.com/airbnb-engineering/how-airbnb-achieved-metric-consistency-at-scale-f23cc53dea70",
    type: "case-study",
    category: "sql",
    source: "Airbnb Engineering",
    tags: ["Query Engine", "Metrics", "Federated"],
  },
  {
    title: "How Uber Built Queryparser for SQL Analysis",
    description:
      "Uber's open-source SQL parser for analyzing query patterns. Covers table lineage, column-level dependencies, and automated migration impact analysis.",
    url: "https://www.uber.com/blog/queryparser/",
    type: "case-study",
    category: "sql",
    source: "Uber Engineering",
    tags: ["SQL Parsing", "Lineage", "Migration"],
  },
  {
    title: "DuckDB — In-Process Analytical Database",
    description:
      "Embeddable analytical SQL database. Blazing-fast OLAP queries on Parquet, CSV, and JSON files with zero configuration. The 'SQLite for analytics'.",
    url: "https://github.com/duckdb/duckdb",
    type: "github",
    category: "sql",
    source: "DuckDB",
    tags: ["OLAP", "Embedded", "Analytics"],
  },
  {
    title: "DataGrip SQL IDE — JetBrains",
    description:
      "Professional SQL IDE with intelligent code completion, on-the-fly analysis, quick-fixes, and support for PostgreSQL, MySQL, Oracle, SQL Server, and more.",
    url: "https://www.jetbrains.com/datagrip/",
    type: "course",
    category: "sql",
    source: "JetBrains",
    tags: ["IDE", "Productivity", "Multi-DB"],
  },

  /* ==================  Mobile  ================== */
  {
    title: "Stanford CS193p — Developing Apps for iOS",
    description:
      "Stanford's legendary iOS development course. Covers SwiftUI, MVVM, property wrappers, gestures, animation, persistence, and building production-quality iOS apps.",
    url: "https://www.youtube.com/playlist?list=PLpGHT1n4-mAtTj9oywMWoBx0dCGd51_yG",
    type: "playlist",
    category: "mobile",
    source: "Stanford",
    tags: ["iOS", "SwiftUI", "MVVM"],
  },
  {
    title: "React Native — Cross-Platform Mobile",
    description:
      "Build native mobile apps using React. One codebase for iOS and Android with native components, hot reloading, and access to platform APIs.",
    url: "https://github.com/facebook/react-native",
    type: "github",
    category: "mobile",
    source: "Meta",
    tags: ["React Native", "Cross-Platform", "JavaScript"],
  },
  {
    title: "Flutter — Google's UI Toolkit",
    description:
      "Build natively compiled apps for mobile, web, and desktop from a single Dart codebase. Hot reload, expressive UI, and native performance.",
    url: "https://github.com/flutter/flutter",
    type: "github",
    category: "mobile",
    source: "Google",
    tags: ["Flutter", "Dart", "Cross-Platform"],
  },
  {
    title: "Android Developer Guides — Official",
    description:
      "Google's official Android development guides. Covers Jetpack Compose, architecture components, navigation, data persistence, and Material Design 3.",
    url: "https://developer.android.com/guide",
    type: "ebook",
    category: "mobile",
    source: "Google",
    tags: ["Android", "Jetpack Compose", "Kotlin"],
  },
  {
    title: "How Instagram Reduced App Size by 60%",
    description:
      "Instagram's systematic approach to reducing Android APK size. Covers code shrinking, resource optimization, native library stripping, and dynamic delivery.",
    url: "https://instagram-engineering.com/",
    type: "case-study",
    category: "mobile",
    source: "Instagram Engineering",
    tags: ["App Size", "Android", "Optimization"],
  },
  {
    title: "How Uber Rebuilt Their Rider App",
    description:
      "Uber's complete rewrite of their rider app. Covers architecture decisions, plugin systems, feature isolation, testing strategies, and incremental rollout.",
    url: "https://www.uber.com/blog/new-rider-app-architecture/",
    type: "case-study",
    category: "mobile",
    source: "Uber Engineering",
    tags: ["Architecture", "Rewrite", "Plugin System"],
  },
  {
    title: "Expo — React Native Development Platform",
    description:
      "Tools, services, and libraries that simplify React Native development. Over-the-air updates, push notifications, and access to native APIs without native code.",
    url: "https://github.com/expo/expo",
    type: "github",
    category: "mobile",
    source: "Expo",
    tags: ["Expo", "React Native", "OTA Updates"],
  },

  /* ==================  Cloud  ================== */
  {
    title: "MIT 6.5840 — Distributed Computer Systems",
    description:
      "MIT's graduate course on building reliable distributed systems in the cloud. Covers consensus, replication, linearizability, and fault tolerance.",
    url: "https://pdos.csail.mit.edu/6.824/",
    type: "course",
    category: "cloud",
    source: "MIT",
    tags: ["Distributed Systems", "Consensus", "Fault Tolerance"],
  },
  {
    title: "AWS Well-Architected Framework",
    description:
      "AWS's guide to building secure, high-performing, resilient, and efficient cloud infrastructure. Covers operational excellence, security, reliability, and cost optimization.",
    url: "https://docs.aws.amazon.com/wellarchitected/latest/framework/",
    type: "ebook",
    category: "cloud",
    source: "AWS",
    tags: ["AWS", "Best Practices", "Architecture"],
  },
  {
    title: "Google Cloud Architecture Framework",
    description:
      "GCP's comprehensive guide covering system design, operational excellence, security, reliability, and performance optimization for cloud-native applications.",
    url: "https://cloud.google.com/architecture/framework",
    type: "ebook",
    category: "cloud",
    source: "Google Cloud",
    tags: ["GCP", "Architecture", "Cloud-Native"],
  },
  {
    title: "Pulumi — Infrastructure as Code in Any Language",
    description:
      "Define cloud infrastructure using TypeScript, Python, Go, or C#. Full programming language support instead of custom DSLs, with testing and reuse.",
    url: "https://github.com/pulumi/pulumi",
    type: "github",
    category: "cloud",
    source: "Pulumi",
    tags: ["IaC", "Multi-Cloud", "TypeScript"],
  },
  {
    title: "How Dropbox Migrated 500PB from AWS to Own Infrastructure",
    description:
      "Dropbox's 2.5-year journey moving half an exabyte of data from AWS S3 to their own data centers. Covers cost analysis, custom hardware, and Magic Pocket storage.",
    url: "https://dropbox.tech/infrastructure/inside-the-magic-pocket",
    type: "case-study",
    category: "cloud",
    source: "Dropbox Engineering",
    tags: ["Migration", "Storage", "Infrastructure"],
  },
  {
    title: "How Netflix Runs on AWS at Global Scale",
    description:
      "Netflix's cloud-native architecture on AWS spanning multiple regions. Covers auto-scaling, chaos engineering, multi-region failover, and microservice orchestration.",
    url: "https://netflixtechblog.com/",
    type: "case-study",
    category: "cloud",
    source: "Netflix Engineering",
    tags: ["AWS", "Multi-Region", "Chaos Engineering"],
  },
  {
    title: "How Cloudflare Built a Globally Distributed Edge Network",
    description:
      "Cloudflare's edge computing architecture spanning 300+ cities. Covers anycast routing, edge workers, KV storage, and serving content within 50ms of every user.",
    url: "https://blog.cloudflare.com/",
    type: "case-study",
    category: "cloud",
    source: "Cloudflare",
    tags: ["Edge Computing", "CDN", "Workers"],
  },
  {
    title: "AWS CDK — Cloud Development Kit",
    description:
      "Define AWS cloud resources using familiar programming languages. Synthesizes to CloudFormation with constructs for common patterns and L3 abstractions.",
    url: "https://github.com/aws/aws-cdk",
    type: "github",
    category: "cloud",
    source: "AWS",
    tags: ["CDK", "AWS", "TypeScript"],
  },
  {
    title: "How Figma Scaled to Multiple Cloud Regions",
    description:
      "Figma's journey to multi-region infrastructure. Covers data replication, failover strategies, latency optimization, and maintaining consistency across regions.",
    url: "https://www.figma.com/blog/",
    type: "case-study",
    category: "cloud",
    source: "Figma Engineering",
    tags: ["Multi-Region", "Failover", "Latency"],
  },

  /* ==================  Dart / Flutter  ================== */
  {
    title: "Dart Language Tour — Official",
    description:
      "The official Dart language tour covering variables, control flow, functions, classes, generics, async/await, isolates, and null safety from the Dart team.",
    url: "https://dart.dev/language",
    type: "ebook",
    category: "dart",
    source: "Dart Team",
    tags: ["Dart", "Language", "Null Safety"],
  },
  {
    title: "Flutter Official Documentation",
    description:
      "Comprehensive Flutter docs covering widgets, layouts, state management, navigation, animations, platform integration, and publishing to app stores.",
    url: "https://docs.flutter.dev/",
    type: "ebook",
    category: "dart",
    source: "Google",
    tags: ["Flutter", "Widgets", "State Management"],
  },
  {
    title: "Flutter — Google's UI Toolkit (Source)",
    description:
      "The open-source Flutter SDK. Build natively compiled apps for mobile, web, and desktop from a single Dart codebase with hot reload and expressive UI.",
    url: "https://github.com/flutter/flutter",
    type: "github",
    category: "dart",
    source: "Google",
    tags: ["Flutter", "Cross-Platform", "SDK"],
  },
  {
    title: "Flutter & Dart — The Complete Guide (Academind)",
    description:
      "Comprehensive course covering Dart fundamentals, Flutter widgets, state management (Provider, Riverpod), animations, Firebase, and building real-world apps.",
    url: "https://www.youtube.com/playlist?list=PL55RiY5tL51qUXDyBqx0OKBrO6gMl5ZR2",
    type: "playlist",
    category: "dart",
    source: "Academind",
    tags: ["Flutter", "Dart", "Full Course"],
  },
  {
    title: "Riverpod — Reactive State Management for Flutter",
    description:
      "Modern, compile-safe state management for Flutter. Provider reimagined with code generation, auto-dispose, and testability built in from the ground up.",
    url: "https://github.com/rrousselGit/riverpod",
    type: "github",
    category: "dart",
    source: "Remi Rousselet",
    tags: ["State Management", "Riverpod", "Reactive"],
  },
  {
    title: "Bloc — Predictable State Management",
    description:
      "Business Logic Component pattern for Flutter. Separates presentation from business logic using streams, events, and states with strong testing support.",
    url: "https://github.com/felangel/bloc",
    type: "github",
    category: "dart",
    source: "Felix Angelov",
    tags: ["Bloc", "Architecture", "Streams"],
  },
  {
    title: "Dart Frog — Backend Framework for Dart",
    description:
      "Minimalistic backend framework for Dart. Build REST APIs with middleware, routing, and dependency injection using the same language as your Flutter frontend.",
    url: "https://github.com/VeryGoodOpenSource/dart_frog",
    type: "github",
    category: "dart",
    source: "Very Good Ventures",
    tags: ["Backend", "API", "Full-Stack Dart"],
  },
  {
    title: "How BMW Built Their App with Flutter",
    description:
      "BMW's adoption of Flutter for their My BMW app used by millions. Covers cross-platform consistency, custom UI components, and integration with vehicle APIs.",
    url: "https://flutter.dev/showcase/bmw",
    type: "case-study",
    category: "dart",
    source: "Flutter Showcase",
    tags: ["BMW", "Production", "Cross-Platform"],
  },
  {
    title: "How Google Pay Rebuilt with Flutter",
    description:
      "Google Pay's migration to Flutter for a unified codebase. Covers performance benchmarks, platform-specific adaptations, and maintaining feature parity across iOS and Android.",
    url: "https://flutter.dev/showcase/google-pay",
    type: "case-study",
    category: "dart",
    source: "Flutter Showcase",
    tags: ["Google Pay", "Migration", "Performance"],
  },
  {
    title: "How Alibaba Uses Flutter for Xianyu",
    description:
      "Alibaba's Xianyu app serving 50M+ users built with Flutter. Covers hybrid integration, custom rendering, and Flutter's performance in a high-traffic Chinese market app.",
    url: "https://flutter.dev/showcase",
    type: "case-study",
    category: "dart",
    source: "Alibaba",
    tags: ["Alibaba", "Scale", "Hybrid"],
  },
  {
    title: "Effective Dart — Style Guide",
    description:
      "Official Dart style guide covering naming conventions, formatting, documentation, design patterns, and idiomatic Dart usage endorsed by the Dart team.",
    url: "https://dart.dev/effective-dart",
    type: "ebook",
    category: "dart",
    source: "Dart Team",
    tags: ["Style Guide", "Best Practices", "Idioms"],
  },
  {
    title: "Serverpod — Full-Stack Dart Framework",
    description:
      "Complete backend framework for Flutter with ORM, authentication, file uploads, web sockets, scheduled tasks, and auto-generated client code for type-safe APIs.",
    url: "https://github.com/serverpod/serverpod",
    type: "github",
    category: "dart",
    source: "Serverpod",
    tags: ["Full-Stack", "ORM", "Code Generation"],
  },

  /* ==================  Kotlin  ================== */
  {
    title: "Kotlin Official Documentation",
    description:
      "The complete Kotlin reference covering coroutines, null safety, extensions, data classes, sealed classes, DSLs, multiplatform, and interop with Java.",
    url: "https://kotlinlang.org/docs/home.html",
    type: "ebook",
    category: "kotlin",
    source: "JetBrains",
    tags: ["Kotlin", "Language", "Reference"],
  },
  {
    title: "Kotlin Programming Language (Source)",
    description:
      "The open-source Kotlin compiler and standard library. A modern, concise, and safe programming language that runs on JVM, Android, JavaScript, and Native platforms.",
    url: "https://github.com/JetBrains/kotlin",
    type: "github",
    category: "kotlin",
    source: "JetBrains",
    tags: ["Compiler", "JVM", "Open Source"],
  },
  {
    title: "Android Development with Kotlin — Google",
    description:
      "Google's official Android development courses using Kotlin. Covers Jetpack Compose, architecture components, navigation, Room, WorkManager, and Material Design.",
    url: "https://developer.android.com/courses",
    type: "course",
    category: "kotlin",
    source: "Google",
    tags: ["Android", "Jetpack Compose", "Official"],
  },
  {
    title: "Kotlin Coroutines Guide — Official",
    description:
      "Comprehensive guide to Kotlin coroutines. Covers structured concurrency, flows, channels, supervisors, exception handling, and testing concurrent code.",
    url: "https://kotlinlang.org/docs/coroutines-guide.html",
    type: "ebook",
    category: "kotlin",
    source: "JetBrains",
    tags: ["Coroutines", "Async", "Concurrency"],
  },
  {
    title: "Ktor — Asynchronous Kotlin Web Framework",
    description:
      "Lightweight Kotlin framework for building async servers and clients. Coroutine-based, multiplatform, with websockets, auth, and serialization built in.",
    url: "https://github.com/ktorio/ktor",
    type: "github",
    category: "kotlin",
    source: "JetBrains",
    tags: ["Ktor", "Server", "Async"],
  },
  {
    title: "Jetpack Compose — Modern Android UI",
    description:
      "Android's modern declarative UI toolkit. Build native UIs with less code, interactive previews, and powerful Kotlin APIs replacing XML layouts.",
    url: "https://developer.android.com/jetpack/compose",
    type: "course",
    category: "kotlin",
    source: "Google",
    tags: ["Compose", "Declarative UI", "Android"],
  },
  {
    title: "Kotlin Multiplatform Mobile (KMM)",
    description:
      "Share business logic between Android and iOS while keeping native UIs. Covers expect/actual declarations, platform-specific code, and Gradle configuration.",
    url: "https://kotlinlang.org/docs/multiplatform-mobile-getting-started.html",
    type: "course",
    category: "kotlin",
    source: "JetBrains",
    tags: ["KMM", "Cross-Platform", "iOS"],
  },
  {
    title: "Spring Boot with Kotlin — Official Guide",
    description:
      "Building production-grade Spring Boot applications with idiomatic Kotlin. Covers WebFlux, coroutines, data classes for DTOs, and extension functions for cleaner code.",
    url: "https://spring.io/guides/tutorials/spring-boot-kotlin",
    type: "course",
    category: "kotlin",
    source: "Spring",
    tags: ["Spring Boot", "Backend", "Enterprise"],
  },
  {
    title: "How Pinterest Adopted Kotlin for Android",
    description:
      "Pinterest's migration from Java to Kotlin for Android. Covers gradual adoption strategy, interop challenges, developer productivity gains, and crash rate reduction.",
    url: "https://medium.com/pinterest-engineering",
    type: "case-study",
    category: "kotlin",
    source: "Pinterest Engineering",
    tags: ["Migration", "Android", "Java Interop"],
  },
  {
    title: "How Square Uses Kotlin for Android & Backend",
    description:
      "Square's full-stack Kotlin adoption. Covers using Kotlin on Android (Cash App), on the backend (OkHttp, Retrofit, Moshi), and the productivity benefits observed.",
    url: "https://developer.squareup.com/blog",
    type: "case-study",
    category: "kotlin",
    source: "Square Engineering",
    tags: ["Full-Stack", "OkHttp", "Cash App"],
  },
  {
    title: "How Netflix Uses Kotlin for Backend Services",
    description:
      "Netflix's adoption of Kotlin for JVM microservices. Covers coroutines for async I/O, DSL-based configuration, Spring integration, and developer experience improvements.",
    url: "https://netflixtechblog.com/",
    type: "case-study",
    category: "kotlin",
    source: "Netflix Engineering",
    tags: ["Backend", "Coroutines", "Microservices"],
  },
  {
    title: "How Uber Migrated to Kotlin for Android",
    description:
      "Uber's large-scale migration of their Android codebase from Java to Kotlin. Covers automated conversion tooling, testing strategies, and scaling across 100+ engineers.",
    url: "https://www.uber.com/blog/kotlin-migration/",
    type: "case-study",
    category: "kotlin",
    source: "Uber Engineering",
    tags: ["Migration", "Automation", "Large Scale"],
  },
  {
    title: "Arrow — Functional Programming for Kotlin",
    description:
      "Idiomatic functional programming library for Kotlin. Typed errors, immutable data, optics, coroutine-based effects, and type-safe concurrency patterns.",
    url: "https://github.com/arrow-kt/arrow",
    type: "github",
    category: "kotlin",
    source: "Arrow-kt",
    tags: ["Functional", "Type-Safe", "Effects"],
  },
  {
    title: "Kotlin for Competitive Programming",
    description:
      "JetBrains' guide to using Kotlin in competitive programming. Covers I/O optimization, collection operations, algorithms, and common problem-solving patterns.",
    url: "https://kotlinlang.org/docs/competitive-programming.html",
    type: "ebook",
    category: "kotlin",
    source: "JetBrains",
    tags: ["Algorithms", "Competitive", "Problem Solving"],
  },

  /* ==================  Rust  ================== */
  {
    title: "The Rust Programming Language Book",
    description:
      "The official Rust book. Covers ownership, borrowing, lifetimes, traits, generics, error handling, concurrency, unsafe code, and building CLI/web applications.",
    url: "https://doc.rust-lang.org/book/",
    type: "ebook",
    category: "rust",
    source: "Rust Foundation",
    tags: ["Ownership", "Borrowing", "Official"],
  },
  {
    title: "Rust By Example — Interactive",
    description:
      "Learn Rust through annotated examples that run in the browser. Covers primitives, custom types, flow control, traits, error handling, generics, and more.",
    url: "https://doc.rust-lang.org/rust-by-example/",
    type: "course",
    category: "rust",
    source: "Rust Foundation",
    tags: ["Examples", "Interactive", "Beginner"],
  },
  {
    title: "Rust Language Source Code",
    description:
      "The Rust compiler, standard library, and core tools. A language focused on reliability, performance, and productivity with zero-cost abstractions.",
    url: "https://github.com/rust-lang/rust",
    type: "github",
    category: "rust",
    source: "Rust Foundation",
    tags: ["Compiler", "Systems", "Open Source"],
  },
  {
    title: "Rustlings — Learn Rust by Fixing Exercises",
    description:
      "Small exercises to learn Rust by reading and fixing code. Covers variables, functions, structs, enums, error handling, traits, iterators, and smart pointers.",
    url: "https://github.com/rust-lang/rustlings",
    type: "github",
    category: "rust",
    source: "Rust Foundation",
    tags: ["Exercises", "Hands-on", "Learning"],
  },
  {
    title: "Tokio — Async Runtime for Rust",
    description:
      "The most widely used async runtime for Rust. Provides async I/O, timers, channels, synchronization, and a multi-threaded work-stealing scheduler.",
    url: "https://github.com/tokio-rs/tokio",
    type: "github",
    category: "rust",
    source: "Tokio",
    tags: ["Async", "Runtime", "Concurrency"],
  },
  {
    title: "Actix Web — High-Performance Rust Web Framework",
    description:
      "Blazingly fast web framework for Rust. Actor-based architecture, websockets, middleware, and consistently ranks among the fastest web frameworks in TechEmpower benchmarks.",
    url: "https://github.com/actix/actix-web",
    type: "github",
    category: "rust",
    source: "Actix",
    tags: ["Web", "Performance", "Actor Model"],
  },
  {
    title: "Axum — Ergonomic Rust Web Framework",
    description:
      "Web framework from the Tokio team. Tower-based middleware, type-safe extractors, and seamless async/await integration for building robust HTTP services.",
    url: "https://github.com/tokio-rs/axum",
    type: "github",
    category: "rust",
    source: "Tokio",
    tags: ["Axum", "Tower", "Ergonomic"],
  },
  {
    title: "Jon Gjengset — Rust for Rustaceans (YouTube)",
    description:
      "Advanced Rust concepts from Jon Gjengset. Deep dives into lifetimes, trait objects, async internals, unsafe code, and building real-world Rust applications.",
    url: "https://www.youtube.com/c/JonGjengset",
    type: "playlist",
    category: "rust",
    source: "Jon Gjengset",
    tags: ["Advanced", "Deep Dive", "Internals"],
  },
  {
    title: "How Discord Switched from Go to Rust",
    description:
      "Discord's migration of their Read States service from Go to Rust. Covers latency improvements, memory management benefits, and eliminating Go's GC pauses.",
    url: "https://discord.com/blog/why-discord-is-switching-from-go-to-rust",
    type: "case-study",
    category: "rust",
    source: "Discord Engineering",
    tags: ["Go vs Rust", "Performance", "GC-Free"],
  },
  {
    title: "How Cloudflare Uses Rust for Edge Computing",
    description:
      "Cloudflare's extensive use of Rust for edge infrastructure. Covers their HTTP proxy (Pingora), Workers runtime, and why they chose Rust over C/C++ for performance-critical paths.",
    url: "https://blog.cloudflare.com/tag/rust/",
    type: "case-study",
    category: "rust",
    source: "Cloudflare",
    tags: ["Edge", "Pingora", "High Performance"],
  },
  {
    title: "How Figma Adopted Rust for Performance",
    description:
      "Figma's adoption of Rust for their multiplayer server. Covers why they moved from TypeScript to Rust for specific hot paths, achieving 10x performance improvement.",
    url: "https://www.figma.com/blog/rust-in-production-at-figma/",
    type: "case-study",
    category: "rust",
    source: "Figma Engineering",
    tags: ["TypeScript to Rust", "10x Performance", "Server"],
  },
  {
    title: "How AWS Uses Rust for Firecracker",
    description:
      "AWS built Firecracker — the micro-VM technology behind Lambda and Fargate — entirely in Rust. Covers memory safety, performance, and why Rust was chosen over C.",
    url: "https://aws.amazon.com/blogs/opensource/why-aws-loves-rust-and-how-wed-like-to-help/",
    type: "case-study",
    category: "rust",
    source: "AWS",
    tags: ["Firecracker", "Lambda", "Micro-VM"],
  },
  {
    title: "How Microsoft Uses Rust to Reduce Memory Bugs",
    description:
      "Microsoft's research showing 70% of CVEs are memory safety issues. How Rust's ownership model eliminates these bugs at compile time for Windows and Azure code.",
    url: "https://msrc.microsoft.com/blog/2019/07/a-proactive-approach-to-more-secure-code/",
    type: "case-study",
    category: "rust",
    source: "Microsoft MSRC",
    tags: ["Memory Safety", "CVE Reduction", "Windows"],
  },
  {
    title: "How 1Password Rebuilt in Rust",
    description:
      "1Password's complete rewrite of their core crypto and sync engine in Rust. Covers cross-platform code sharing, WASM compilation for browser, and security benefits.",
    url: "https://blog.1password.com/1passwordx-]]september-2019-release/",
    type: "case-study",
    category: "rust",
    source: "1Password",
    tags: ["Crypto", "WASM", "Cross-Platform"],
  },
  {
    title: "Serde — Serialization Framework for Rust",
    description:
      "The de facto serialization framework for Rust. Zero-cost JSON, YAML, TOML, MessagePack, and custom format support with derive macros for automatic implementation.",
    url: "https://github.com/serde-rs/serde",
    type: "github",
    category: "rust",
    source: "Serde",
    tags: ["Serialization", "JSON", "Zero-Cost"],
  },
  {
    title: "Zero To Production In Rust",
    description:
      "Hands-on book for building production-ready APIs in Rust. Covers project setup, testing, CI/CD, error handling, observability, and deploying real Rust services.",
    url: "https://www.zero2prod.com/",
    type: "ebook",
    category: "rust",
    source: "Luca Palmieri",
    tags: ["Production", "API", "Backend"],
  },
  {
    title: "Rust Design Patterns — Unofficial Book",
    description:
      "Catalog of idiomatic Rust design patterns, anti-patterns, and common idioms. Covers builder pattern, newtype, typestate, RAII, and functional patterns in Rust.",
    url: "https://rust-unofficial.github.io/patterns/",
    type: "ebook",
    category: "rust",
    source: "Community",
    tags: ["Design Patterns", "Idioms", "Best Practices"],
  },
];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

const ITEMS_PER_PAGE = 24;

export default function ResourcesPage() {
  const [activeCategory, setActiveCategory] = useState<ResourceCategory>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeType, setActiveType] = useState<ResourceType | "all">("all");
  const [visibleCount, setVisibleCount] = useState(ITEMS_PER_PAGE);

  // Merge hand-curated + extra resources
  const ALL_RESOURCES = useMemo(() => [
    ...RESOURCES,
    ...(EXTRA_RESOURCES as Resource[]),
  ], []);

  const filtered = useMemo(() => ALL_RESOURCES.filter((r) => {
    const matchesCategory =
      activeCategory === "all" || r.category === activeCategory;
    const matchesType = activeType === "all" || r.type === activeType;
    const matchesSearch =
      searchQuery === "" ||
      r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesType && matchesSearch;
  }), [ALL_RESOURCES, activeCategory, activeType, searchQuery]);

  // Reset visible count when filters change
  const paginatedFiltered = filtered.slice(0, visibleCount);
  const hasMore = visibleCount < filtered.length;

  const grouped = filtered.reduce<Record<string, Resource[]>>((acc, r) => {
    const cat = CATEGORIES.find((c) => c.id === r.category);
    const key = cat?.label || "Other";
    if (!acc[key]) acc[key] = [];
    acc[key].push(r);
    return acc;
  }, {});

  const typeCounts = ALL_RESOURCES.reduce<Record<string, number>>((acc, r) => {
    acc[r.type] = (acc[r.type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="mx-auto max-w-5xl">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 text-center"
      >
        <span className="inline-flex items-center gap-2 rounded-xl bg-card shadow-sm border border-border px-3.5 py-1.5 text-xs font-semibold text-primary mb-4">
          <GraduationCap className="h-3.5 w-3.5" /> Curated Learning Library
        </span>
        <h1 className="mt-4 text-4xl font-serif font-bold tracking-tight md:text-5xl text-[#1E1F1B]">
          Developer Resources
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-base leading-relaxed text-muted-foreground">
          Handpicked case studies, eBooks, GitHub repositories, and university
          lecture playlists from MIT, Stanford, and CMU to level up across every
          major tech stack.
        </p>
      </motion.div>

      {/* Search + Filters */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="bg-card shadow-sm border border-border rounded-2xl border border-border p-5 mb-6 shadow-sm"
      >
        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            placeholder="Search resources by title, description, or tag..."
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setVisibleCount(ITEMS_PER_PAGE); }}
            className="w-full bg-card shadow-sm border border-border rounded-xl border border-border pl-10 pr-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
          />
        </div>

        {/* Category pills */}
        <div className="flex flex-wrap gap-2 mb-3">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground mr-1">
            <Filter className="w-3 h-3" /> Category
          </div>
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => { setActiveCategory(cat.id); setVisibleCount(ITEMS_PER_PAGE); }}
              className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all duration-200 cursor-pointer ${
                activeCategory === cat.id
                  ? "border-primary/35 bg-brand/12 text-primary shadow-[0_4px_16px_hsla(270,70%,60%,0.12)]"
                  : "border-transparent text-muted-foreground hover:border-primary/15 hover:bg-accent/10 hover:text-foreground"
              }`}
            >
              {cat.icon} {cat.label}
            </button>
          ))}
        </div>

        {/* Type pills */}
        <div className="flex flex-wrap gap-2">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground mr-1">
            <Filter className="w-3 h-3" /> Type
          </div>
          <button
            onClick={() => { setActiveType("all"); setVisibleCount(ITEMS_PER_PAGE); }}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-all cursor-pointer ${
              activeType === "all"
                ? "border-primary/35 bg-brand/12 text-primary"
                : "border-transparent text-muted-foreground hover:border-primary/15 hover:bg-accent/10"
            }`}
          >
            All Types
          </button>
          {(Object.keys(TYPE_META) as ResourceType[]).map((type) => {
            const meta = TYPE_META[type];
            return (
              <button
                key={type}
                onClick={() => { setActiveType(type); setVisibleCount(ITEMS_PER_PAGE); }}
                className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all cursor-pointer ${
                  activeType === type
                    ? `${meta.color} border`
                    : "border-transparent text-muted-foreground hover:border-primary/15 hover:bg-accent/10"
                }`}
              >
                {meta.icon} {meta.label}{" "}
                <span className="text-[10px] opacity-60">
                  ({typeCounts[type] || 0})
                </span>
              </button>
            );
          })}
        </div>
      </motion.div>

      {/* Stats bar */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6"
      >
        {(Object.keys(TYPE_META) as ResourceType[]).map((type) => {
          const meta = TYPE_META[type];
          return (
            <div
              key={type}
              className="bg-card shadow-sm border border-border border border-border rounded-xl px-3.5 py-3 shadow-sm"
            >
              <div
                className={`flex items-center gap-2 text-xs font-semibold ${meta.color.split(" ")[1]}`}
              >
                {meta.icon} {meta.label}
              </div>
              <p className="text-lg font-extrabold mt-1">
                {typeCounts[type] || 0}
              </p>
            </div>
          );
        })}
      </motion.div>

      {/* Results */}
      {filtered.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-card shadow-sm border border-border border border-border rounded-2xl p-12 text-center shadow-sm"
        >
          <Search className="w-8 h-8 text-muted-foreground mx-auto mb-3 opacity-50" />
          <p className="text-sm text-muted-foreground">
            No resources match your current filters. Try a different category or
            search term.
          </p>
        </motion.div>
      ) : activeCategory === "all" && searchQuery === "" && activeType === "all" ? (
        /* Grouped view — paginated */
        <div className="space-y-8">
          {(() => {
            let count = 0;
            return Object.entries(grouped).map(([groupLabel, items], gi) => {
              if (count >= visibleCount) return null;
              const remaining = visibleCount - count;
              const slicedItems = items.slice(0, remaining);
              count += slicedItems.length;
              return (
                <motion.div
                  key={groupLabel}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 * Math.min(gi, 5) }}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <h2 className="text-lg font-bold tracking-tight">
                      {groupLabel}
                    </h2>
                    <div className="flex-1 h-px bg-border" />
                    <span className="text-xs text-muted-foreground font-mono">
                      {items.length} resources
                    </span>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    {slicedItems.map((r) => (
                      <ResourceCard key={r.url} resource={r} />
                    ))}
                  </div>
                </motion.div>
              );
            });
          })()}
        </div>
      ) : (
        /* Flat filtered view — paginated */
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          <p className="text-xs text-muted-foreground font-mono">
            {filtered.length} resource{filtered.length !== 1 ? "s" : ""} found
            {paginatedFiltered.length < filtered.length && (
              <> · showing {paginatedFiltered.length}</>
            )}
          </p>
          <div className="grid gap-3 md:grid-cols-2">
            {paginatedFiltered.map((r) => (
              <ResourceCard key={r.url} resource={r} />
            ))}
          </div>
        </motion.div>
      )}

      {/* Load More button */}
      {hasMore && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-3 mt-8 mb-4"
        >
          <p className="text-xs text-muted-foreground font-mono">
            Showing {Math.min(visibleCount, filtered.length)} of {filtered.length} resources
          </p>
          <button
            onClick={() => setVisibleCount((prev) => prev + ITEMS_PER_PAGE)}
            className="group relative inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/20 transition-all duration-300 hover:shadow-xl hover:shadow-primary/30 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
          >
            <Layers className="w-4 h-4" />
            Load More Resources
            <span className="ml-1 rounded-lg bg-card/40 px-2 py-0.5 text-[11px] font-mono">
              +{Math.min(ITEMS_PER_PAGE, filtered.length - visibleCount)}
            </span>
          </button>
        </motion.div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Resource Card                                                      */
/* ------------------------------------------------------------------ */

function ResourceCard({ resource }: { resource: Resource }) {
  const meta = TYPE_META[resource.type];

  return (
    <a
      href={resource.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group bg-card shadow-sm border border-border rounded-2xl border border-border p-5 shadow-sm transition-all duration-300 hover:border-primary/40 block"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <span
          className={`inline-flex items-center gap-1.5 rounded-xl border px-2.5 py-1 text-[11px] font-semibold ${meta.color}`}
        >
          {meta.icon} {meta.label}
        </span>
        <ExternalLink className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5" />
      </div>

      <h3 className="text-sm font-bold leading-6 text-foreground mb-2 group-hover:text-primary transition-colors">
        {resource.title}
      </h3>
      <p className="text-xs leading-relaxed text-muted-foreground mb-3 line-clamp-3">
        {resource.description}
      </p>

      <div className="flex items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {resource.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 rounded-xl text-[10px] font-mono bg-muted/50 border border-border text-muted-foreground"
            >
              {tag}
            </span>
          ))}
        </div>
        <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary whitespace-nowrap">
          {resource.source}
        </span>
      </div>
    </a>
  );
}
