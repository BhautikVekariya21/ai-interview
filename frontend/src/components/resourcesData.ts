/* ------------------------------------------------------------------ */
/*  Additional resources – auto-generated pool                         */
/*  These supplement the hand-curated entries in ResourcesPage.tsx      */
/* ------------------------------------------------------------------ */

export interface Resource {
  title: string;
  description: string;
  url: string;
  type: "case-study" | "ebook" | "github" | "playlist" | "course";
  category:
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
  source: string;
  tags: string[];
}

const EXTRA_RESOURCES: Resource[] = [
  /* ==================  AI / ML (extra)  ================== */
  { title: "DeepMind AlphaFold — Protein Structure Prediction", description: "DeepMind's breakthrough AI system predicting 3D structures of proteins from amino-acid sequences. Covers attention mechanisms, evolutionary data, and biological applications.", url: "https://github.com/deepmind/alphafold", type: "github", category: "ai-ml", source: "DeepMind", tags: ["Biology", "Proteins", "Attention"] },
  { title: "Stable Diffusion — Open Source Image Generation", description: "Latent diffusion model for generating images from text prompts. Covers U-Net architecture, CLIP text encoder, VAE decoder, and LoRA fine-tuning techniques.", url: "https://github.com/CompVis/stable-diffusion", type: "github", category: "ai-ml", source: "CompVis", tags: ["Diffusion", "Image Gen", "Latent Space"] },
  { title: "YOLOv8 — Real-Time Object Detection", description: "State-of-the-art object detection, segmentation, and classification model. Covers anchor-free detection, multi-task learning, and edge deployment optimization.", url: "https://github.com/ultralytics/ultralytics", type: "github", category: "ai-ml", source: "Ultralytics", tags: ["Object Detection", "YOLO", "Real-Time"] },
  { title: "MLflow — ML Lifecycle Management", description: "Open-source platform for managing the complete ML lifecycle. Experiment tracking, reproducible runs, model packaging, and deployment to any serving environment.", url: "https://github.com/mlflow/mlflow", type: "github", category: "ai-ml", source: "Databricks", tags: ["MLOps", "Tracking", "Deployment"] },
  { title: "Weights & Biases — ML Experiment Tracking", description: "Developer tools for ML experiment tracking, dataset versioning, and model management. Interactive dashboards, hyperparameter sweeps, and team collaboration.", url: "https://wandb.ai/site", type: "course", category: "ai-ml", source: "W&B", tags: ["Tracking", "Visualization", "Teams"] },
  { title: "Stanford CS 236 — Deep Generative Models", description: "Stanford course on deep generative models. Covers VAEs, GANs, normalizing flows, autoregressive models, diffusion models, and energy-based models.", url: "https://deepgenerativemodels.github.io/", type: "course", category: "ai-ml", source: "Stanford", tags: ["Generative", "VAE", "GAN"] },
  { title: "UC Berkeley CS 285 — Deep Reinforcement Learning", description: "Berkeley's graduate RL course. Covers policy gradients, actor-critic, model-based RL, offline RL, multi-task learning, and real-world RL applications.", url: "https://rail.eecs.berkeley.edu/deeprlcourse/", type: "course", category: "ai-ml", source: "UC Berkeley", tags: ["Deep RL", "Policy Gradient", "Actor-Critic"] },
  { title: "JAX — High-Performance ML Research", description: "Google's composable transformations library. Autograd + XLA for GPU/TPU acceleration with functional transformations: grad, jit, vmap, and pmap.", url: "https://github.com/google/jax", type: "github", category: "ai-ml", source: "Google", tags: ["JAX", "XLA", "Functional"] },
  { title: "PyTorch Lightning — Structured DL Training", description: "Lightweight PyTorch wrapper for high-performance AI research. Removes boilerplate code while keeping flexibility. Distributed training, mixed precision, and logging.", url: "https://github.com/Lightning-AI/pytorch-lightning", type: "github", category: "ai-ml", source: "Lightning AI", tags: ["PyTorch", "Training", "Distributed"] },
  { title: "Whisper — OpenAI Speech Recognition", description: "General-purpose speech recognition model trained on 680K hours of multilingual audio. Robust ASR, translation, and language identification.", url: "https://github.com/openai/whisper", type: "github", category: "ai-ml", source: "OpenAI", tags: ["Speech", "ASR", "Multilingual"] },
  { title: "DALL-E Research — Text-to-Image Paper", description: "OpenAI's research on generating images from text descriptions using transformers. Covers zero-shot generation, CLIP-guided diffusion, and image editing.", url: "https://openai.com/research/dall-e", type: "case-study", category: "ai-ml", source: "OpenAI", tags: ["Text-to-Image", "CLIP", "Generation"] },
  { title: "How Tesla Uses AI for Self-Driving", description: "Tesla's vision-only approach to autonomous driving. Covers BEV networks, occupancy networks, planning with neural nets, and training on fleet data.", url: "https://www.tesla.com/AI", type: "case-study", category: "ai-ml", source: "Tesla", tags: ["Autonomous", "Vision", "Self-Driving"] },
  { title: "GPT-4 Technical Report", description: "OpenAI's technical report on GPT-4. Covers multimodal capabilities, benchmark performance, safety alignment through RLHF, and limitations.", url: "https://openai.com/research/gpt-4", type: "ebook", category: "ai-ml", source: "OpenAI", tags: ["GPT-4", "LLM", "RLHF"] },
  { title: "Attention Is All You Need — Original Paper", description: "The landmark paper introducing the Transformer architecture. Self-attention mechanisms, multi-head attention, positional encodings, and the foundation of modern NLP.", url: "https://arxiv.org/abs/1706.03762", type: "ebook", category: "ai-ml", source: "Google Brain", tags: ["Transformer", "Attention", "Foundational"] },
  { title: "Stanford CS 330 — Multi-Task & Meta-Learning", description: "Stanford course on learning to learn. Covers few-shot learning, meta-learning algorithms (MAML, Prototypical Networks), multi-task architectures, and curriculum learning.", url: "https://cs330.stanford.edu/", type: "course", category: "ai-ml", source: "Stanford", tags: ["Meta-Learning", "Few-Shot", "Multi-Task"] },
  { title: "Detectron2 — Facebook's Object Detection Platform", description: "Meta's detection and segmentation library. Panoptic segmentation, instance segmentation, keypoint detection, and DensePose with modular design.", url: "https://github.com/facebookresearch/detectron2", type: "github", category: "ai-ml", source: "Meta AI", tags: ["Detection", "Segmentation", "Computer Vision"] },
  { title: "How Google Trains Gemini at Scale", description: "Google's approach to training the Gemini family of models. Covers distributed training infrastructure, data curation, evaluation methodology, and safety alignment.", url: "https://deepmind.google/technologies/gemini/", type: "case-study", category: "ai-ml", source: "Google DeepMind", tags: ["Gemini", "Scale", "Training"] },
  { title: "Gradio — ML Demo Interfaces", description: "Build web UIs for ML models in minutes. Supports any Python ML framework with customizable components, API generation, and Hugging Face Spaces integration.", url: "https://github.com/gradio-app/gradio", type: "github", category: "ai-ml", source: "Gradio", tags: ["Demo", "UI", "Prototyping"] },
  { title: "Deep Learning Specialization — Andrew Ng", description: "Five-course specialization covering neural networks, regularization, optimization, CNNs, sequence models, and attention mechanisms with hands-on projects.", url: "https://www.coursera.org/specializations/deep-learning", type: "course", category: "ai-ml", source: "Coursera", tags: ["Specialization", "Neural Nets", "Comprehensive"] },
  { title: "How Waymo Applies ML to Autonomous Driving", description: "Waymo's perception and prediction stack. Covers 3D point cloud processing, sensor fusion, behavior prediction, and continuous learning from millions of miles driven.", url: "https://waymo.com/research/", type: "case-study", category: "ai-ml", source: "Waymo", tags: ["Perception", "Point Cloud", "Prediction"] },
  { title: "TimeSeries Foundation Models — TimesFM", description: "Google's foundation model for time series forecasting. Zero-shot prediction across domains without task-specific training, covering financial, weather, and demand data.", url: "https://github.com/google-research/timesfm", type: "github", category: "ai-ml", source: "Google Research", tags: ["Time Series", "Forecasting", "Foundation"] },
  { title: "How Duolingo Uses AI for Language Learning", description: "Duolingo's AI engine for adaptive learning. Covers spaced repetition optimization, NLP for exercise generation, and personalized difficulty adjustment.", url: "https://blog.duolingo.com/tag/engineering/", type: "case-study", category: "ai-ml", source: "Duolingo", tags: ["EdTech", "NLP", "Adaptive"] },
  { title: "ONNX Runtime — Cross-Platform ML Inference", description: "High-performance inference engine for ONNX models. Hardware acceleration for CPU, GPU, FPGA with optimizations for production deployment across platforms.", url: "https://github.com/microsoft/onnxruntime", type: "github", category: "ai-ml", source: "Microsoft", tags: ["Inference", "ONNX", "Optimization"] },
  { title: "Stanford HAI — AI Ethics & Policy", description: "Stanford's Institute for Human-Centered AI. Research and policy resources on AI fairness, accountability, transparency, and societal impact.", url: "https://hai.stanford.edu/", type: "ebook", category: "ai-ml", source: "Stanford HAI", tags: ["Ethics", "Policy", "Fairness"] },
  { title: "How Anthropic Builds Safe AI Systems", description: "Anthropic's research on AI safety. Constitutional AI, RLHF improvements, interpretability research, and techniques for building helpful and harmless AI.", url: "https://www.anthropic.com/research", type: "case-study", category: "ai-ml", source: "Anthropic", tags: ["Safety", "Constitutional AI", "Alignment"] },

  /* ==================  Frontend (extra)  ================== */
  { title: "Remix — Full Stack Web Framework", description: "React-based framework focused on web standards and modern UX. Nested routes, progressive enhancement, error boundaries, and server/client data loading.", url: "https://github.com/remix-run/remix", type: "github", category: "frontend", source: "Shopify", tags: ["Remix", "Full Stack", "Progressive"] },
  { title: "Astro — Content-Focused Web Framework", description: "Build faster websites with less JavaScript. Islands architecture, zero JS by default, multi-framework support (React, Vue, Svelte), and automatic code splitting.", url: "https://github.com/withastro/astro", type: "github", category: "frontend", source: "Astro", tags: ["Astro", "Static", "Islands"] },
  { title: "Zustand — Lightweight React State", description: "Small, fast, and scalable state management for React. No boilerplate, no providers, hooks-based API with middleware support and devtools integration.", url: "https://github.com/pmndrs/zustand", type: "github", category: "frontend", source: "Poimandres", tags: ["State", "React", "Minimal"] },
  { title: "TanStack Query — Async State Management", description: "Powerful asynchronous state management for React, Vue, Solid. Server state caching, background refetching, pagination, infinite queries, and optimistic updates.", url: "https://github.com/TanStack/query", type: "github", category: "frontend", source: "TanStack", tags: ["Data Fetching", "Cache", "Async"] },
  { title: "Framer Motion — React Animation Library", description: "Production-ready animation library for React. Declarative animations, gestures, layout animations, scroll-based animations, and shared layout transitions.", url: "https://github.com/framer/motion", type: "github", category: "frontend", source: "Framer", tags: ["Animation", "Gestures", "Layout"] },
  { title: "Vite — Next Generation Frontend Tooling", description: "Lightning-fast dev server with HMR, Rollup-based production builds, framework-agnostic with first-class support for React, Vue, Svelte, and more.", url: "https://github.com/vitejs/vite", type: "github", category: "frontend", source: "Evan You", tags: ["Build Tool", "HMR", "ESM"] },
  { title: "Three.js — WebGL 3D Graphics", description: "The most popular 3D library for the web. Scenes, cameras, lights, materials, geometries, post-processing, and physics with WebGL and WebGPU renderers.", url: "https://github.com/mrdoob/three.js", type: "github", category: "frontend", source: "mrdoob", tags: ["3D", "WebGL", "Graphics"] },
  { title: "Turborepo — High-Performance Monorepo Build", description: "Incremental build system for JavaScript/TypeScript monorepos. Remote caching, parallel execution, task pipelines, and seamless integration with existing tools.", url: "https://github.com/vercel/turborepo", type: "github", category: "frontend", source: "Vercel", tags: ["Monorepo", "Build", "Caching"] },
  { title: "How Vercel Optimizes Next.js Performance", description: "Vercel's approach to web performance. Covers ISR, edge functions, image optimization, font loading, and Core Web Vitals improvements at scale.", url: "https://vercel.com/blog", type: "case-study", category: "frontend", source: "Vercel", tags: ["Performance", "ISR", "Edge"] },
  { title: "Playwright — Cross-Browser Testing", description: "Microsoft's end-to-end testing framework. Auto-wait, web-first assertions, tracing, screenshot comparison, and support for Chromium, Firefox, and WebKit.", url: "https://github.com/microsoft/playwright", type: "github", category: "frontend", source: "Microsoft", tags: ["Testing", "E2E", "Cross-Browser"] },
  { title: "How Shopify Built Hydrogen for Commerce", description: "Shopify's React framework for custom storefronts. Covers Remix integration, Storefront API, server components, and optimized commerce patterns.", url: "https://shopify.engineering/", type: "case-study", category: "frontend", source: "Shopify", tags: ["Commerce", "React", "Remix"] },
  { title: "SolidJS — Fine-Grained Reactive Framework", description: "Declarative JavaScript library for building UIs. True reactivity without virtual DOM, compiled templates, and React-like API with superior performance.", url: "https://github.com/solidjs/solid", type: "github", category: "frontend", source: "SolidJS", tags: ["Reactive", "No VDOM", "Performance"] },
  { title: "Radix UI — Accessible Component Primitives", description: "Unstyled, accessible UI component primitives for React. Dialog, dropdown, tooltip, popover, and more with full keyboard navigation and ARIA support.", url: "https://github.com/radix-ui/primitives", type: "github", category: "frontend", source: "Radix", tags: ["A11y", "Primitives", "Headless"] },
  { title: "ShadCN UI — Beautifully Designed Components", description: "Re-usable components built with Radix UI and Tailwind CSS. Copy-paste components that you own, with full customization and accessibility built in.", url: "https://github.com/shadcn-ui/ui", type: "github", category: "frontend", source: "shadcn", tags: ["Components", "Tailwind", "Copy-Paste"] },
  { title: "How Notion Achieved <100ms Page Loads", description: "Notion's frontend performance optimization journey. Covers bundle splitting, lazy loading, caching strategies, and WASM-powered rendering.", url: "https://www.notion.so/blog/faster-page-loads", type: "case-study", category: "frontend", source: "Notion", tags: ["Performance", "Bundle", "WASM"] },
  { title: "How GitHub Rebuilt Their Frontend Architecture", description: "GitHub's migration from Rails views to React. Covers progressive enhancement, turbo frames, custom elements, and maintaining backward compatibility.", url: "https://github.blog/engineering/", type: "case-study", category: "frontend", source: "GitHub", tags: ["Migration", "Architecture", "Progressive"] },
  { title: "D3.js — Data-Driven Documents", description: "The gold standard for data visualization on the web. SVG, Canvas, and HTML manipulation with powerful data binding, transitions, and geographic projections.", url: "https://github.com/d3/d3", type: "github", category: "frontend", source: "Observable", tags: ["Visualization", "SVG", "Charts"] },
  { title: "Cypress — JavaScript E2E Testing", description: "Fast, reliable end-to-end testing framework. Time travel debugging, automatic waiting, real browser testing, and network stubbing for frontend applications.", url: "https://github.com/cypress-io/cypress", type: "github", category: "frontend", source: "Cypress", tags: ["E2E", "Testing", "Debugging"] },
  { title: "tRPC — End-to-End Type-Safe APIs", description: "Build fully type-safe APIs without code generation. End-to-end type inference from server to client with React Query integration and automatic validation.", url: "https://github.com/trpc/trpc", type: "github", category: "frontend", source: "tRPC", tags: ["Type-Safe", "API", "Full Stack"] },
  { title: "How Linear Built Their Ultra-Fast UI", description: "Linear's approach to building a snappy project management tool. Covers optimistic updates, local-first architecture, and keyboard-driven UX.", url: "https://linear.app/blog", type: "case-study", category: "frontend", source: "Linear", tags: ["Local-First", "Optimistic", "Speed"] },

  /* ==================  Backend (extra)  ================== */
  { title: "Nest.js — Progressive Node.js Framework", description: "Enterprise-grade Node.js framework with TypeScript. Modular architecture, dependency injection, decorators, guards, and microservice support.", url: "https://github.com/nestjs/nest", type: "github", category: "backend", source: "NestJS", tags: ["Node.js", "TypeScript", "DI"] },
  { title: "Bun — All-in-One JavaScript Runtime", description: "Fast JavaScript runtime, bundler, transpiler, and package manager. Drop-in Node.js replacement with native TypeScript support and SQLite built in.", url: "https://github.com/oven-sh/bun", type: "github", category: "backend", source: "Oven", tags: ["Runtime", "Fast", "All-in-One"] },
  { title: "Deno — Secure JavaScript Runtime", description: "Modern JavaScript/TypeScript runtime with built-in security, dependency management via URLs, native TypeScript support, and web standard APIs.", url: "https://github.com/denoland/deno", type: "github", category: "backend", source: "Deno Land", tags: ["Deno", "Secure", "TypeScript"] },
  { title: "tRPC — End-to-End Typesafe Backend", description: "Build typesafe APIs with TypeScript. Full static type safety from backend to frontend, auto-generated documentation, and first-class React/Next.js support.", url: "https://trpc.io/", type: "course", category: "backend", source: "tRPC", tags: ["TypeScript", "Type-Safe", "Full-Stack"] },
  { title: "Elixir — Scalable Concurrent Language", description: "Dynamic, functional language for building scalable, maintainable applications. Built on Erlang VM with fault tolerance, distribution, and hot code upgrades.", url: "https://github.com/elixir-lang/elixir", type: "github", category: "backend", source: "Elixir", tags: ["Elixir", "Erlang", "Concurrent"] },
  { title: "Phoenix Framework — Elixir Web", description: "Productive web framework for Elixir. Real-time features with channels, LiveView for server-rendered interactivity, and millions of concurrent connections.", url: "https://github.com/phoenixframework/phoenix", type: "github", category: "backend", source: "Phoenix", tags: ["Phoenix", "LiveView", "Real-Time"] },
  { title: "RabbitMQ — Message Broker", description: "Most widely deployed open-source message broker. AMQP protocol, multiple messaging patterns, clustering, federation, and management UI.", url: "https://github.com/rabbitmq/rabbitmq-server", type: "github", category: "backend", source: "VMware", tags: ["Messaging", "AMQP", "Queue"] },
  { title: "NATS — Cloud Native Messaging", description: "Simple, secure, high-performance messaging system. Subject-based addressing, request-reply, pub-sub, and JetStream for persistent messaging.", url: "https://github.com/nats-io/nats-server", type: "github", category: "backend", source: "Synadia", tags: ["NATS", "Messaging", "Cloud Native"] },
  { title: "How WhatsApp Handles 100B Messages/Day", description: "WhatsApp's Erlang/Elixir based infrastructure serving billions of messages daily. Covers custom XMPP protocol, message queuing, and 2M connections per server.", url: "https://engineering.fb.com/", type: "case-study", category: "backend", source: "Meta Engineering", tags: ["Messaging", "Erlang", "Scale"] },
  { title: "How Figma Scaled Their Multiplayer API", description: "Figma's WebSocket-based real-time API handling millions of concurrent editing sessions. Covers CRDT implementation, conflict resolution, and server architecture.", url: "https://www.figma.com/blog/", type: "case-study", category: "backend", source: "Figma", tags: ["WebSocket", "CRDT", "Real-Time"] },
  { title: "GraphQL — Query Language for APIs", description: "Meta's query language for APIs. Request exactly the data you need, strong typing, introspection, real-time subscriptions, and efficient data loading.", url: "https://github.com/graphql/graphql-spec", type: "github", category: "backend", source: "GraphQL Foundation", tags: ["GraphQL", "API", "Query"] },
  { title: "How Stripe Built Idempotent APIs", description: "Stripe's approach to idempotency in payment APIs. Covers idempotency keys, request deduplication, retry handling, and ensuring exactly-once semantics.", url: "https://stripe.com/blog/idempotency", type: "case-study", category: "backend", source: "Stripe", tags: ["Idempotency", "API", "Payments"] },
  { title: "How Shopify Built Their Webhook System", description: "Shopify's event-driven webhook infrastructure. Covers at-least-once delivery, retry strategies, dead letter queues, and webhook verification.", url: "https://shopify.engineering/", type: "case-study", category: "backend", source: "Shopify", tags: ["Webhooks", "Events", "Delivery"] },
  { title: "Prisma — Next-Gen ORM for Node.js", description: "Type-safe database client for TypeScript and Node.js. Auto-generated query builder, migrations, schema-first design, and support for PostgreSQL, MySQL, SQLite.", url: "https://github.com/prisma/prisma", type: "github", category: "backend", source: "Prisma", tags: ["ORM", "TypeScript", "Migrations"] },
  { title: "Drizzle ORM — TypeScript ORM", description: "Lightweight TypeScript ORM with zero dependencies. SQL-like syntax, type-safe queries, automatic migrations, and support for PostgreSQL, MySQL, SQLite.", url: "https://github.com/drizzle-team/drizzle-orm", type: "github", category: "backend", source: "Drizzle", tags: ["ORM", "SQL-Like", "Lightweight"] },
  { title: "How Discord Handles Trillions of Messages", description: "Discord's backend architecture for message storage and delivery. Covers Cassandra to ScyllaDB migration, read states service, and real-time message fanout.", url: "https://discord.com/blog/how-discord-stores-trillions-of-messages", type: "case-study", category: "backend", source: "Discord", tags: ["Storage", "ScyllaDB", "Fanout"] },
  { title: "How Notion Built Their Real-Time Engine", description: "Notion's collaborative editing backend. Block-based data model, operation log, transactional semantics, and conflict resolution for multi-user editing.", url: "https://www.notion.so/blog/", type: "case-study", category: "backend", source: "Notion", tags: ["Collaboration", "Operations", "Sync"] },
  { title: "How Uber Built Their Service Mesh", description: "Uber's service mesh architecture handling millions of RPS. Covers sidecar proxies, service discovery, load balancing, circuit breaking, and observability.", url: "https://www.uber.com/blog/microservice-architecture/", type: "case-study", category: "backend", source: "Uber", tags: ["Service Mesh", "Proxy", "Microservices"] },
  { title: "Temporal — Durable Execution Platform", description: "Open-source durable execution system for building reliable distributed systems. Workflow orchestration, activity retry, and state management at scale.", url: "https://github.com/temporalio/temporal", type: "github", category: "backend", source: "Temporal", tags: ["Workflow", "Durable", "Orchestration"] },
  { title: "How GitHub Scales Code Search", description: "GitHub's custom search infrastructure indexing 100M+ repositories. Covers trigram indexing, Zoekt search engine, and incremental index updates.", url: "https://github.blog/engineering/", type: "case-study", category: "backend", source: "GitHub", tags: ["Search", "Indexing", "Scale"] },

  /* ==================  DevOps (extra)  ================== */
  { title: "ArgoCD — GitOps Continuous Delivery", description: "Declarative GitOps CD tool for Kubernetes. Automated sync, multi-cluster deployment, SSO integration, and audit trails for production deployments.", url: "https://github.com/argoproj/argo-cd", type: "github", category: "devops", source: "Argo", tags: ["GitOps", "Kubernetes", "CD"] },
  { title: "Flux — GitOps for Kubernetes", description: "CNCF GitOps toolkit for Kubernetes. Source controllers, Kustomize/Helm support, progressive delivery, and multi-tenant cluster management.", url: "https://github.com/fluxcd/flux2", type: "github", category: "devops", source: "CNCF", tags: ["GitOps", "Flux", "Kubernetes"] },
  { title: "Istio — Service Mesh for Kubernetes", description: "Connect, secure, control, and observe microservices. Traffic management, mTLS, telemetry, and policy enforcement across your service mesh.", url: "https://github.com/istio/istio", type: "github", category: "devops", source: "Google", tags: ["Service Mesh", "mTLS", "Traffic"] },
  { title: "Cilium — eBPF-Based Networking", description: "eBPF-powered networking, security, and observability for Kubernetes. High-performance L3/L4/L7 load balancing, network policies, and Hubble flow visualization.", url: "https://github.com/cilium/cilium", type: "github", category: "devops", source: "Isovalent", tags: ["eBPF", "Networking", "Security"] },
  { title: "Crossplane — Universal Cloud Control Plane", description: "Build control planes for cloud infrastructure with Kubernetes. Compose cloud resources into custom APIs, GitOps-ready, and multi-cloud support.", url: "https://github.com/crossplane/crossplane", type: "github", category: "devops", source: "Upbound", tags: ["IaC", "Kubernetes", "Multi-Cloud"] },
  { title: "How Spotify Manages 3000+ Microservices", description: "Spotify's developer platform for managing thousands of microservices. Covers Backstage, golden paths, service catalogs, and developer experience.", url: "https://engineering.atspotify.com/", type: "case-study", category: "devops", source: "Spotify", tags: ["Backstage", "Platform", "DX"] },
  { title: "How Airbnb Built Their CI/CD Pipeline", description: "Airbnb's testing and deployment pipeline. Covers test parallelization, flaky test management, canary deployments, and automated rollback.", url: "https://medium.com/airbnb-engineering/", type: "case-study", category: "devops", source: "Airbnb", tags: ["CI/CD", "Testing", "Canary"] },
  { title: "OpenTelemetry — Observability Framework", description: "Vendor-neutral observability framework. Unified APIs for traces, metrics, and logs across any language. Auto-instrumentation and collector pipeline.", url: "https://github.com/open-telemetry/opentelemetry-collector", type: "github", category: "devops", source: "CNCF", tags: ["Observability", "Traces", "Metrics"] },
  { title: "Karpenter — Kubernetes Node Autoscaler", description: "Just-in-time node provisioning for Kubernetes. Fast, flexible autoscaling that provisions the right instance types and sizes based on workload requirements.", url: "https://github.com/aws/karpenter", type: "github", category: "devops", source: "AWS", tags: ["Autoscaling", "Kubernetes", "Nodes"] },
  { title: "How Netflix Does Chaos Engineering", description: "Netflix's pioneering chaos engineering practices. Covers Chaos Monkey, fault injection, blast radius control, and building resilience through controlled failure.", url: "https://netflixtechblog.com/tagged/chaos-engineering", type: "case-study", category: "devops", source: "Netflix", tags: ["Chaos", "Resilience", "Fault Injection"] },
  { title: "Buildpacks — Containerize Without Dockerfiles", description: "Cloud Native Buildpacks transform application source code into container images. Auto-detection, security patching, and reproducible builds without Dockerfiles.", url: "https://github.com/buildpacks/pack", type: "github", category: "devops", source: "CNCF", tags: ["Buildpacks", "Containers", "No Dockerfile"] },
  { title: "How Etsy Deploys to Production 50+ Times/Day", description: "Etsy's continuous deployment culture. Covers feature flags, dark launches, A/B testing, monitoring-driven deployment, and developer ownership of deploys.", url: "https://www.etsy.com/codeascraft", type: "case-study", category: "devops", source: "Etsy", tags: ["Continuous Deploy", "Feature Flags", "Culture"] },
  { title: "Traefik — Cloud-Native Edge Router", description: "Modern reverse proxy and load balancer. Auto-discovery of services, Let's Encrypt integration, middleware, and support for Docker, Kubernetes, and more.", url: "https://github.com/traefik/traefik", type: "github", category: "devops", source: "Traefik Labs", tags: ["Proxy", "Load Balancer", "Auto-Discovery"] },
  { title: "Helm — Kubernetes Package Manager", description: "The package manager for Kubernetes. Charts, templates, release management, and a public chart repository for deploying common applications.", url: "https://github.com/helm/helm", type: "github", category: "devops", source: "CNCF", tags: ["Helm", "Charts", "Package Manager"] },
  { title: "k9s — Kubernetes CLI Dashboard", description: "Terminal-based UI to interact with Kubernetes clusters. Resource viewing, log tailing, port forwarding, and cluster management from the command line.", url: "https://github.com/derailed/k9s", type: "github", category: "devops", source: "Community", tags: ["CLI", "Dashboard", "Kubernetes"] },

  /* ==================  Databases (extra)  ================== */
  { title: "CockroachDB — Distributed SQL", description: "Cloud-native distributed SQL database. Serializable transactions, horizontal scaling, multi-region support, and PostgreSQL wire compatibility.", url: "https://github.com/cockroachdb/cockroach", type: "github", category: "databases", source: "Cockroach Labs", tags: ["Distributed SQL", "NewSQL", "PostgreSQL"] },
  { title: "TiDB — HTAP Database", description: "Open-source MySQL-compatible distributed database. HTAP (Hybrid Transactional/Analytical Processing), horizontal scaling, and TiKV distributed storage.", url: "https://github.com/pingcap/tidb", type: "github", category: "databases", source: "PingCAP", tags: ["HTAP", "MySQL", "Distributed"] },
  { title: "Vitess — Database Clustering for MySQL", description: "CNCF project for deploying, scaling, and managing large clusters of MySQL instances. Horizontal sharding, connection pooling, and schema management.", url: "https://github.com/vitessio/vitess", type: "github", category: "databases", source: "PlanetScale", tags: ["MySQL", "Sharding", "Clustering"] },
  { title: "ScyllaDB — High-Performance NoSQL", description: "C++ reimplementation of Apache Cassandra. 10x throughput, consistent low latency, and CQL compatibility with automatic memory and CPU management.", url: "https://github.com/scylladb/scylladb", type: "github", category: "databases", source: "ScyllaDB", tags: ["NoSQL", "Performance", "Cassandra"] },
  { title: "How Notion Migrated from MongoDB to PostgreSQL", description: "Notion's database migration journey. Covers data modeling changes, zero-downtime migration strategy, and PostgreSQL performance improvements.", url: "https://www.notion.so/blog/", type: "case-study", category: "databases", source: "Notion", tags: ["Migration", "PostgreSQL", "MongoDB"] },
  { title: "QuestDB — Time Series Database", description: "High-performance time series database with SQL. Columnar storage, SIMD-accelerated queries, and 480M+ row/second ingestion on a single machine.", url: "https://github.com/questdb/questdb", type: "github", category: "databases", source: "QuestDB", tags: ["Time Series", "SQL", "Performance"] },
  { title: "Dragonfly — In-Memory Data Store", description: "Modern Redis/Memcached alternative. Multi-threaded, 25x faster, and compatible with existing Redis clients. Efficient memory management with dashtable.", url: "https://github.com/dragonflydb/dragonfly", type: "github", category: "databases", source: "Dragonfly", tags: ["In-Memory", "Redis", "Performance"] },
  { title: "How Shopify Manages Database Query Performance", description: "Shopify's approach to SQL performance at scale. Slow query detection, index optimization, query rewriting, and monitoring query latencies.", url: "https://shopify.engineering/", type: "case-study", category: "databases", source: "Shopify", tags: ["Query Perf", "Indexing", "Monitoring"] },
  { title: "Neon — Serverless PostgreSQL", description: "Separates storage and compute for PostgreSQL. Instant branching, autoscaling to zero, point-in-time restore, and bottomless storage with copy-on-write.", url: "https://github.com/neondatabase/neon", type: "github", category: "databases", source: "Neon", tags: ["Serverless", "PostgreSQL", "Branching"] },
  { title: "How DoorDash Scaled Their Database Layer", description: "DoorDash's database scaling strategies. Covers read replicas, caching layers, connection pooling, and migrating from a monolithic to sharded architecture.", url: "https://doordash.engineering/", type: "case-study", category: "databases", source: "DoorDash", tags: ["Scaling", "Sharding", "Caching"] },

  /* ==================  System Design (extra)  ================== */
  { title: "MIT 6.172 — Performance Engineering", description: "MIT's performance engineering course. Covers cache optimization, parallel algorithms, race conditions, measurement methodology, and software performance tuning.", url: "https://ocw.mit.edu/courses/6-172-performance-engineering-of-software-systems-fall-2018/", type: "course", category: "system-design", source: "MIT", tags: ["Performance", "Optimization", "Parallel"] },
  { title: "How Uber Built H3 Geospatial Indexing", description: "Uber's hexagonal hierarchical geospatial indexing system. Covers spatial partitioning, geographic analysis, and efficient location-based operations.", url: "https://www.uber.com/blog/h3/", type: "case-study", category: "system-design", source: "Uber", tags: ["Geospatial", "Indexing", "H3"] },
  { title: "How Slack Built Real-Time Search", description: "Slack's search infrastructure serving millions of queries. Covers inverted indexes, real-time indexing, ranking, and scaling search across billions of messages.", url: "https://slack.engineering/", type: "case-study", category: "system-design", source: "Slack", tags: ["Search", "Real-Time", "Indexing"] },
  { title: "How YouTube Serves 1B Hours of Video Daily", description: "YouTube's video serving infrastructure. Covers CDN architecture, adaptive bitrate streaming, transcoding pipeline, and global traffic management.", url: "https://blog.youtube/inside-youtube/", type: "case-study", category: "system-design", source: "YouTube", tags: ["Video", "CDN", "Streaming"] },
  { title: "How Airbnb Built Their Search Platform", description: "Airbnb's search ranking system. Covers listing quality scoring, personalization, geographic search, dynamic pricing integration, and ML-based ranking.", url: "https://medium.com/airbnb-engineering/", type: "case-study", category: "system-design", source: "Airbnb", tags: ["Search", "Ranking", "Personalization"] },
  { title: "How Notion Built Their Block Data Model", description: "Notion's innovative block-based data model. How they represent any type of content as blocks with properties, relations, and formulas in a flexible schema.", url: "https://www.notion.so/blog/", type: "case-study", category: "system-design", source: "Notion", tags: ["Data Model", "Blocks", "Flexible Schema"] },
  { title: "How WhatsApp Achieves 99.99% Uptime", description: "WhatsApp's reliability architecture. Covers Erlang-based backend, multi-datacenter replication, graceful degradation, and handling billions of messages.", url: "https://engineering.fb.com/", type: "case-study", category: "system-design", source: "Meta", tags: ["Reliability", "Uptime", "Erlang"] },
  { title: "Rate Limiting Algorithms Explained", description: "Comprehensive guide to rate limiting. Token bucket, sliding window, leaky bucket, fixed window, and distributed rate limiting with Redis.", url: "https://blog.bytebytego.com/", type: "ebook", category: "system-design", source: "ByteByteGo", tags: ["Rate Limiting", "Algorithms", "Redis"] },
  { title: "How Pinterest Handles 1B+ Pins", description: "Pinterest's content management system. Covers pin storage, image processing pipeline, content recommendation, and search infrastructure.", url: "https://medium.com/pinterest-engineering/", type: "case-study", category: "system-design", source: "Pinterest", tags: ["Content", "Images", "Recommendations"] },
  { title: "How Shopify Handles Flash Sales", description: "Shopify's approach to handling massive traffic spikes during flash sales. Covers load shedding, queue-based checkout, caching, and auto-scaling.", url: "https://shopify.engineering/", type: "case-study", category: "system-design", source: "Shopify", tags: ["Flash Sales", "Load Shedding", "Queue"] },
  { title: "How Reddit Scaled to 1.7B Monthly Users", description: "Reddit's infrastructure evolution. Covers comment tree rendering, hot/new ranking, media processing, and scaling through rapid growth.", url: "https://www.redditinc.com/blog", type: "case-study", category: "system-design", source: "Reddit", tags: ["Ranking", "Comments", "Growth"] },
  { title: "How Canva Handles Image Rendering at Scale", description: "Canva's image rendering pipeline. Covers server-side rendering, PDF generation, multi-format export, and distributed rendering clusters.", url: "https://www.canva.dev/blog/engineering/", type: "case-study", category: "system-design", source: "Canva", tags: ["Rendering", "Images", "PDF"] },

  /* ==================  Security (extra)  ================== */
  { title: "Falco — Runtime Security for Kubernetes", description: "Cloud-native runtime security tool. eBPF-powered threat detection, Kubernetes audit logs, and custom rules for detecting anomalous behavior.", url: "https://github.com/falcosecurity/falco", type: "github", category: "security", source: "CNCF", tags: ["Runtime", "Kubernetes", "eBPF"] },
  { title: "Vault — Secrets Management", description: "HashiCorp's secrets management tool. Dynamic secrets, encryption as a service, identity-based access, and audit logging for sensitive data.", url: "https://github.com/hashicorp/vault", type: "github", category: "security", source: "HashiCorp", tags: ["Secrets", "Encryption", "IAM"] },
  { title: "Snyk — Developer Security Platform", description: "Find and fix vulnerabilities in code, dependencies, containers, and IaC. Integrates into CI/CD pipelines with auto-fix PRs.", url: "https://snyk.io/", type: "course", category: "security", source: "Snyk", tags: ["Vulnerabilities", "Dependencies", "CI/CD"] },
  { title: "How 1Password Implements Zero-Knowledge", description: "1Password's zero-knowledge security architecture. Covers SRP protocol, secret key derivation, vault encryption, and why they can't access your data.", url: "https://blog.1password.com/", type: "case-study", category: "security", source: "1Password", tags: ["Zero-Knowledge", "Encryption", "SRP"] },
  { title: "How Cloudflare Generates Random Numbers", description: "Cloudflare's lava lamp wall for entropy generation. Covers the importance of randomness in cryptography and their creative hardware RNG solution.", url: "https://blog.cloudflare.com/randomness-101-lavarand-in-production/", type: "case-study", category: "security", source: "Cloudflare", tags: ["Randomness", "Entropy", "Cryptography"] },
  { title: "CrowdStrike — Endpoint Security Research", description: "Research on advanced persistent threats, malware analysis, nation-state actors, and incident response. Regular threat intelligence reports.", url: "https://www.crowdstrike.com/blog/", type: "case-study", category: "security", source: "CrowdStrike", tags: ["Threat Intel", "APT", "Incident"] },
  { title: "How Signal Implements End-to-End Encryption", description: "Signal's encryption protocol. Covers the Double Ratchet algorithm, X3DH key agreement, sealed sender, and why E2E encryption matters.", url: "https://signal.org/docs/", type: "ebook", category: "security", source: "Signal", tags: ["E2E Encryption", "Protocol", "Privacy"] },
  { title: "OAuth 2.0 Simplified — Book", description: "Practical guide to OAuth 2.0 and OpenID Connect. Covers authorization code flow, PKCE, token management, and building secure authentication.", url: "https://www.oauth.com/", type: "ebook", category: "security", source: "Aaron Parecki", tags: ["OAuth", "OIDC", "Auth"] },

  /* ==================  Data Science (extra)  ================== */
  { title: "Polars — Fast DataFrame Library", description: "Blazingly fast DataFrame library in Rust with Python bindings. Lazy execution, query optimization, and multi-threaded operations. 10-100x faster than Pandas.", url: "https://github.com/pola-rs/polars", type: "github", category: "data-science", source: "Polars", tags: ["DataFrames", "Rust", "Performance"] },
  { title: "DuckDB — Analytical SQL Engine", description: "In-process analytical database. Run analytical SQL queries directly on Parquet, CSV, and Pandas DataFrames with zero configuration.", url: "https://github.com/duckdb/duckdb", type: "github", category: "data-science", source: "DuckDB", tags: ["SQL", "Analytics", "Embedded"] },
  { title: "dbt — Data Build Tool", description: "Transform data in your warehouse using SQL and software engineering best practices. Version control, testing, documentation, and modular data pipelines.", url: "https://github.com/dbt-labs/dbt-core", type: "github", category: "data-science", source: "dbt Labs", tags: ["ELT", "SQL", "Data Warehouse"] },
  { title: "Great Expectations — Data Quality", description: "Tool for validating, documenting, and profiling data. Expectations as tests, automated data docs, and integration with Airflow, Spark, and SQL.", url: "https://github.com/great-expectations/great_expectations", type: "github", category: "data-science", source: "GX", tags: ["Quality", "Testing", "Validation"] },
  { title: "How Spotify Manages Data at Scale", description: "Spotify's data infrastructure. Covers data mesh architecture, event sourcing, data lakes, and democratizing access for 1000+ data scientists.", url: "https://engineering.atspotify.com/", type: "case-study", category: "data-science", source: "Spotify", tags: ["Data Mesh", "Lake", "Events"] },
  { title: "How Twitter Built Their ML Feature Store", description: "Twitter's real-time feature store for ML models. Covers feature computation, serving, monitoring, and time-travel queries for training data.", url: "https://blog.x.com/engineering", type: "case-study", category: "data-science", source: "X Engineering", tags: ["Feature Store", "Real-Time", "ML"] },
  { title: "Apache Flink — Stream Processing", description: "Stateful stream processing framework. Exactly-once semantics, event time processing, watermarks, and both batch and stream processing.", url: "https://github.com/apache/flink", type: "github", category: "data-science", source: "Apache", tags: ["Streaming", "Flink", "Stateful"] },
  { title: "Metabase — Business Intelligence", description: "Open-source BI tool for asking questions about your data. SQL and no-code query builder, dashboards, alerts, and embedding for customer-facing analytics.", url: "https://github.com/metabase/metabase", type: "github", category: "data-science", source: "Metabase", tags: ["BI", "Dashboards", "No-Code"] },
  { title: "How Zillow Uses ML for Home Valuations", description: "Zillow's Zestimate machine learning model. Covers feature engineering from property data, ensemble methods, and updating valuations for 100M+ homes.", url: "https://www.zillow.com/tech/", type: "case-study", category: "data-science", source: "Zillow", tags: ["Real Estate", "Ensemble", "Valuation"] },
  { title: "Evidence — BI as Code", description: "Build polished data products with SQL and Markdown. Version-controlled reports, automated scheduling, and deployment to any static hosting.", url: "https://github.com/evidence-dev/evidence", type: "github", category: "data-science", source: "Evidence", tags: ["BI", "SQL", "Markdown"] },

  /* ==================  SQL (extra)  ================== */
  { title: "SQL Performance Explained — eBook", description: "Complete guide to SQL performance tuning. Covers execution plans, index design, join algorithms, subquery optimization, and database-specific tips.", url: "https://sql-performance-explained.com/", type: "ebook", category: "sql", source: "Markus Winand", tags: ["Performance", "Execution Plans", "Tuning"] },
  { title: "LeetCode SQL Problems — Practice", description: "Curated collection of SQL interview problems. Covers joins, window functions, CTEs, recursive queries, and complex analytical queries with test cases.", url: "https://leetcode.com/studyplan/top-sql-50/", type: "course", category: "sql", source: "LeetCode", tags: ["Practice", "Interview", "Problems"] },
  { title: "HackerRank SQL Challenges", description: "SQL practice challenges across difficulty levels. Covers basic select, joins, aggregation, advanced queries, and alternative approaches.", url: "https://www.hackerrank.com/domains/sql", type: "course", category: "sql", source: "HackerRank", tags: ["Challenges", "Practice", "Levels"] },
  { title: "How Meta Optimizes SQL Queries at Scale", description: "Meta's SQL optimization techniques for Presto/Trino. Covers query planning, predicate pushdown, join reordering, and resource management.", url: "https://engineering.fb.com/", type: "case-study", category: "sql", source: "Meta Engineering", tags: ["Presto", "Optimization", "Scale"] },
  { title: "Window Functions Tutorial — PostgreSQL", description: "Interactive tutorial on SQL window functions. ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, running totals, and moving averages with PostgreSQL.", url: "https://www.postgresql.org/docs/current/tutorial-window.html", type: "ebook", category: "sql", source: "PostgreSQL", tags: ["Window Functions", "Tutorial", "PostgreSQL"] },
  { title: "How Datadog Built Their Query Engine", description: "Datadog's custom SQL query engine for observability data. Covers columnar storage, vectorized execution, and time-series specific optimizations.", url: "https://www.datadoghq.com/blog/", type: "case-study", category: "sql", source: "Datadog", tags: ["Query Engine", "Columnar", "Time Series"] },

  /* ==================  Mobile (extra)  ================== */
  { title: "SwiftUI Tutorials — Apple Official", description: "Apple's official SwiftUI tutorials. Build iOS, macOS, watchOS apps with declarative syntax, previews, and integration with UIKit.", url: "https://developer.apple.com/tutorials/swiftui", type: "course", category: "mobile", source: "Apple", tags: ["SwiftUI", "iOS", "Declarative"] },
  { title: "Kotlin Multiplatform — Shared Code", description: "Share business logic between Android, iOS, web, and desktop. Keep native UIs while maximizing code reuse across platforms.", url: "https://kotlinlang.org/docs/multiplatform.html", type: "course", category: "mobile", source: "JetBrains", tags: ["KMP", "Cross-Platform", "Shared"] },
  { title: "How Airbnb Rebuilt Their Mobile Architecture", description: "Airbnb's server-driven UI system for mobile. Covers component rendering, dynamic layouts, and reducing app update cycles.", url: "https://medium.com/airbnb-engineering/", type: "case-study", category: "mobile", source: "Airbnb", tags: ["Server-Driven", "Architecture", "Dynamic"] },
  { title: "How Spotify Optimized Mobile Performance", description: "Spotify's mobile performance optimization. Covers startup time reduction, memory management, network efficiency, and battery optimization.", url: "https://engineering.atspotify.com/", type: "case-study", category: "mobile", source: "Spotify", tags: ["Performance", "Startup", "Battery"] },
  { title: "How Twitter Handles Mobile Push Notifications", description: "Twitter's push notification infrastructure. Covers notification prioritization, delivery optimization, and reducing notification fatigue.", url: "https://blog.x.com/engineering", type: "case-study", category: "mobile", source: "X Engineering", tags: ["Push", "Notifications", "Delivery"] },
  { title: "How Cash App Built Their Android Architecture", description: "Square's modern Android architecture for Cash App. Covers unidirectional data flow, presenters, navigation, and testing strategies.", url: "https://developer.squareup.com/blog", type: "case-study", category: "mobile", source: "Square", tags: ["Android", "Architecture", "UDF"] },
  { title: "Capacitor — Cross-Platform Native Runtime", description: "Build web apps that run natively on iOS, Android, and Web. Access native device APIs from JavaScript with a consistent plugin system.", url: "https://github.com/ionic-team/capacitor", type: "github", category: "mobile", source: "Ionic", tags: ["Hybrid", "Web", "Native Bridge"] },

  /* ==================  Cloud (extra)  ================== */
  { title: "Terraform Best Practices — Guide", description: "Community guide to Terraform best practices. Module structure, state management, workspace strategies, and CI/CD integration patterns.", url: "https://www.terraform-best-practices.com/", type: "ebook", category: "cloud", source: "Community", tags: ["Terraform", "Best Practices", "Modules"] },
  { title: "How Stripe Manages Multi-Region Infrastructure", description: "Stripe's multi-region deployment strategy. Covers data sovereignty, active-active routing, and maintaining sub-100ms API latency globally.", url: "https://stripe.com/blog/", type: "case-study", category: "cloud", source: "Stripe", tags: ["Multi-Region", "Latency", "Global"] },
  { title: "How Spotify Migrated to Google Cloud", description: "Spotify's 7-year infrastructure migration from self-hosted data centers to GCP. Covers BigQuery adoption, GKE, and Dataflow.", url: "https://engineering.atspotify.com/", type: "case-study", category: "cloud", source: "Spotify", tags: ["Migration", "GCP", "BigQuery"] },
  { title: "Fly.io — Deploy Apps Globally", description: "Run full-stack apps and databases close to users worldwide. Firecracker VMs, built-in Anycast networking, and distributed PostgreSQL.", url: "https://fly.io/docs/", type: "course", category: "cloud", source: "Fly.io", tags: ["Edge", "Global", "Firecracker"] },
  { title: "How Vercel Built Their Edge Network", description: "Vercel's global edge network architecture. Covers ISR, edge middleware, serverless functions, and sub-100ms TTFB worldwide.", url: "https://vercel.com/blog", type: "case-study", category: "cloud", source: "Vercel", tags: ["Edge", "Serverless", "TTFB"] },
  { title: "How Twilio Built a Multi-Cloud Platform", description: "Twilio's multi-cloud strategy spanning AWS, Azure, and GCP. Covers cloud-agnostic abstractions, workload placement, and cost optimization.", url: "https://www.twilio.com/blog/", type: "case-study", category: "cloud", source: "Twilio", tags: ["Multi-Cloud", "Abstraction", "Cost"] },

  /* ==================  Dart / Flutter (extra)  ================== */
  { title: "Flutter Gems — Curated Package Guide", description: "Curated list of top Dart and Flutter packages. Categorized by use case: state management, networking, storage, animation, UI components, and more.", url: "https://fluttergems.dev/", type: "ebook", category: "dart", source: "Flutter Gems", tags: ["Packages", "Curated", "Ecosystem"] },
  { title: "How Nubank Built Their App with Flutter", description: "Nubank's Flutter adoption for Latin America's largest digital bank. Covers performance, code sharing, localization, and serving 80M+ customers.", url: "https://blog.nubank.com.br/", type: "case-study", category: "dart", source: "Nubank", tags: ["Fintech", "Scale", "Banking"] },
  { title: "Flutter Fire — Firebase for Flutter", description: "Official Firebase plugins for Flutter. Authentication, Firestore, Cloud Storage, Cloud Functions, Analytics, Crashlytics with full Dart type safety.", url: "https://github.com/firebase/flutterfire", type: "github", category: "dart", source: "Firebase", tags: ["Firebase", "Auth", "Firestore"] },
  { title: "Freezed — Code Generation for Dart", description: "Union/sealed classes, immutable data, copy-with, JSON serialization, and pattern matching for Dart via code generation. Essential for clean Dart code.", url: "https://github.com/rrousselGit/freezed", type: "github", category: "dart", source: "Remi Rousselet", tags: ["Code Gen", "Immutable", "Unions"] },
  { title: "How Toyota Built Their App with Flutter", description: "Toyota's Flutter adoption for their connected car platform. Covers Bluetooth integration, real-time vehicle data, and cross-platform deployment.", url: "https://flutter.dev/showcase", type: "case-study", category: "dart", source: "Toyota", tags: ["Automotive", "IoT", "Connected"] },

  /* ==================  Kotlin (extra)  ================== */
  { title: "Compose Multiplatform — Desktop & Web UI", description: "JetBrains' UI framework extending Jetpack Compose to desktop, web, and iOS. Share UI code across all platforms with Kotlin.", url: "https://github.com/JetBrains/compose-multiplatform", type: "github", category: "kotlin", source: "JetBrains", tags: ["Compose", "Desktop", "Multiplatform"] },
  { title: "Exposed — Kotlin SQL Library", description: "Lightweight SQL library for Kotlin. Both DSL and DAO approaches, type-safe queries, transactions, and support for PostgreSQL, MySQL, H2.", url: "https://github.com/JetBrains/Exposed", type: "github", category: "kotlin", source: "JetBrains", tags: ["SQL", "ORM", "Type-Safe"] },
  { title: "How DoorDash Uses Kotlin for Android", description: "DoorDash's Kotlin adoption story. Covers coroutines for network calls, sealed classes for state, and Jetpack Compose migration.", url: "https://doordash.engineering/", type: "case-study", category: "kotlin", source: "DoorDash", tags: ["Android", "Coroutines", "Compose"] },
  { title: "How Lyft Uses Kotlin Multiplatform", description: "Lyft's approach to sharing Kotlin code between Android and iOS. Covers KMM architecture, shared networking layer, and reducing code duplication.", url: "https://eng.lyft.com/", type: "case-study", category: "kotlin", source: "Lyft", tags: ["KMM", "Code Sharing", "iOS"] },
  { title: "Kotest — Kotlin Testing Framework", description: "Flexible and comprehensive testing framework for Kotlin. Multiple testing styles, property-based testing, data-driven testing, and coroutine support.", url: "https://github.com/kotest/kotest", type: "github", category: "kotlin", source: "Kotest", tags: ["Testing", "Property-Based", "BDD"] },

  /* ==================  Rust (extra)  ================== */
  { title: "Bevy — Rust Game Engine", description: "Data-driven game engine built in Rust. ECS architecture, 2D/3D rendering, hot reloading, cross-platform deployment, and a growing plugin ecosystem.", url: "https://github.com/bevyengine/bevy", type: "github", category: "rust", source: "Bevy", tags: ["Game Engine", "ECS", "2D/3D"] },
  { title: "Tauri — Desktop Apps with Rust + Web", description: "Build smaller, faster, and more secure desktop applications with a Rust backend and web frontend. 10x smaller than Electron.", url: "https://github.com/tauri-apps/tauri", type: "github", category: "rust", source: "Tauri", tags: ["Desktop", "WebView", "Lightweight"] },
  { title: "Leptos — Full-Stack Rust Web Framework", description: "Build fast web apps in Rust. Fine-grained reactivity, server-side rendering, hydration, and no virtual DOM — all in pure Rust.", url: "https://github.com/leptos-rs/leptos", type: "github", category: "rust", source: "Leptos", tags: ["Full Stack", "SSR", "Reactive"] },
  { title: "Polars — Blazing Fast DataFrame Library", description: "Lightning-fast DataFrame library written in Rust with Python bindings. Lazy query optimization, parallel execution, and Apache Arrow integration.", url: "https://github.com/pola-rs/polars", type: "github", category: "rust", source: "Polars", tags: ["DataFrames", "Arrow", "Parallel"] },
  { title: "How Vercel Built Turbopack in Rust", description: "Vercel's next-generation bundler written in Rust. 700x faster than Webpack, incremental computation, and designed for the scale of modern web applications.", url: "https://vercel.com/blog/turbopack", type: "case-study", category: "rust", source: "Vercel", tags: ["Bundler", "Turbopack", "Speed"] },
  { title: "How Deno Uses Rust Under the Hood", description: "Deno runtime's Rust core. Covers the V8 bindings (rusty_v8), ops system, security sandboxing, and why Rust was chosen over C++.", url: "https://deno.com/blog/", type: "case-study", category: "rust", source: "Deno", tags: ["Runtime", "V8", "Sandboxing"] },

  /* ==================  More AI/ML  ================== */
  { title: "Microsoft Phi Models — Small Language Models", description: "Microsoft's small but capable language models. Phi-2 and Phi-3 demonstrate that smaller models with better data can match larger models.", url: "https://azure.microsoft.com/en-us/blog/introducing-phi-3-redefining-whats-possible-with-slms/", type: "case-study", category: "ai-ml", source: "Microsoft", tags: ["SLM", "Efficient", "Edge"] },
  { title: "Ollama — Run LLMs Locally", description: "Run large language models locally. Easy setup for Llama, Mistral, Gemma, and other open models with a simple CLI and API.", url: "https://github.com/ollama/ollama", type: "github", category: "ai-ml", source: "Ollama", tags: ["Local LLM", "CLI", "Privacy"] },
  { title: "vLLM — Fast LLM Serving", description: "High-throughput and memory-efficient inference engine for LLMs. PagedAttention, continuous batching, and tensor parallelism for production serving.", url: "https://github.com/vllm-project/vllm", type: "github", category: "ai-ml", source: "vLLM", tags: ["Inference", "Serving", "High-Throughput"] },
  { title: "LlamaIndex — LLM Data Framework", description: "Connect LLMs to external data. Data ingestion, indexing, retrieval-augmented generation, and building production RAG applications.", url: "https://github.com/run-llama/llama_index", type: "github", category: "ai-ml", source: "LlamaIndex", tags: ["RAG", "Data", "Indexing"] },
  { title: "How GitHub Built Copilot", description: "GitHub's AI coding assistant. Covers Codex model training, context gathering, prompt engineering, and real-time code suggestion architecture.", url: "https://github.blog/ai-and-ml/github-copilot/", type: "case-study", category: "ai-ml", source: "GitHub", tags: ["Copilot", "Code Gen", "IDE"] },

  /* ==================  More Backend ================== */
  { title: "Hono — Ultrafast Edge Web Framework", description: "Fast, lightweight web framework for Edge computing. Works on Cloudflare Workers, Deno, Bun, and Node.js with middleware, routing, and validators.", url: "https://github.com/honojs/hono", type: "github", category: "backend", source: "Hono", tags: ["Edge", "Lightweight", "Universal"] },
  { title: "Effect — TypeScript for Complex Applications", description: "TypeScript library for building complex applications. Structured concurrency, typed errors, dependency injection, and composable concurrent programs.", url: "https://github.com/Effect-TS/effect", type: "github", category: "backend", source: "Effect", tags: ["TypeScript", "Concurrency", "Typed Errors"] },
  { title: "How Figma Built LiveGraph", description: "Figma's custom GraphQL-like API for real-time subscriptions. Covers data dependencies, incremental computation, and efficient change propagation.", url: "https://www.figma.com/blog/livegraph-real-time-data-fetching-at-figma/", type: "case-study", category: "backend", source: "Figma", tags: ["Real-Time", "GraphQL", "Subscriptions"] },

  /* ==================  More DevOps ================== */
  { title: "Dagger — CI/CD as Code", description: "Programmable CI/CD engine that runs pipelines as containers. Write pipelines in Go, Python, TypeScript, and cache everything automatically.", url: "https://github.com/dagger/dagger", type: "github", category: "devops", source: "Dagger", tags: ["CI/CD", "Containers", "Programmable"] },
  { title: "Kamal — Deploy Web Apps Anywhere", description: "Deploy web apps with zero-downtime to any server. From the creators of 37signals (Ruby on Rails). Docker-based with built-in proxy.", url: "https://github.com/basecamp/kamal", type: "github", category: "devops", source: "37signals", tags: ["Deployment", "Docker", "Zero-Downtime"] },
  { title: "Caddy — Modern Web Server", description: "Automatic HTTPS web server. Reverse proxy, load balancing, file serving, and dynamic config via API. Written in Go with extensible modules.", url: "https://github.com/caddyserver/caddy", type: "github", category: "devops", source: "Caddy", tags: ["Web Server", "HTTPS", "Reverse Proxy"] },

  /* ==================  More Databases ================== */
  { title: "Turso — Edge SQLite Database", description: "Distributed SQLite for the edge. Built on libSQL (SQLite fork), replicated globally, with embedded replicas and serverless model.", url: "https://github.com/tursodatabase/libsql", type: "github", category: "databases", source: "Turso", tags: ["SQLite", "Edge", "Distributed"] },
  { title: "Milvus — Vector Database", description: "Open-source vector database for AI applications. Billion-scale similarity search, hybrid search, and multi-tenancy for RAG and recommendation systems.", url: "https://github.com/milvus-io/milvus", type: "github", category: "databases", source: "Zilliz", tags: ["Vector DB", "Similarity", "AI"] },
  { title: "Valkey — Redis Fork", description: "Community-driven fork of Redis after the license change. Feature-compatible, high-performance in-memory data store with ongoing community development.", url: "https://github.com/valkey-io/valkey", type: "github", category: "databases", source: "Linux Foundation", tags: ["In-Memory", "Redis Fork", "Community"] },

  /* ==================  More System Design ================== */
  { title: "How Figma Built a CDN", description: "Figma's custom CDN for design file delivery. Covers edge caching, cache invalidation, and optimizing for large binary files.", url: "https://www.figma.com/blog/", type: "case-study", category: "system-design", source: "Figma", tags: ["CDN", "Caching", "Binary Files"] },
  { title: "How Slack Rebuilt Their Desktop Client", description: "Slack's architecture rewrite. Moving from multiple Electron instances to a single shared-core with per-workspace rendering.", url: "https://slack.engineering/rebuilding-slack-on-the-desktop/", type: "case-study", category: "system-design", source: "Slack", tags: ["Desktop", "Electron", "Architecture"] },
  { title: "How Zoom Handles 300M Daily Meeting Participants", description: "Zoom's real-time video infrastructure. Covers SFU architecture, adaptive encoding, network congestion handling, and global media routing.", url: "https://blog.zoom.us/", type: "case-study", category: "system-design", source: "Zoom", tags: ["Video", "SFU", "Real-Time"] },

  /* ==================  More Security ================== */
  { title: "How Let's Encrypt Secures the Web", description: "Let's Encrypt's free SSL/TLS CA. Covers ACME protocol, certificate issuance at scale, and automating HTTPS for 300M+ websites.", url: "https://letsencrypt.org/how-it-works/", type: "case-study", category: "security", source: "ISRG", tags: ["TLS", "ACME", "Free SSL"] },
  { title: "Mozilla SSL Configuration Generator", description: "Generate recommended TLS configurations for Apache, Nginx, HAProxy, and other servers. Based on Mozilla's security guidelines.", url: "https://ssl-config.mozilla.org/", type: "course", category: "security", source: "Mozilla", tags: ["TLS Config", "Nginx", "Apache"] },

  /* ==================  More Cloud ================== */
  { title: "How Cloudflare Built R2 Object Storage", description: "Cloudflare's S3-compatible object storage with zero egress fees. Architecture decisions, consistency model, and integration with Workers.", url: "https://blog.cloudflare.com/introducing-r2-object-storage/", type: "case-study", category: "cloud", source: "Cloudflare", tags: ["Object Storage", "S3", "Zero Egress"] },
  { title: "How Render Simplified Cloud Deployment", description: "Render's approach to simplifying cloud infrastructure. Covers auto-scaling, managed databases, and zero-DevOps deployment from Git.", url: "https://render.com/blog", type: "case-study", category: "cloud", source: "Render", tags: ["PaaS", "Simple", "Git Deploy"] },

  /* ==================  More Data Science ================== */
  { title: "Hugging Face Datasets — ML Data Library", description: "Access and share datasets for ML. 70K+ datasets for NLP, computer vision, and audio with efficient loading, streaming, and processing.", url: "https://github.com/huggingface/datasets", type: "github", category: "data-science", source: "Hugging Face", tags: ["Datasets", "NLP", "Loading"] },
  { title: "How Instacart Uses ML for Grocery Delivery", description: "Instacart's ML systems for demand forecasting, item availability prediction, optimal batching, and delivery time estimation.", url: "https://tech.instacart.com/", type: "case-study", category: "data-science", source: "Instacart", tags: ["Delivery", "Forecasting", "Logistics"] },

  /* ==================  More Frontend ================== */
  { title: "Million.js — Make React 70% Faster", description: "Drop-in virtual DOM replacement for React. Block-based virtual DOM that compiles JSX at build time for significantly faster rendering.", url: "https://github.com/aidenybai/million", type: "github", category: "frontend", source: "Million", tags: ["VDOM", "Performance", "React"] },
  { title: "Partytown — Offload Scripts to Web Workers", description: "Relocate resource-intensive third-party scripts to web workers. Improves main thread performance while keeping existing script tags.", url: "https://github.com/BuilderIO/partytown", type: "github", category: "frontend", source: "Builder.io", tags: ["Workers", "Performance", "Third-Party"] },

  /* ==================  Expanded — AI / ML  ================== */
  { title: "AutoGPT — Autonomous AI Agent", description: "Autonomous AI agent that chains LLM calls to achieve complex goals. Task planning, web browsing, code execution, and memory management.", url: "https://github.com/Significant-Gravitas/AutoGPT", type: "github", category: "ai-ml", source: "Significant Gravitas", tags: ["Agent", "Autonomous", "Planning"] },
  { title: "LiteLLM — Unified LLM API", description: "Call 100+ LLMs with a unified OpenAI-format API. Load balancing, fallbacks, spend tracking, and budget management.", url: "https://github.com/BerriAI/litellm", type: "github", category: "ai-ml", source: "BerriAI", tags: ["Unified API", "LLM", "Gateway"] },
  { title: "OpenLLMetry — LLM Observability", description: "OpenTelemetry-based observability for LLM applications. Track token usage, latency, and errors across LLM providers.", url: "https://github.com/traceloop/openllmetry", type: "github", category: "ai-ml", source: "Traceloop", tags: ["Observability", "LLM", "OpenTelemetry"] },
  { title: "Semantic Kernel — Microsoft AI SDK", description: "Microsoft's SDK for integrating AI into applications. Plugins, planners, memory, and connectors for building AI agents.", url: "https://github.com/microsoft/semantic-kernel", type: "github", category: "ai-ml", source: "Microsoft", tags: ["SDK", "Agents", "Plugins"] },
  { title: "Open Interpreter — Code Execution AI", description: "Natural language interface for your computer. Execute Python, JavaScript, Shell commands via conversation with safety controls.", url: "https://github.com/OpenInterpreter/open-interpreter", type: "github", category: "ai-ml", source: "Open Interpreter", tags: ["Code Exec", "Chat", "Tool Use"] },
  { title: "Phidata — AI Assistants Framework", description: "Build AI assistants with memory, knowledge, tools, and reasoning. Production-ready with monitoring and evaluation.", url: "https://github.com/phidatahq/phidata", type: "github", category: "ai-ml", source: "Phidata", tags: ["Assistants", "Memory", "Tools"] },
  { title: "DSPy — Programming Not Prompting", description: "Framework for algorithmically optimizing LM prompts and weights. Replace hand-written prompts with compiled, optimized programs.", url: "https://github.com/stanfordnlp/dspy", type: "github", category: "ai-ml", source: "Stanford NLP", tags: ["Optimization", "Prompts", "Compiled"] },
  { title: "Outlines — Structured LLM Generation", description: "Structured text generation with LLMs. JSON mode, regex-guided generation, and grammar-constrained outputs.", url: "https://github.com/outlines-dev/outlines", type: "github", category: "ai-ml", source: "Outlines", tags: ["Structured", "JSON", "Grammar"] },
  { title: "LoRA — Low-Rank Adaptation for LLMs", description: "Efficient fine-tuning technique for large language models. Freeze model weights and train low-rank adapters with 10-100x less memory.", url: "https://github.com/microsoft/LoRA", type: "github", category: "ai-ml", source: "Microsoft", tags: ["Fine-Tuning", "Efficient", "LoRA"] },
  { title: "Unsloth — Fast LLM Fine-Tuning", description: "2x faster, 60% less memory LLM fine-tuning. QLoRA and LoRA support for Llama, Mistral, and other popular models.", url: "https://github.com/unslothai/unsloth", type: "github", category: "ai-ml", source: "Unsloth", tags: ["Fine-Tuning", "Fast", "Memory"] },
  { title: "GGML — Tensor Library for ML", description: "Tensor library for ML, enabling running LLMs on CPU. Quantization, memory-mapped models, and inference optimization.", url: "https://github.com/ggerganov/ggml", type: "github", category: "ai-ml", source: "Georgi Gerganov", tags: ["Tensor", "CPU", "Quantization"] },
  { title: "llama.cpp — LLM Inference in C++", description: "Port of Facebook's LLaMA model in pure C/C++. Run LLMs on consumer hardware with 4-bit quantization.", url: "https://github.com/ggerganov/llama.cpp", type: "github", category: "ai-ml", source: "Georgi Gerganov", tags: ["llama", "C++", "Quantization"] },
  { title: "ComfyUI — Modular Stable Diffusion", description: "Modular, node-based, stable diffusion GUI. Custom workflows, ControlNet, IP-Adapter, and AnimateDiff support.", url: "https://github.com/comfyanonymous/ComfyUI", type: "github", category: "ai-ml", source: "ComfyAnonymous", tags: ["SD", "Nodes", "Workflow"] },
  { title: "Text Generation WebUI — Gradio LLM", description: "Gradio web UI for running LLMs locally. Text generation, chat mode, multi-modal, and extension system.", url: "https://github.com/oobabooga/text-generation-webui", type: "github", category: "ai-ml", source: "oobabooga", tags: ["WebUI", "Local", "Multi-Modal"] },
  { title: "Jan — Offline AI Assistant", description: "Open-source ChatGPT alternative that runs offline. Local model management, privacy-first, and extension ecosystem.", url: "https://github.com/janhq/jan", type: "github", category: "ai-ml", source: "Jan", tags: ["Offline", "Privacy", "Desktop"] },
  { title: "How Walmart Uses AI for Inventory", description: "Walmart's AI-powered inventory management. Demand forecasting, automated replenishment, and shelf stock optimization across 10K+ stores.", url: "https://tech.walmart.com/", type: "case-study", category: "ai-ml", source: "Walmart", tags: ["Inventory", "Forecasting", "Retail"] },
  { title: "How Netflix Trains Recommendation Models", description: "Netflix's recommendation system architecture. Two-stage ranking, contextual bandits, and personalizing for 250M+ subscribers.", url: "https://netflixtechblog.com/", type: "case-study", category: "ai-ml", source: "Netflix", tags: ["Recommendations", "Personalization", "Bandits"] },
  { title: "How X Uses ML for Timeline Ranking", description: "X's ML-powered timeline. Multi-objective optimization, engagement prediction, and balancing relevance with recency.", url: "https://blog.x.com/engineering", type: "case-study", category: "ai-ml", source: "X Engineering", tags: ["Timeline", "Ranking", "Multi-Objective"] },
  { title: "Stanford CS 229 — Machine Learning", description: "Stanford's foundational ML course by Andrew Ng. Supervised learning, unsupervised learning, learning theory, and reinforcement learning.", url: "https://cs229.stanford.edu/", type: "course", category: "ai-ml", source: "Stanford", tags: ["Foundational", "Andrew Ng", "Theory"] },
  { title: "Fast.ai — Practical Deep Learning", description: "Making deep learning accessible. Top-down teaching approach, practical projects, and state-of-the-art results with minimal code.", url: "https://course.fast.ai/", type: "course", category: "ai-ml", source: "fast.ai", tags: ["Practical", "Top-Down", "Accessible"] },

  /* ==================  Expanded — Frontend  ================== */
  { title: "React — UI Component Library", description: "The library for web and native user interfaces. Components, hooks, server components, and the most popular frontend ecosystem.", url: "https://github.com/facebook/react", type: "github", category: "frontend", source: "Meta", tags: ["React", "Components", "UI"] },
  { title: "Vue.js — Progressive JS Framework", description: "The progressive JavaScript framework. Composition API, reactivity system, single-file components, and excellent documentation.", url: "https://github.com/vuejs/core", type: "github", category: "frontend", source: "Evan You", tags: ["Vue", "Reactive", "Progressive"] },
  { title: "Angular — Platform for Web Apps", description: "Platform for building mobile and desktop web applications. TypeScript-first, dependency injection, and comprehensive CLI.", url: "https://github.com/angular/angular", type: "github", category: "frontend", source: "Google", tags: ["Angular", "TypeScript", "Platform"] },
  { title: "Deno Fresh — Web Framework for Deno", description: "Next-gen web framework for Deno. Islands architecture, zero JavaScript overhead, and server-rendered with Preact.", url: "https://github.com/denoland/fresh", type: "github", category: "frontend", source: "Deno", tags: ["Deno", "Islands", "Preact"] },
  { title: "Web Components — MDN Guide", description: "Build reuseable custom elements using web standards. Shadow DOM, custom elements, HTML templates, and slots.", url: "https://developer.mozilla.org/en-US/docs/Web/API/Web_components", type: "ebook", category: "frontend", source: "MDN", tags: ["Web Components", "Standards", "Custom Elements"] },
  { title: "State of JavaScript — Annual Survey", description: "Annual survey of the JavaScript ecosystem. Framework usage, satisfaction, and emerging trends from 30K+ developers.", url: "https://stateofjs.com/", type: "ebook", category: "frontend", source: "State of JS", tags: ["Survey", "Trends", "Ecosystem"] },
  { title: "Frontend Masters — Complete Intro to React v8", description: "Complete introduction to React by Brian Holt. Hooks, effects, context, portals, and building a complete application.", url: "https://frontendmasters.com/courses/complete-react-v8/", type: "course", category: "frontend", source: "Frontend Masters", tags: ["React", "Complete", "Brian Holt"] },
  { title: "How New York Times Built Their Design System", description: "NYT's design system for serving 100M+ monthly readers. Typography, responsive design, and accessible news reading experience.", url: "https://open.nytimes.com/", type: "case-study", category: "frontend", source: "NYT", tags: ["Design System", "Typography", "News"] },
  { title: "How Figma Uses WebAssembly for Performance", description: "Figma's use of WASM for their design tool. C++ to WASM compilation, memory management, and achieving near-native performance.", url: "https://www.figma.com/blog/", type: "case-study", category: "frontend", source: "Figma", tags: ["WASM", "C++", "Performance"] },

  /* ==================  Expanded — Backend  ================== */
  { title: "Apache Kafka — Event Streaming Platform", description: "Distributed event streaming platform. Publish-subscribe, fault-tolerant storage, and real-time stream processing.", url: "https://github.com/apache/kafka", type: "github", category: "backend", source: "Apache", tags: ["Kafka", "Streaming", "Events"] },
  { title: "Redis — In-Memory Data Structure Store", description: "The world's most popular in-memory data store. Strings, hashes, lists, sets, sorted sets, streams, and pub/sub.", url: "https://github.com/redis/redis", type: "github", category: "backend", source: "Redis", tags: ["In-Memory", "Data Structures", "Cache"] },
  { title: "Nginx — High-Performance Web Server", description: "High-performance HTTP server and reverse proxy. Load balancing, SSL termination, caching, and handling 10M+ concurrent connections.", url: "https://github.com/nginx/nginx", type: "github", category: "backend", source: "F5", tags: ["Web Server", "Reverse Proxy", "Load Balancer"] },
  { title: "Envoy — Cloud-Native Edge Proxy", description: "High-performance edge/service proxy. L7 load balancing, gRPC support, circuit breaking, and observability for microservices.", url: "https://github.com/envoyproxy/envoy", type: "github", category: "backend", source: "CNCF", tags: ["Proxy", "L7", "Service Mesh"] },
  { title: "How Pinterest Built Their API Rate Limiter", description: "Pinterest's rate limiting system. Token bucket algorithm, distributed coordination, and handling traffic spikes gracefully.", url: "https://medium.com/pinterest-engineering/", type: "case-study", category: "backend", source: "Pinterest", tags: ["Rate Limiting", "Token Bucket", "API"] },
  { title: "How DoorDash Built Their Real-Time Order Tracking", description: "DoorDash's order tracking system. WebSocket connections, location streaming, and ETA updates for millions of concurrent orders.", url: "https://doordash.engineering/", type: "case-study", category: "backend", source: "DoorDash", tags: ["Real-Time", "Tracking", "WebSocket"] },
  { title: "How Cloudflare Handles 55M+ HTTP Requests/Second", description: "Cloudflare's edge infrastructure. Anycast routing, connection coalescing, and distributed caching across 300+ cities.", url: "https://blog.cloudflare.com/", type: "case-study", category: "backend", source: "Cloudflare", tags: ["Edge", "Anycast", "Scale"] },

  /* ==================  Expanded — DevOps  ================== */
  { title: "Docker — Container Platform", description: "The standard container platform. Build, share, and run applications in isolated environments with Docker Engine and Docker Compose.", url: "https://github.com/moby/moby", type: "github", category: "devops", source: "Docker", tags: ["Containers", "Docker", "Compose"] },
  { title: "Kubernetes — Container Orchestration", description: "The de facto standard for container orchestration. Pods, services, deployments, and managing applications at scale.", url: "https://github.com/kubernetes/kubernetes", type: "github", category: "devops", source: "CNCF", tags: ["Kubernetes", "Orchestration", "Pods"] },
  { title: "GitHub Actions — CI/CD Workflows", description: "Automate software workflows with GitHub Actions. Build, test, and deploy from GitHub with YAML-based workflow definitions.", url: "https://github.com/features/actions", type: "course", category: "devops", source: "GitHub", tags: ["CI/CD", "Workflows", "Automation"] },
  { title: "Jaeger — Distributed Tracing", description: "Open-source distributed tracing system. Trace analysis, service dependency analysis, and latency optimization.", url: "https://github.com/jaegertracing/jaeger", type: "github", category: "devops", source: "CNCF", tags: ["Tracing", "Distributed", "Latency"] },
  { title: "How Meta Handles Code Deployment at Scale", description: "Meta's deployment system serving billions of users. Thousands of commits per day, progressive rollouts, and automated rollbacks.", url: "https://engineering.fb.com/", type: "case-study", category: "devops", source: "Meta", tags: ["Deployment", "Scale", "Progressive"] },
  { title: "How Google Runs SRE at Scale", description: "Google's site reliability engineering practices. Error budgets, SLOs, toil reduction, and managing reliability for global services.", url: "https://sre.google/", type: "ebook", category: "devops", source: "Google", tags: ["SRE", "Error Budgets", "SLOs"] },

  /* ==================  Expanded — Databases  ================== */
  { title: "MySQL — Relational Database", description: "The world's most popular open-source relational database. InnoDB engine, replication, partitioning, and JSON support.", url: "https://github.com/mysql/mysql-server", type: "github", category: "databases", source: "Oracle", tags: ["MySQL", "Relational", "InnoDB"] },
  { title: "PostgreSQL — Advanced Open Source DB", description: "The most advanced open-source relational database. JSONB, extensions, full-text search, PostGIS, and CTEs.", url: "https://github.com/postgres/postgres", type: "github", category: "databases", source: "PostgreSQL", tags: ["PostgreSQL", "Object-Relational", "Extensions"] },
  { title: "MongoDB — Document Database", description: "The most popular NoSQL document database. Flexible schema, aggregation pipeline, atlas search, and change streams.", url: "https://github.com/mongodb/mongo", type: "github", category: "databases", source: "MongoDB", tags: ["NoSQL", "Document", "Aggregation"] },
  { title: "Elasticsearch — Search & Analytics", description: "Distributed search and analytics engine. Full-text search, log analytics, and real-time data visualization with Kibana.", url: "https://github.com/elastic/elasticsearch", type: "github", category: "databases", source: "Elastic", tags: ["Search", "Analytics", "ELK"] },
  { title: "Neo4j — Graph Database", description: "The leading graph database platform. Cypher query language, graph algorithms, and visualization for connected data.", url: "https://github.com/neo4j/neo4j", type: "github", category: "databases", source: "Neo4j", tags: ["Graph", "Cypher", "Connected Data"] },
  { title: "How Google Built Spanner", description: "Google's globally-distributed database. TrueTime, distributed transactions, and strong consistency across continents.", url: "https://research.google/pubs/pub39966/", type: "case-study", category: "databases", source: "Google", tags: ["Spanner", "TrueTime", "Global"] },

  /* ==================  Expanded — System Design  ================== */
  { title: "How LinkedIn Built People You May Know", description: "LinkedIn's PYMK feature. Graph analysis, second-degree connections, and ML-based ranking for connection suggestions.", url: "https://engineering.linkedin.com/blog", type: "case-study", category: "system-design", source: "LinkedIn", tags: ["Graph", "PYMK", "Suggestions"] },
  { title: "How DoorDash Built Their Dispatch System", description: "DoorDash's order dispatch system. Batching optimization, Dasher routing, and real-time assignment across millions of deliveries.", url: "https://doordash.engineering/", type: "case-study", category: "system-design", source: "DoorDash", tags: ["Dispatch", "Batching", "Routing"] },
  { title: "How Lyft Built Their Geofencing Service", description: "Lyft's geofencing for pricing zones and airport pickups. Polygon queries, Redis caching, and sub-millisecond lookups.", url: "https://eng.lyft.com/", type: "case-study", category: "system-design", source: "Lyft", tags: ["Geofencing", "Polygons", "Caching"] },
  { title: "How Twitch Built Their Chat System", description: "Twitch's IRC-based chat at scale. Handling millions of concurrent chatters, message ordering, and real-time moderation.", url: "https://blog.twitch.tv/en/tags/engineering/", type: "case-study", category: "system-design", source: "Twitch", tags: ["Chat", "IRC", "Moderation"] },
  { title: "ByteByteGo Newsletter — Weekly System Design", description: "Weekly newsletter on system design. Architecture deep dives, visual explanations, and real-world case studies.", url: "https://blog.bytebytego.com/", type: "ebook", category: "system-design", source: "ByteByteGo", tags: ["Newsletter", "Weekly", "Visual"] },
  { title: "High Scalability Blog", description: "Blog analyzing architectures of the world's largest sites. How they handle scale, what technologies they use, and lessons learned.", url: "http://highscalability.com/", type: "ebook", category: "system-design", source: "High Scalability", tags: ["Blog", "Architecture", "Analysis"] },

  /* ==================  Expanded — Security  ================== */
  { title: "CWE/SANS Top 25 Software Errors", description: "The most common and dangerous software errors. Buffer overflow, injection, XSS, and root causes of security vulnerabilities.", url: "https://cwe.mitre.org/top25/", type: "ebook", category: "security", source: "MITRE", tags: ["CWE", "Top 25", "Errors"] },
  { title: "NIST Cybersecurity Framework", description: "NIST's framework for improving critical infrastructure cybersecurity. Identify, protect, detect, respond, recover.", url: "https://www.nist.gov/cyberframework", type: "ebook", category: "security", source: "NIST", tags: ["Framework", "Critical Infra", "Risk"] },
  { title: "How GitGuardian Detects Leaked Secrets", description: "GitGuardian's approach to detecting exposed secrets. Real-time scanning, pattern matching, and developer remediation workflows.", url: "https://www.gitguardian.com/blog", type: "case-study", category: "security", source: "GitGuardian", tags: ["Secrets", "Scanning", "Remediation"] },
  { title: "Burp Suite — Web Security Testing", description: "Industry-standard web security testing tool. Proxy, scanner, intruder, and repeater for manual and automated security testing.", url: "https://portswigger.net/burp", type: "course", category: "security", source: "PortSwigger", tags: ["Burp", "Web Testing", "Scanner"] },

  /* ==================  Expanded — Data Science  ================== */
  { title: "Kaggle — Data Science Competitions", description: "The world's largest data science community. Competitions, datasets, notebooks, and learning resources for ML practitioners.", url: "https://www.kaggle.com/", type: "course", category: "data-science", source: "Kaggle", tags: ["Competitions", "Community", "Datasets"] },
  { title: "Papers With Code — ML Papers", description: "Free and open resource with ML papers, code, datasets, methods, and evaluation tables. Track the latest in ML research.", url: "https://paperswithcode.com/", type: "ebook", category: "data-science", source: "Papers With Code", tags: ["Papers", "SOTA", "Benchmarks"] },
  { title: "Weights & Biases Reports — ML Articles", description: "Community-driven ML reports and articles. Experiment comparisons, model evaluations, and research walkthroughs.", url: "https://wandb.ai/fully-connected", type: "ebook", category: "data-science", source: "W&B", tags: ["Reports", "Community", "Research"] },
  { title: "How Shopify Uses Data Science for Commerce", description: "Shopify's data science applications. Fraud detection, marketing attribution, and product recommendations for millions of merchants.", url: "https://shopify.engineering/", type: "case-study", category: "data-science", source: "Shopify", tags: ["Commerce", "Fraud", "Attribution"] },

  /* ==================  Expanded — SQL  ================== */
  { title: "PostgreSQL Exercises — pgexercises.com", description: "Free PostgreSQL exercises with live queries. Schema design, JOINs, aggregation, window functions, and recursive queries.", url: "https://pgexercises.com/", type: "course", category: "sql", source: "pgexercises", tags: ["PostgreSQL", "Exercises", "Live"] },
  { title: "How Google Runs Spanner at Global Scale", description: "Google Spanner's SQL semantics at global scale. Strong consistency across regions, SQL dialect, and managing petabyte databases.", url: "https://research.google/", type: "case-study", category: "sql", source: "Google", tags: ["Spanner", "Global", "Strong Consistency"] },
  { title: "StrataScratch — SQL Interview Questions", description: "SQL and Python interview questions from real companies. Practice with questions from Meta, Amazon, Google, and more.", url: "https://www.stratascratch.com/", type: "course", category: "sql", source: "StrataScratch", tags: ["Interview", "Real Questions", "FAANG"] },

  /* ==================  Expanded — Mobile  ================== */
  { title: "Flutter — Cross-Platform UI Toolkit", description: "Google's UI toolkit for building natively compiled applications for mobile, web, and desktop from a single codebase.", url: "https://github.com/flutter/flutter", type: "github", category: "mobile", source: "Google", tags: ["Flutter", "Cross-Platform", "Dart"] },
  { title: "How Instagram Optimized Their Android App", description: "Instagram's Android performance optimization. Image loading, RecyclerView optimization, and reducing ANR rates.", url: "https://engineering.fb.com/", type: "case-study", category: "mobile", source: "Meta", tags: ["Android", "Performance", "ANR"] },
  { title: "How Uber Built Cross-Platform Driver App", description: "Uber's driver app architecture. Shared business logic, platform-specific UIs, and offline support for emerging markets.", url: "https://www.uber.com/blog/", type: "case-study", category: "mobile", source: "Uber", tags: ["Cross-Platform", "Driver", "Offline"] },

  /* ==================  Expanded — Cloud  ================== */
  { title: "How Databricks Built Their Lakehouse", description: "Databricks' lakehouse architecture combining data warehouse and data lake. Delta Lake, Photon engine, and Unity Catalog.", url: "https://www.databricks.com/blog", type: "case-study", category: "cloud", source: "Databricks", tags: ["Lakehouse", "Delta Lake", "Analytics"] },
  { title: "How Snowflake Built Their Data Cloud", description: "Snowflake's architecture separating storage and compute. Multi-cluster shared data, data sharing, and cross-cloud availability.", url: "https://www.snowflake.com/blog/", type: "case-study", category: "cloud", source: "Snowflake", tags: ["Data Cloud", "Separation", "Sharing"] },
  { title: "Kubernetes Patterns — Free eBook", description: "Design patterns for cloud-native applications on Kubernetes. Foundational, behavioral, structural, and configuration patterns.", url: "https://www.oreilly.com/library/view/kubernetes-patterns-2nd/9781098131678/", type: "ebook", category: "cloud", source: "O'Reilly", tags: ["Patterns", "Kubernetes", "Cloud Native"] },

  /* ==================  Expanded — Dart / Kotlin / Rust  ================== */
  { title: "Riverpod — Reactive State for Flutter", description: "Next-generation state management for Flutter. Compile-safe, testable, and provider-based with code generation support.", url: "https://github.com/rrousselGit/riverpod", type: "github", category: "dart", source: "Remi Rousselet", tags: ["Riverpod", "State", "Reactive"] },
  { title: "BLoC — Business Logic Component for Flutter", description: "Predictable state management library for Dart. Streams-based, testable, and with Flutter BLoC widgets for clean architecture.", url: "https://github.com/felangel/bloc", type: "github", category: "dart", source: "Felix Angelov", tags: ["BLoC", "Stream", "Architecture"] },
  { title: "Hilt — Dependency Injection for Android", description: "Google's recommended DI library for Android. Built on Dagger, with simplified APIs and Jetpack integration.", url: "https://developer.android.com/training/dependency-injection/hilt-android", type: "course", category: "kotlin", source: "Google", tags: ["Hilt", "DI", "Dagger"] },
  { title: "Ktor Client — Kotlin HTTP Client", description: "Kotlin multiplatform HTTP client. Coroutine-based, content negotiation, authentication, and WebSocket support.", url: "https://github.com/ktorio/ktor", type: "github", category: "kotlin", source: "JetBrains", tags: ["HTTP Client", "Multiplatform", "Coroutines"] },
  { title: "Tokio — Async Runtime for Rust", description: "Asynchronous runtime for Rust. Event-driven I/O, timers, synchronization, and the foundation for async Rust applications.", url: "https://github.com/tokio-rs/tokio", type: "github", category: "rust", source: "Tokio", tags: ["Async", "Runtime", "I/O"] },
  { title: "Serde — Serialization Framework for Rust", description: "The standard serialization framework for Rust. JSON, TOML, YAML, MessagePack, and custom format support with derive macros.", url: "https://github.com/serde-rs/serde", type: "github", category: "rust", source: "Serde", tags: ["Serialization", "JSON", "Derive"] },
  { title: "Clap — Command Line Parser for Rust", description: "Full-featured command line argument parser for Rust. Derive-based or builder API, completions, and colored help output.", url: "https://github.com/clap-rs/clap", type: "github", category: "rust", source: "Clap", tags: ["CLI", "Parser", "Arguments"] },

  /* ==================  More AI/ML — More Topics  ================== */
  { title: "How Snapchat Uses ML for AR Lenses", description: "Snapchat's ML pipeline for AR. Real-time face tracking, object detection, and running complex models on mobile devices.", url: "https://eng.snap.com/", type: "case-study", category: "ai-ml", source: "Snap", tags: ["AR", "Mobile ML", "Face Tracking"] },
  { title: "How Stripe Uses ML for Fraud Detection", description: "Stripe Radar's machine learning system. Card testing prevention, behavioral analysis, and reducing false positives in payments.", url: "https://stripe.com/blog/", type: "case-study", category: "ai-ml", source: "Stripe", tags: ["Fraud", "Payments", "Radar"] },
  { title: "How Reddit Uses ML for Content Safety", description: "Reddit's approach to content moderation. Automod, ML-based detection, and human-in-the-loop review processes.", url: "https://www.redditinc.com/blog", type: "case-study", category: "ai-ml", source: "Reddit", tags: ["Moderation", "Safety", "HITL"] },
  { title: "Hugging Face Transformers — NLP Library", description: "State-of-the-art NLP library. 100K+ pre-trained models, easy fine-tuning, and support for PyTorch, TensorFlow, and JAX.", url: "https://github.com/huggingface/transformers", type: "github", category: "ai-ml", source: "Hugging Face", tags: ["NLP", "Pretrained", "Transformers"] },
  { title: "Diffusers — Diffusion Model Library", description: "Hugging Face library for diffusion models. Stable Diffusion, DALL-E, ControlNet, and custom pipeline building.", url: "https://github.com/huggingface/diffusers", type: "github", category: "ai-ml", source: "Hugging Face", tags: ["Diffusion", "Image Gen", "Pipelines"] },

  /* ==================  More System Design & Backend  ================== */
  { title: "How Amazon Uses Microservices", description: "Amazon's microservice architecture evolution. From monolith to 2-pizza team services, service discovery, and team autonomy.", url: "https://www.amazon.science/", type: "case-study", category: "system-design", source: "Amazon", tags: ["Microservices", "Team Structure", "Evolution"] },
  { title: "How Etsy Handles 2B API Calls/Day", description: "Etsy's API infrastructure. GraphQL adoption, caching strategies, and serving marketplace data at scale.", url: "https://www.etsy.com/codeascraft", type: "case-study", category: "system-design", source: "Etsy", tags: ["API", "GraphQL", "Marketplace"] },
  { title: "How PayPal Handles Billions in Transactions", description: "PayPal's transaction processing system. Consistency, compliance, multi-currency, and handling payment disputes.", url: "https://medium.com/paypal-tech", type: "case-study", category: "system-design", source: "PayPal", tags: ["Payments", "Transactions", "Compliance"] },
  { title: "Clean Architecture — Robert C. Martin", description: "Uncle Bob's architecture guide. Dependency rule, SOLID principles, and building maintainable, testable software systems.", url: "https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/", type: "ebook", category: "backend", source: "O'Reilly", tags: ["Clean Arch", "SOLID", "Maintainability"] },
  { title: "Microservices Patterns — Chris Richardson", description: "Comprehensive patterns for microservices. Saga, CQRS, event sourcing, circuit breaker, and service mesh patterns.", url: "https://microservices.io/book", type: "ebook", category: "backend", source: "Manning", tags: ["Microservices", "Saga", "CQRS"] },
  { title: "Building Microservices — Sam Newman", description: "Designing fine-grained systems. Service boundaries, deployment, testing, monitoring, and organizational patterns.", url: "https://www.oreilly.com/library/view/building-microservices-2nd/9781492034018/", type: "ebook", category: "backend", source: "O'Reilly", tags: ["Microservices", "Design", "Organization"] },

  /* ==================  More Data Science  ================== */
  { title: "How Google Built BigQuery", description: "Google's serverless data warehouse. Dremel query engine, columnar storage, and processing petabytes of data on demand.", url: "https://research.google/", type: "case-study", category: "data-science", source: "Google", tags: ["BigQuery", "Serverless", "Dremel"] },
  { title: "How Uber Built Their Real-Time Analytics", description: "Uber's real-time analytics platform. Apache Pinot, streaming ingestion, and sub-second queries on trillions of records.", url: "https://www.uber.com/blog/", type: "case-study", category: "data-science", source: "Uber", tags: ["Real-Time", "Pinot", "Streaming"] },
  { title: "Apache Airflow — Workflow Orchestration", description: "Platform for programmatically authoring, scheduling, and monitoring workflows. DAGs, operators, and sensor-based triggers.", url: "https://github.com/apache/airflow", type: "github", category: "data-science", source: "Apache", tags: ["Airflow", "DAGs", "Scheduling"] },
  { title: "Superset — Modern Data Exploration", description: "Apache Superset is a modern data exploration and visualization platform. SQL Lab, dashboards, charts, and enterprise analytics.", url: "https://github.com/apache/superset", type: "github", category: "data-science", source: "Apache", tags: ["Visualization", "SQL Lab", "Dashboards"] },

  /* ==================  Wave 3 — AI/ML  ================== */
  { title: "vLLM — Fast LLM Inference", description: "High-throughput LLM serving engine. PagedAttention for efficient KV cache management, continuous batching, and tensor parallelism.", url: "https://github.com/vllm-project/vllm", type: "github", category: "ai-ml", source: "vLLM", tags: ["Inference", "PagedAttention", "Serving"] },
  { title: "Ollama — Run LLMs Locally", description: "Run large language models locally. Modelfile customization, model library, and REST API for local LLM deployment.", url: "https://github.com/ollama/ollama", type: "github", category: "ai-ml", source: "Ollama", tags: ["Local", "Easy", "Modelfile"] },
  { title: "LocalAI — Self-Hosted AI", description: "Free, self-hosted, local OpenAI-compatible API. Text generation, audio, image generation without GPU required.", url: "https://github.com/mudler/LocalAI", type: "github", category: "ai-ml", source: "LocalAI", tags: ["Self-Hosted", "API", "No GPU"] },
  { title: "MemGPT — Memory for LLMs", description: "Teach LLMs to manage their own memory. Long-term memory, self-editing context, and conversation history management.", url: "https://github.com/cpacker/MemGPT", type: "github", category: "ai-ml", source: "MemGPT", tags: ["Memory", "Long-Term", "Context"] },
  { title: "Instructor — Structured LLM Outputs", description: "Python library for getting structured outputs from LLMs. Pydantic models, retry logic, and streaming structured data.", url: "https://github.com/jxnl/instructor", type: "github", category: "ai-ml", source: "Jason Liu", tags: ["Structured", "Pydantic", "Validation"] },
  { title: "Guidance — Constrained Generation", description: "Microsoft's library for constraining LLM outputs. Token healing, regex constraints, and interleaving generation with logic.", url: "https://github.com/guidance-ai/guidance", type: "github", category: "ai-ml", source: "Microsoft", tags: ["Constraints", "Control", "Interleave"] },
  { title: "DeepSpeed — Deep Learning Optimization", description: "Microsoft's deep learning optimization library. ZeRO optimizer, pipeline parallelism, and training trillion-parameter models.", url: "https://github.com/microsoft/DeepSpeed", type: "github", category: "ai-ml", source: "Microsoft", tags: ["Optimization", "ZeRO", "Training"] },
  { title: "PEFT — Parameter-Efficient Fine-Tuning", description: "Hugging Face library for parameter-efficient fine-tuning. LoRA, QLoRA, prefix tuning, and prompt tuning methods.", url: "https://github.com/huggingface/peft", type: "github", category: "ai-ml", source: "Hugging Face", tags: ["PEFT", "LoRA", "QLoRA"] },
  { title: "Ray — Unified Framework for Scaling AI", description: "Scale AI and Python applications. Distributed computing, Ray Serve for model serving, and Ray Tune for hyperparameter tuning.", url: "https://github.com/ray-project/ray", type: "github", category: "ai-ml", source: "Anyscale", tags: ["Distributed", "Scaling", "Tune"] },
  { title: "Weights & Biases — ML Experiment Tracking", description: "Track ML experiments, visualize results, and collaborate. Hyperparameter sweeps, model registry, and dataset versioning.", url: "https://wandb.ai/", type: "course", category: "ai-ml", source: "W&B", tags: ["Tracking", "Experiment", "Collaboration"] },
  { title: "Stanford CS 224N — NLP with Deep Learning", description: "Stanford's NLP course. Word vectors, neural networks for NLP, attention, transformers, and pre-training methods.", url: "https://web.stanford.edu/class/cs224n/", type: "course", category: "ai-ml", source: "Stanford", tags: ["NLP", "Transformers", "Attention"] },
  { title: "MIT 6.S191 — Intro to Deep Learning", description: "MIT's introductory deep learning course. Neural networks, CNNs, RNNs, generative models, and reinforcement learning.", url: "https://introtodeeplearning.com/", type: "course", category: "ai-ml", source: "MIT", tags: ["Deep Learning", "Intro", "Comprehensive"] },
  { title: "How Tesla Trains Autopilot", description: "Tesla's approach to self-driving AI. Real-world data collection, shadow mode, neural network architecture, and simulation.", url: "https://www.tesla.com/AI", type: "case-study", category: "ai-ml", source: "Tesla", tags: ["Autopilot", "Self-Driving", "Simulation"] },
  { title: "How DeepMind Built AlphaFold", description: "DeepMind's protein structure prediction breakthrough. Attention-based architecture, MSA processing, and scientific impact.", url: "https://www.deepmind.com/blog", type: "case-study", category: "ai-ml", source: "DeepMind", tags: ["AlphaFold", "Protein", "Breakthrough"] },
  { title: "How OpenAI Trains Large Models", description: "OpenAI's training infrastructure. Distributed training, RLHF pipeline, data curation, and safety evaluation processes.", url: "https://openai.com/research", type: "case-study", category: "ai-ml", source: "OpenAI", tags: ["Training", "RLHF", "Safety"] },

  /* ==================  Wave 3 — Frontend  ================== */
  { title: "Astro — Content-Driven Framework", description: "Build faster websites with Astro. Islands architecture, zero JavaScript by default, and content collection API.", url: "https://github.com/withastro/astro", type: "github", category: "frontend", source: "Astro", tags: ["Islands", "Zero JS", "Content"] },
  { title: "Remix — Full Stack Web Framework", description: "Full stack framework focused on web fundamentals. Nested routing, progressive enhancement, and server-side rendering.", url: "https://github.com/remix-run/remix", type: "github", category: "frontend", source: "Shopify", tags: ["Full Stack", "Progressive", "Nested Routes"] },
  { title: "TanStack Query — Data Synchronization", description: "Powerful data synchronization for web apps. Caching, pagination, optimistic updates, and automatic background refetching.", url: "https://github.com/TanStack/query", type: "github", category: "frontend", source: "TanStack", tags: ["Data Sync", "Cache", "Queries"] },
  { title: "TanStack Router — Type-Safe Routing", description: "Type-safe routing for React applications. Search params validation, code splitting, and hierarchical data loading.", url: "https://github.com/TanStack/router", type: "github", category: "frontend", source: "TanStack", tags: ["Routing", "Type-Safe", "Search Params"] },
  { title: "Framer Motion — React Animations", description: "Production-ready animations for React. Layout animations, gesture recognition, and declarative animation API.", url: "https://github.com/framer/motion", type: "github", category: "frontend", source: "Framer", tags: ["Animations", "React", "Gestures"] },
  { title: "Vitest — Blazing Fast Unit Testing", description: "Vite-native unit test framework. Compatible with Jest API, instant watch mode, and component testing support.", url: "https://github.com/vitest-dev/vitest", type: "github", category: "frontend", source: "Vitest", tags: ["Testing", "Vite", "Jest Compatible"] },
  { title: "Playwright — End-to-End Testing", description: "Cross-browser end-to-end testing. Auto-wait, web-first assertions, and built-in Safari, Chrome, and Firefox testing.", url: "https://github.com/microsoft/playwright", type: "github", category: "frontend", source: "Microsoft", tags: ["E2E", "Cross-Browser", "Testing"] },
  { title: "Cypress — Component & E2E Testing", description: "Fast, easy, and reliable testing for anything that runs in a browser. Time travel debugging and real browser testing.", url: "https://github.com/cypress-io/cypress", type: "github", category: "frontend", source: "Cypress", tags: ["Testing", "E2E", "Debug"] },
  { title: "TypeScript Handbook — Official Guide", description: "Complete guide to TypeScript. Types, generics, utility types, decorators, and advanced patterns for large codebases.", url: "https://www.typescriptlang.org/docs/handbook/", type: "ebook", category: "frontend", source: "Microsoft", tags: ["TypeScript", "Official", "Handbook"] },
  { title: "JavaScript.info — Modern Tutorial", description: "Comprehensive modern JavaScript tutorial. Language features, browser APIs, network requests, and advanced patterns.", url: "https://javascript.info/", type: "ebook", category: "frontend", source: "JavaScript.info", tags: ["JavaScript", "Modern", "Comprehensive"] },
  { title: "How Vercel Builds Their Edge Network", description: "Vercel's edge deployment infrastructure. Serverless functions, ISR, edge middleware, and global CDN for Next.js apps.", url: "https://vercel.com/blog", type: "case-study", category: "frontend", source: "Vercel", tags: ["Edge", "Serverless", "CDN"] },

  /* ==================  Wave 3 — Backend  ================== */
  { title: "NestJS — Progressive Node.js Framework", description: "Server-side Node.js framework with TypeScript. Modules, dependency injection, guards, and OpenAPI integration.", url: "https://github.com/nestjs/nest", type: "github", category: "backend", source: "NestJS", tags: ["Node.js", "TypeScript", "Modular"] },
  { title: "tRPC — End-to-End Typesafe APIs", description: "Build typesafe APIs without schemas or code generation. Full type inference from backend to frontend in TypeScript.", url: "https://github.com/trpc/trpc", type: "github", category: "backend", source: "tRPC", tags: ["TypeSafe", "No Schema", "Full Stack"] },
  { title: "Drizzle ORM — Lightweight TypeScript ORM", description: "TypeScript ORM that is lightweight and performant. SQL-like queries, migrations, and type-safe database access.", url: "https://github.com/drizzle-team/drizzle-orm", type: "github", category: "backend", source: "Drizzle", tags: ["ORM", "TypeScript", "SQL-Like"] },
  { title: "Prisma — Next-Gen Node.js ORM", description: "Type-safe database toolkit. Auto-generated client, schema migrations, Prisma Studio, and multi-database support.", url: "https://github.com/prisma/prisma", type: "github", category: "backend", source: "Prisma", tags: ["ORM", "Type-Safe", "Migrations"] },
  { title: "Go — Systems Programming Language", description: "Google's simple, reliable, and efficient programming language. Goroutines, channels, and building scalable network services.", url: "https://github.com/golang/go", type: "github", category: "backend", source: "Google", tags: ["Go", "Concurrency", "Simple"] },
  { title: "How Discord Handles 1M+ Concurrent Voice Users", description: "Discord's voice infrastructure. WebRTC, selective forwarding, and scaling real-time audio for millions of users.", url: "https://discord.com/blog", type: "case-study", category: "backend", source: "Discord", tags: ["Voice", "WebRTC", "Real-Time"] },
  { title: "How Notion Built Their Real-Time Sync", description: "Notion's operational transformation (OT) system. Conflict resolution, real-time collaboration, and offline support.", url: "https://www.notion.so/blog", type: "case-study", category: "backend", source: "Notion", tags: ["Real-Time", "OT", "Collaboration"] },
  { title: "How Discord Stores Trillions of Messages", description: "Discord's migration from MongoDB to Cassandra to ScyllaDB. Handling trillions of messages with low-latency reads.", url: "https://discord.com/blog", type: "case-study", category: "backend", source: "Discord", tags: ["Messages", "ScyllaDB", "Migration"] },
  { title: "How Shopify Handles Flash Sales", description: "Shopify's infrastructure for flash sales. Auto-scaling, queue-based checkout, and handling 10K+ orders per second.", url: "https://shopify.engineering/", type: "case-study", category: "backend", source: "Shopify", tags: ["Flash Sales", "Auto-Scale", "Queue"] },

  /* ==================  Wave 3 — DevOps  ================== */
  { title: "Istio — Service Mesh", description: "Connect, secure, control, and observe microservices. Traffic management, security policies, and distributed tracing.", url: "https://github.com/istio/istio", type: "github", category: "devops", source: "Google", tags: ["Service Mesh", "Traffic", "Security"] },
  { title: "Linkerd — Ultralight Service Mesh", description: "Ultra-lightweight service mesh for Kubernetes. mTLS, observability, and reliability features with minimal resource usage.", url: "https://github.com/linkerd/linkerd2", type: "github", category: "devops", source: "Buoyant", tags: ["Service Mesh", "Lightweight", "mTLS"] },
  { title: "Crossplane — Cloud Infrastructure via K8s", description: "Manage cloud infrastructure using Kubernetes APIs. Compose resources across providers and GitOps-ready.", url: "https://github.com/crossplane/crossplane", type: "github", category: "devops", source: "CNCF", tags: ["Infrastructure", "K8s API", "Multi-Cloud"] },
  { title: "Kustomize — Kubernetes Config Management", description: "Template-free customization of Kubernetes configs. Overlays, patches, and managing multiple environments.", url: "https://github.com/kubernetes-sigs/kustomize", type: "github", category: "devops", source: "Kubernetes", tags: ["Config", "Overlays", "Environments"] },
  { title: "The Phoenix Project — DevOps Novel", description: "IT revolution novel illustrating DevOps principles. The Three Ways, flow, feedback, and continual learning.", url: "https://itrevolution.com/the-phoenix-project/", type: "ebook", category: "devops", source: "IT Revolution", tags: ["Novel", "Three Ways", "Culture"] },
  { title: "Accelerate — DevOps Science", description: "The science of lean software. Four key metrics, capabilities that drive performance, and evidence-based transformation.", url: "https://itrevolution.com/accelerate-book/", type: "ebook", category: "devops", source: "IT Revolution", tags: ["Metrics", "DORA", "Performance"] },

  /* ==================  Wave 3 — Security  ================== */
  { title: "Snyk — Developer Security Platform", description: "Find and fix vulnerabilities in code, open source, containers, and IaC. Developer-first security scanning.", url: "https://snyk.io/", type: "course", category: "security", source: "Snyk", tags: ["Dev Security", "Vulnerabilities", "Code"] },
  { title: "SonarQube — Code Quality & Security", description: "Continuous code quality and security inspection. Static analysis, code smells, security hotspots, and quality gates.", url: "https://github.com/SonarSource/sonarqube", type: "github", category: "security", source: "SonarSource", tags: ["Quality", "Static Analysis", "Gates"] },
  { title: "How Cloudflare Mitigates DDoS Attacks", description: "Cloudflare's DDoS protection. Anycast network, rate limiting, challenge pages, and handling the largest attacks in history.", url: "https://blog.cloudflare.com/", type: "case-study", category: "security", source: "Cloudflare", tags: ["DDoS", "Anycast", "Protection"] },
  { title: "How 1Password Designs Their Security Model", description: "1Password's security architecture. Secret Key, SRP authentication, zero-knowledge design, and breach response.", url: "https://1password.com/blog/", type: "case-study", category: "security", source: "1Password", tags: ["Zero Knowledge", "SRP", "Design"] },

  /* ==================  Wave 3 — System Design  ================== */
  { title: "How YouTube Handles 500 Hours of Video/Minute", description: "YouTube's video pipeline. Ingestion, transcoding, CDN distribution, and recommendation at massive scale.", url: "https://blog.youtube/", type: "case-study", category: "system-design", source: "YouTube", tags: ["Video", "Transcoding", "CDN"] },
  { title: "How Pinterest Built Their Search Engine", description: "Pinterest's visual search infrastructure. Image embeddings, query understanding, and personalized discovery.", url: "https://medium.com/pinterest-engineering/", type: "case-study", category: "system-design", source: "Pinterest", tags: ["Visual Search", "Embeddings", "Discovery"] },
  { title: "How Zoom Handles 300M Daily Participants", description: "Zoom's real-time communication architecture. Media processing, noise cancellation, and global infrastructure for video calls.", url: "https://blog.zoom.us/", type: "case-study", category: "system-design", source: "Zoom", tags: ["Video Calls", "Real-Time", "Media"] },
  { title: "How Discord Scales Their WebSocket Server", description: "Discord's Elixir-based gateway. WebSocket management, sharding, guild distribution, and handling millions of concurrent connections.", url: "https://discord.com/blog", type: "case-study", category: "system-design", source: "Discord", tags: ["WebSocket", "Elixir", "Gateway"] },
  { title: "System Design Primer — Comprehensive Guide", description: "Comprehensive resource for system design interviews. Load balancing, caching, databases, CDNs, and microservices.", url: "https://github.com/donnemartin/system-design-primer", type: "github", category: "system-design", source: "Donne Martin", tags: ["Primer", "Comprehensive", "Interview"] },
  { title: "How Shopify Runs Their Platform at Scale", description: "Shopify's multi-tenant architecture. Pod-based sharding, deployment strategies, and handling Black Friday/Cyber Monday.", url: "https://shopify.engineering/", type: "case-study", category: "system-design", source: "Shopify", tags: ["Multi-Tenant", "Pods", "BFCM"] },

  /* ==================  Wave 3 — Data Science  ================== */
  { title: "DuckDB — In-Process Analytics Database", description: "Fast in-process analytical database. Columnar storage, vectorized execution, and zero-dependency SQL analytics.", url: "https://github.com/duckdb/duckdb", type: "github", category: "data-science", source: "DuckDB", tags: ["In-Process", "Columnar", "Analytics"] },
  { title: "Polars — Fast DataFrame Library", description: "Lightning fast DataFrame library for Rust and Python. Lazy evaluation, query optimization, and multi-threaded execution.", url: "https://github.com/pola-rs/polars", type: "github", category: "data-science", source: "Polars", tags: ["DataFrame", "Rust", "Fast"] },
  { title: "dbt — Data Build Tool", description: "Transform data in your warehouse using SQL. Modular analytics, version control, testing, and documentation.", url: "https://github.com/dbt-labs/dbt-core", type: "github", category: "data-science", source: "dbt Labs", tags: ["Transform", "SQL", "Modular"] },
  { title: "How Spotify Built Backstage", description: "Spotify's developer portal platform. Service catalog, software templates, and plugin architecture for developer experience.", url: "https://engineering.atspotify.com/", type: "case-study", category: "data-science", source: "Spotify", tags: ["Backstage", "Developer Portal", "Catalog"] },

  /* ==================  Wave 3 — SQL  ================== */
  { title: "LeetCode SQL 50 — Interview Practice", description: "Top 50 SQL interview questions on LeetCode. Ranked by difficulty with solutions covering joins, aggregations, and window functions.", url: "https://leetcode.com/studyplan/top-sql-50/", type: "course", category: "sql", source: "LeetCode", tags: ["Interview", "Top 50", "Practice"] },
  { title: "HackerRank SQL — Challenges", description: "SQL challenges by difficulty level. Basic select, advanced joins, aggregations, and alternative queries.", url: "https://www.hackerrank.com/domains/sql", type: "course", category: "sql", source: "HackerRank", tags: ["Challenges", "Difficulty", "Practice"] },
  { title: "SQL Performance Explained — O'Reilly", description: "In-depth guide to SQL performance. Indexing strategies, join algorithms, execution plans, and query optimization.", url: "https://sql-performance-explained.com/", type: "ebook", category: "sql", source: "Markus Winand", tags: ["Performance", "Execution Plans", "Indexing"] },

  /* ==================  Wave 3 — Databases  ================== */
  { title: "SurrealDB — Multi-Model Database", description: "All-in-one database for modern apps. Documents, graphs, full-text search, and real-time queries in a single platform.", url: "https://github.com/surrealdb/surrealdb", type: "github", category: "databases", source: "SurrealDB", tags: ["Multi-Model", "Graph", "Real-Time"] },
  { title: "CockroachDB — Distributed SQL", description: "Distributed SQL database designed for cloud-native apps. PostgreSQL compatibility, serializable isolation, and multi-region.", url: "https://github.com/cockroachdb/cockroach", type: "github", category: "databases", source: "Cockroach Labs", tags: ["Distributed SQL", "PostgreSQL", "Multi-Region"] },
  { title: "Turso — Edge SQLite Database", description: "SQLite-based database for the edge. libSQL fork, embedded replicas, and globally distributed reads.", url: "https://github.com/tursodatabase/libsql", type: "github", category: "databases", source: "Turso", tags: ["SQLite", "Edge", "Replicas"] },
  { title: "How Notion Migrated Their Database", description: "Notion's migration from PostgreSQL monolith to sharded architecture. Data partitioning and zero-downtime migrations.", url: "https://www.notion.so/blog", type: "case-study", category: "databases", source: "Notion", tags: ["Migration", "Sharding", "Zero-Downtime"] },

  /* ==================  Wave 3 — Mobile  ================== */
  { title: "Capacitor — Cross-Platform Mobile Runtime", description: "Cross-platform runtime for web apps. Use any web framework and deploy to iOS, Android, and web with native APIs.", url: "https://github.com/ionic-team/capacitor", type: "github", category: "mobile", source: "Ionic", tags: ["Capacitor", "Web", "Native APIs"] },
  { title: "KMM — Kotlin Multiplatform Mobile", description: "Share business logic between iOS and Android. Kotlin code, platform-specific UIs, and gradual adoption.", url: "https://kotlinlang.org/lp/multiplatform/", type: "course", category: "mobile", source: "JetBrains", tags: ["KMM", "Sharing", "Gradual"] },
  { title: "How TikTok Optimized Their Feed Performance", description: "TikTok's feed performance optimization. Pre-loading, memory management, and achieving smooth scrolling on low-end devices.", url: "https://newsroom.tiktok.com/", type: "case-study", category: "mobile", source: "TikTok", tags: ["Feed", "Pre-Loading", "Low-End"] },

  /* ==================  Wave 3 — Cloud  ================== */
  { title: "Pulumi — IaC with Programming Languages", description: "Infrastructure as code using TypeScript, Python, Go, and C#. State management, testing, and multi-cloud provisioning.", url: "https://github.com/pulumi/pulumi", type: "github", category: "cloud", source: "Pulumi", tags: ["IaC", "Code", "Multi-Language"] },
  { title: "How Vercel Scales Their Edge Network", description: "Vercel's global edge infrastructure. Serverless functions, smart routing, and serving billions of requests per day.", url: "https://vercel.com/blog", type: "case-study", category: "cloud", source: "Vercel", tags: ["Edge", "Global", "Routing"] },
  { title: "How Fly.io Runs VMs Globally", description: "Fly.io's approach to running apps close to users. Firecracker VMs, anycast networking, and multi-region deployment.", url: "https://fly.io/blog/", type: "case-study", category: "cloud", source: "Fly.io", tags: ["VMs", "Firecracker", "Global"] },

  /* ==================  Wave 3 — Dart/Flutter  ================== */
  { title: "Flutter Hooks — React-Style Hooks", description: "React-like hooks for Flutter. useState, useEffect, useMemoized, and building custom hooks for clean widget logic.", url: "https://github.com/rrousselGit/flutter_hooks", type: "github", category: "dart", source: "Remi Rousselet", tags: ["Hooks", "React-Like", "Clean"] },
  { title: "Freezed — Code Generation for Dart", description: "Code generation for immutable classes and unions in Dart. Sealed classes, copyWith, JSON serialization, and pattern matching.", url: "https://github.com/rrousselGit/freezed", type: "github", category: "dart", source: "Remi Rousselet", tags: ["Code Gen", "Immutable", "Sealed"] },
  { title: "Flutter Performance Best Practices", description: "Official guide to Flutter performance. Widget rebuilds, shader compilation, image caching, and profiling with DevTools.", url: "https://docs.flutter.dev/perf/best-practices", type: "ebook", category: "dart", source: "Flutter", tags: ["Performance", "Profiling", "DevTools"] },

  /* ==================  Wave 3 — Kotlin  ================== */
  { title: "Compose Multiplatform — JetBrains", description: "Share UI code across Android, iOS, desktop, and web using Compose. Single codebase for truly cross-platform apps.", url: "https://github.com/JetBrains/compose-multiplatform", type: "github", category: "kotlin", source: "JetBrains", tags: ["Compose", "Multiplatform", "Shared UI"] },
  { title: "Arrow — Functional Kotlin", description: "Functional programming library for Kotlin. Either, Option, Validated, and effect handlers for type-safe error handling.", url: "https://github.com/arrow-kt/arrow", type: "github", category: "kotlin", source: "Arrow", tags: ["Functional", "Either", "Type Safety"] },
  { title: "Kotlin in Action — JetBrains Guide", description: "Comprehensive Kotlin book by JetBrains developers. From basics to advanced coroutines, DSLs, and multiplatform projects.", url: "https://kotlinlang.org/docs/getting-started.html", type: "ebook", category: "kotlin", source: "JetBrains", tags: ["Book", "Comprehensive", "Official"] },

  /* ==================  Wave 3 — Rust  ================== */
  { title: "Leptos — Full-Stack Rust Web Framework", description: "Full-stack web framework in Rust. Fine-grained reactivity, SSR, and both client-side and server-side rendering.", url: "https://github.com/leptos-rs/leptos", type: "github", category: "rust", source: "Leptos", tags: ["Web", "Reactivity", "Full-Stack"] },
  { title: "Tauri — Build Desktop Apps with Web Tech", description: "Build lightweight desktop applications with web frontend and Rust backend. Small bundle sizes and native system access.", url: "https://github.com/tauri-apps/tauri", type: "github", category: "rust", source: "Tauri", tags: ["Desktop", "Web Tech", "Lightweight"] },
  { title: "How Discord Switched from Go to Rust", description: "Discord's migration of their Read States service from Go to Rust. Eliminating GC pauses and improving tail latencies.", url: "https://discord.com/blog/why-discord-is-switching-from-go-to-rust", type: "case-study", category: "rust", source: "Discord", tags: ["Go to Rust", "GC", "Latency"] },
  { title: "Rustlings — Learn Rust by Exercises", description: "Small exercises for getting used to reading and writing Rust code. Covers ownership, structs, enums, error handling, and traits.", url: "https://github.com/rust-lang/rustlings", type: "course", category: "rust", source: "Rust Foundation", tags: ["Exercises", "Interactive", "Beginner"] },

  /* ==================  Wave 3 — More Cross-Category  ================== */
  { title: "How GitHub Built Copilot", description: "GitHub Copilot's architecture. Codex model integration, context gathering, suggestion ranking, and responsible AI deployment.", url: "https://github.blog/", type: "case-study", category: "ai-ml", source: "GitHub", tags: ["Copilot", "Code Gen", "AI Pair"] },
  { title: "How Cursor Built Their AI Code Editor", description: "Cursor's approach to AI-assisted coding. Context understanding, code prediction, and integrating LLMs into the editing experience.", url: "https://cursor.com/blog", type: "case-study", category: "ai-ml", source: "Cursor", tags: ["Code Editor", "AI", "Context"] },
  { title: "How Canva Scales Their Design Platform", description: "Canva's architecture serving 100M+ monthly users. Template rendering, real-time collaboration, and media processing at scale.", url: "https://www.canva.dev/blog/engineering/", type: "case-study", category: "system-design", source: "Canva", tags: ["Design", "Collaboration", "Rendering"] },
  { title: "How Linear Built Their Project Management", description: "Linear's engineering principles. Optimistic UI, real-time sync, and building a fast project management tool.", url: "https://linear.app/blog/", type: "case-study", category: "frontend", source: "Linear", tags: ["Project Mgmt", "Optimistic UI", "Speed"] },
  { title: "How Figma Built Multi-Player Editing", description: "Figma's real-time collaboration system. CRDT-based state, WebSocket communication, and conflict-free concurrent editing.", url: "https://www.figma.com/blog/", type: "case-study", category: "system-design", source: "Figma", tags: ["Multiplayer", "CRDT", "Real-Time"] },
  { title: "How Slack Built Their Desktop App", description: "Slack's desktop app architecture. Electron optimization, workspaces management, and reducing memory usage.", url: "https://slack.engineering/", type: "case-study", category: "frontend", source: "Slack", tags: ["Desktop", "Electron", "Memory"] },
  { title: "How Vercel Built Next.js", description: "The evolution of Next.js from pages to app router. Server components, streaming, and the future of React frameworks.", url: "https://vercel.com/blog", type: "case-study", category: "frontend", source: "Vercel", tags: ["Next.js", "App Router", "RSC"] },
  { title: "How Supabase Built Their Platform", description: "Supabase's architecture as an open-source Firebase alternative. PostgreSQL extensions, real-time engine, and edge functions.", url: "https://supabase.com/blog", type: "case-study", category: "backend", source: "Supabase", tags: ["BaaS", "PostgreSQL", "Real-Time"] },
  { title: "How PlanetScale Handles Database Branching", description: "PlanetScale's non-blocking schema changes using Vitess. Database branches, deploy requests, and online DDL.", url: "https://planetscale.com/blog", type: "case-study", category: "databases", source: "PlanetScale", tags: ["Branching", "Vitess", "Online DDL"] },
  { title: "The Twelve-Factor App — Methodology", description: "Best practices for building modern SaaS applications. Config, dependencies, build-release-run, and stateless processes.", url: "https://12factor.net/", type: "ebook", category: "devops", source: "Heroku", tags: ["12 Factor", "Methodology", "SaaS"] },
  { title: "Google SRE Book — Free Online", description: "Google's SRE book available for free. 24 chapters covering SRE principles, practices, management, and on-call.", url: "https://sre.google/sre-book/table-of-contents/", type: "ebook", category: "devops", source: "Google", tags: ["SRE", "Free", "Comprehensive"] },
  { title: "Awesome System Design Resources", description: "Curated list of system design resources. Articles, papers, talks, and courses for building large-scale distributed systems.", url: "https://github.com/madd86/awesome-system-design", type: "github", category: "system-design", source: "Community", tags: ["Awesome List", "Curated", "Resources"] },
  { title: "Coding Interview University", description: "Complete computer science study plan. Data structures, algorithms, system design, and preparation for technical interviews.", url: "https://github.com/jwasham/coding-interview-university", type: "github", category: "system-design", source: "John Washam", tags: ["Interview Prep", "CS Fundamentals", "Study Plan"] },

  /* ==================  Final Wave — Cross Category  ================== */
  { title: "ChromaDB — AI Embedding Database", description: "Open-source embedding database for AI applications. Store, search, and filter embeddings for RAG and similarity search.", url: "https://github.com/chroma-core/chroma", type: "github", category: "ai-ml", source: "Chroma", tags: ["Embeddings", "Vector DB", "RAG"] },
  { title: "Pinecone — Vector Database Guide", description: "Learn about vector databases for AI. Embedding similarity search, indexing strategies, and building semantic search.", url: "https://www.pinecone.io/learn/", type: "ebook", category: "ai-ml", source: "Pinecone", tags: ["Vector DB", "Semantic Search", "Guide"] },
  { title: "Replicate — Run ML Models in the Cloud", description: "Run open-source ML models with an API. Stable Diffusion, LLaMA, and thousands of models with simple deployment.", url: "https://replicate.com/", type: "course", category: "ai-ml", source: "Replicate", tags: ["Cloud ML", "API", "Models"] },
  { title: "Modal — Serverless Cloud for AI", description: "Run generative AI models, large-scale batch jobs, and intensive async tasks. GPU orchestration and serverless containers.", url: "https://github.com/modal-labs/modal-client", type: "github", category: "ai-ml", source: "Modal", tags: ["Serverless", "GPU", "AI Cloud"] },
  { title: "Gradio — ML Web Interfaces", description: "Create machine learning demos quickly. Interactive web interfaces for ML models with just a few lines of Python.", url: "https://github.com/gradio-app/gradio", type: "github", category: "ai-ml", source: "Hugging Face", tags: ["Demo", "Web UI", "Quick"] },
  { title: "Anthropic Courses — Claude AI", description: "Official training materials for building with Claude. Prompt engineering, RAG implementation, and API best practices.", url: "https://docs.anthropic.com/", type: "course", category: "ai-ml", source: "Anthropic", tags: ["Claude", "Prompt Engineering", "Official"] },
  { title: "How Shopify Uses AI for Product Descriptions", description: "Shopify Magic's AI-powered product descriptions. Fine-tuned language models, merchant-specific tone, and multi-language support.", url: "https://shopify.engineering/", type: "case-study", category: "ai-ml", source: "Shopify", tags: ["Product", "Descriptions", "Commerce"] },
  { title: "How Duolingo Uses AI for Language Learning", description: "Duolingo's AI-powered learning platform. Adaptive difficulty, GPT-4 roleplay partner, and personalized lesson generation.", url: "https://blog.duolingo.com/", type: "case-study", category: "ai-ml", source: "Duolingo", tags: ["Education", "Adaptive", "GPT"] },
  { title: "How Grammarly Uses NLP for Writing", description: "Grammarly's NLP infrastructure. Grammar checking, tone detection, plagiarism detection, and generative writing assistance.", url: "https://www.grammarly.com/blog/engineering/", type: "case-study", category: "ai-ml", source: "Grammarly", tags: ["Writing", "NLP", "Tone"] },

  { title: "Bun — All-in-One JavaScript Runtime", description: "Fast JavaScript runtime, bundler, transpiler, and package manager. Drop-in Node.js replacement written in Zig.", url: "https://github.com/oven-sh/bun", type: "github", category: "frontend", source: "Oven", tags: ["Runtime", "Bundler", "Fast"] },
  { title: "D3.js — Data-Driven Documents", description: "The most powerful data visualization library. SVG, Canvas, and HTML manipulation with data binding and transitions.", url: "https://github.com/d3/d3", type: "github", category: "frontend", source: "Observable", tags: ["D3", "SVG", "Visualization"] },
  { title: "Three.js — 3D Graphics for Web", description: "Create 3D content for the web. WebGL renderer, scenes, cameras, lights, materials, and post-processing effects.", url: "https://github.com/mrdoob/three.js", type: "github", category: "frontend", source: "Three.js", tags: ["3D", "WebGL", "Graphics"] },
  { title: "Excalidraw — Virtual Whiteboard", description: "Open-source virtual whiteboard for sketching. Collaborative drawing, export to SVG/PNG, and embeddable component.", url: "https://github.com/excalidraw/excalidraw", type: "github", category: "frontend", source: "Excalidraw", tags: ["Whiteboard", "Drawing", "Collaborative"] },
  { title: "tldraw — Drawing Library", description: "A collaborative digital whiteboard library. React component, multiplayer support, and customizable shape system.", url: "https://github.com/tldraw/tldraw", type: "github", category: "frontend", source: "tldraw", tags: ["Drawing", "React", "Multiplayer"] },
  { title: "Shadcn UI — Re-Usable Components", description: "Beautifully designed, accessible UI components built with Radix UI. Copy and paste into your apps with full customization.", url: "https://github.com/shadcn-ui/ui", type: "github", category: "frontend", source: "shadcn", tags: ["UI", "Radix", "Accessible"] },
  { title: "Radix UI — Primitive Components", description: "Open-source primitive UI components. Accessible, unstyled, and composable building blocks for building design systems.", url: "https://github.com/radix-ui/primitives", type: "github", category: "frontend", source: "Radix", tags: ["Primitives", "Accessible", "Unstyled"] },

  { title: "Django — Python Web Framework", description: "The web framework for perfectionists with deadlines. ORM, admin panel, authentication, and batteries-included approach.", url: "https://github.com/django/django", type: "github", category: "backend", source: "Django", tags: ["Python", "Batteries", "Admin"] },
  { title: "Gin — Go Web Framework", description: "HTTP web framework written in Go. Built with performance in mind, middleware support, and JSON validation.", url: "https://github.com/gin-gonic/gin", type: "github", category: "backend", source: "Gin", tags: ["Go", "Fast", "Middleware"] },
  { title: "Fiber — Express-Inspired Go Framework", description: "Express-inspired web framework built on Fasthttp. Fastest Go web framework with familiar API and built-in middleware.", url: "https://github.com/gofiber/fiber", type: "github", category: "backend", source: "Fiber", tags: ["Go", "Express-Like", "Fasthttp"] },
  { title: "Temporal — Workflow Engine", description: "Open-source durable execution platform. Reliable workflow orchestration, retries, and long-running processes.", url: "https://github.com/temporalio/temporal", type: "github", category: "backend", source: "Temporal", tags: ["Workflows", "Durable", "Orchestration"] },
  { title: "Bull — Node.js Job Queue", description: "Premium queue package for handling distributed jobs and messages in Node.js. Redis-based, reliable, and fast.", url: "https://github.com/OptimalBits/bull", type: "github", category: "backend", source: "OptimalBits", tags: ["Queue", "Redis", "Jobs"] },
  { title: "How Slack Built Thread Notifications", description: "Slack's thread notification system. Fan-out patterns, notification deduplication, and user preference management.", url: "https://slack.engineering/", type: "case-study", category: "backend", source: "Slack", tags: ["Notifications", "Fan-Out", "Threads"] },

  { title: "Helm — Kubernetes Package Manager", description: "Package manager for Kubernetes. Charts, releases, repositories, and managing complex application deployments.", url: "https://github.com/helm/helm", type: "github", category: "devops", source: "CNCF", tags: ["Helm", "Charts", "Kubernetes"] },
  { title: "Flux — GitOps for Kubernetes", description: "GitOps toolkit for Kubernetes. Automated deployments, image automation, and multi-tenancy with Git as source of truth.", url: "https://github.com/fluxcd/flux2", type: "github", category: "devops", source: "CNCF", tags: ["GitOps", "Automated", "Multi-Tenant"] },
  { title: "Falco — Runtime Security for K8s", description: "Cloud-native runtime security. Detect anomalous activity in real-time using system calls, Kubernetes audit logs, and rules.", url: "https://github.com/falcosecurity/falco", type: "github", category: "devops", source: "CNCF", tags: ["Runtime", "Security", "Detection"] },
  { title: "OpenTelemetry — Observability Framework", description: "Vendor-neutral observability framework. Traces, metrics, and logs with unified collection and export to any backend.", url: "https://github.com/open-telemetry/opentelemetry-specification", type: "github", category: "devops", source: "CNCF", tags: ["Observability", "Traces", "Metrics"] },

  { title: "How Spotify Handles 100M+ Tracks", description: "Spotify's music catalog system. Content ingestion, metadata management, and serving audio files at global scale.", url: "https://engineering.atspotify.com/", type: "case-study", category: "system-design", source: "Spotify", tags: ["Music", "Catalog", "Audio"] },
  { title: "How Reddit Scales Their Comment System", description: "Reddit's comment threading system. Tree structures, ranking algorithms, and handling viral posts with millions of comments.", url: "https://www.redditinc.com/blog", type: "case-study", category: "system-design", source: "Reddit", tags: ["Comments", "Trees", "Ranking"] },
  { title: "How Notion Built Their Block Editor", description: "Notion's block-based editor architecture. Custom blocks, real-time collaboration, and platform-specific rendering.", url: "https://www.notion.so/blog", type: "case-study", category: "system-design", source: "Notion", tags: ["Editor", "Blocks", "CRDT"] },
  { title: "How Wikipedia Serves 6B+ Page Views/Month", description: "Wikipedia's infrastructure. MediaWiki, Varnish caching, and serving the world's knowledge on donated infrastructure.", url: "https://wikitech.wikimedia.org/", type: "case-study", category: "system-design", source: "Wikimedia", tags: ["Wikipedia", "Caching", "Open Source"] },

  { title: "TimescaleDB — Time Series Database", description: "PostgreSQL extension for time-series data. Hypertables, continuous aggregations, and compression for IoT and metrics.", url: "https://github.com/timescale/timescaledb", type: "github", category: "databases", source: "Timescale", tags: ["Time Series", "PostgreSQL", "IoT"] },
  { title: "ScyllaDB — Low-Latency NoSQL", description: "Cassandra-compatible database written in C++. 10x lower latency, auto-tuning, and simplified operations.", url: "https://github.com/scylladb/scylladb", type: "github", category: "databases", source: "ScyllaDB", tags: ["Low-Latency", "Cassandra", "C++"] },
  { title: "Neon — Serverless PostgreSQL", description: "Serverless PostgreSQL with autoscaling. Database branching, point-in-time restore, and scale-to-zero for cost savings.", url: "https://github.com/neondatabase/neon", type: "github", category: "databases", source: "Neon", tags: ["Serverless", "Branching", "PostgreSQL"] },

  { title: "Postman — API Testing Platform", description: "Complete API testing and development platform. Collections, automated testing, mock servers, and API documentation.", url: "https://www.postman.com/", type: "course", category: "backend", source: "Postman", tags: ["API", "Testing", "Documentation"] },
  { title: "Insomnia — REST & GraphQL Client", description: "Open-source API client for REST and GraphQL. Environment variables, plugins, and Git sync for team collaboration.", url: "https://github.com/Kong/insomnia", type: "github", category: "backend", source: "Kong", tags: ["REST", "GraphQL", "Client"] },

  { title: "Solidity — Smart Contract Language", description: "Language for writing smart contracts on Ethereum. Events, modifiers, inheritance, and interacting with the EVM.", url: "https://docs.soliditylang.org/", type: "ebook", category: "backend", source: "Ethereum", tags: ["Blockchain", "Smart Contracts", "EVM"] },
  { title: "Hardhat — Ethereum Development", description: "Professional development environment for Ethereum. Testing, debugging, deployment, and Solidity compiler management.", url: "https://github.com/NomicFoundation/hardhat", type: "github", category: "backend", source: "Nomic Foundation", tags: ["Ethereum", "Testing", "Solidity"] },

  { title: "W3Schools SQL Tutorial", description: "Beginner-friendly SQL tutorial. Interactive examples for SELECT, INSERT, UPDATE, DELETE, and common SQL functions.", url: "https://www.w3schools.com/sql/", type: "course", category: "sql", source: "W3Schools", tags: ["Beginner", "Interactive", "Tutorial"] },
  { title: "SQL Murder Mystery — Practice Game", description: "Learn SQL by solving a murder mystery. Walk through a database schema and write queries to find the killer.", url: "https://mystery.knightlab.com/", type: "course", category: "sql", source: "Knight Lab", tags: ["Game", "Mystery", "Fun"] },

  { title: "Cloudflare Workers — Edge Computing", description: "Run JavaScript at the edge across 300+ cities. V8 isolates, KV storage, Durable Objects, and D1 SQLite database.", url: "https://developers.cloudflare.com/workers/", type: "course", category: "cloud", source: "Cloudflare", tags: ["Edge", "Workers", "V8 Isolates"] },
  { title: "Vercel Edge Functions", description: "Deploy serverless functions at the edge. Middleware, geolocation, and low-latency responses from 20+ regions.", url: "https://vercel.com/docs/functions/edge-functions", type: "course", category: "cloud", source: "Vercel", tags: ["Edge", "Serverless", "Low-Latency"] },

  { title: "OWASP API Security Top 10", description: "Top 10 API security risks. Broken authentication, excessive data exposure, injection, and rate limiting best practices.", url: "https://owasp.org/www-project-api-security/", type: "ebook", category: "security", source: "OWASP", tags: ["API Security", "Top 10", "Best Practices"] },
  { title: "Let's Encrypt — Free HTTPS Certificates", description: "Free, automated, and open certificate authority. ACME protocol, certbot, and enabling HTTPS for all websites.", url: "https://letsencrypt.org/docs/", type: "ebook", category: "security", source: "Let's Encrypt", tags: ["HTTPS", "Certificates", "Free"] },

  { title: "Pandas — Python Data Analysis Library", description: "Powerful data analysis and manipulation tool. DataFrames, time series, reading/writing CSV/Excel/SQL, and group-by operations.", url: "https://github.com/pandas-dev/pandas", type: "github", category: "data-science", source: "Pandas", tags: ["DataFrame", "Analysis", "Python"] },
  { title: "NumPy — Numerical Computing for Python", description: "Fundamental package for scientific computing. N-dimensional arrays, broadcasting, linear algebra, and random number generation.", url: "https://github.com/numpy/numpy", type: "github", category: "data-science", source: "NumPy", tags: ["Arrays", "Scientific", "Linear Algebra"] },
  { title: "Matplotlib — Python Visualization", description: "Comprehensive library for creating static, animated, and interactive visualizations. Plots, histograms, and 3D surfaces.", url: "https://github.com/matplotlib/matplotlib", type: "github", category: "data-science", source: "Matplotlib", tags: ["Plots", "Visualization", "Python"] },
  { title: "Jupyter — Interactive Computing", description: "Web-based interactive computing platform. Notebooks, code execution, visualization, and multi-language kernel support.", url: "https://github.com/jupyter/notebook", type: "github", category: "data-science", source: "Jupyter", tags: ["Notebooks", "Interactive", "Multi-Language"] },

  { title: "Flutter Awesome — Curated Packages", description: "Curated list of awesome Flutter packages, libraries, tools, and projects. Organized by category with descriptions and ratings.", url: "https://github.com/Solido/awesome-flutter", type: "github", category: "dart", source: "Community", tags: ["Awesome", "Packages", "Curated"] },
  { title: "Dart Language Tour — Official Guide", description: "Complete tour of the Dart language. Variables, functions, classes, generics, async/await, and null safety.", url: "https://dart.dev/language", type: "ebook", category: "dart", source: "Dart", tags: ["Language Tour", "Official", "Null Safety"] },

  { title: "Kotlin Multiplatform Wizard", description: "Interactive tool for creating KMP projects. Choose targets (Android, iOS, web, desktop), dependencies, and project structure.", url: "https://kmp.jetbrains.com/", type: "course", category: "kotlin", source: "JetBrains", tags: ["Wizard", "Interactive", "Project Setup"] },
  { title: "Android Developer Roadmap — 2024", description: "Comprehensive Android development roadmap. Architecture, UI, testing, and modern Android development with Kotlin.", url: "https://github.com/skydoves/android-developer-roadmap", type: "github", category: "kotlin", source: "Jaewoong Eum", tags: ["Roadmap", "Android", "2024"] },

  { title: "Rust by Example — Official Guide", description: "Collection of runnable Rust examples. Learn Rust through hands-on coding with extensive examples and explanations.", url: "https://doc.rust-lang.org/rust-by-example/", type: "ebook", category: "rust", source: "Rust Foundation", tags: ["Examples", "Hands-On", "Official"] },
  { title: "Awesome Rust — Curated List", description: "Curated list of Rust code and resources. Web frameworks, game engines, databases, and CLI tools written in Rust.", url: "https://github.com/rust-unofficial/awesome-rust", type: "github", category: "rust", source: "Community", tags: ["Awesome", "Curated", "Ecosystem"] },

  { title: "How Notion Reduced Latency by 20%", description: "Notion's performance optimization journey. Database query optimization, caching strategies, and reducing time-to-interactive.", url: "https://www.notion.so/blog", type: "case-study", category: "frontend", source: "Notion", tags: ["Performance", "Latency", "TTI"] },
  { title: "How GitHub Makes Their Homepage Fast", description: "GitHub's homepage performance engineering. Asset optimization, SSR, lazy loading, and achieving sub-second load times.", url: "https://github.blog/", type: "case-study", category: "frontend", source: "GitHub", tags: ["Homepage", "Fast", "SSR"] },
  { title: "How Medium Built Their Text Editor", description: "Medium's rich text editor architecture. ContentEditable, custom block system, and cross-browser compatibility challenges.", url: "https://medium.engineering/", type: "case-study", category: "frontend", source: "Medium", tags: ["Editor", "Rich Text", "ContentEditable"] },

  { title: "How Twilio Handles Millions of API Calls", description: "Twilio's API infrastructure. Rate limiting, webhook delivery, and ensuring reliability for communications APIs.", url: "https://www.twilio.com/blog", type: "case-study", category: "backend", source: "Twilio", tags: ["API", "Communications", "Webhooks"] },
  { title: "How Plaid Connects to 12K+ Financial Institutions", description: "Plaid's banking integration platform. Screen scraping, API integrations, OAuth, and handling sensitive financial data.", url: "https://plaid.com/blog/", type: "case-study", category: "backend", source: "Plaid", tags: ["Banking", "Integration", "OAuth"] },

  { title: "How Databricks Processes Petabyte-Scale Data", description: "Databricks' Spark optimization. Photon engine, adaptive query execution, and processing analytics at petabyte scale.", url: "https://www.databricks.com/blog", type: "case-study", category: "data-science", source: "Databricks", tags: ["Spark", "Photon", "Petabyte"] },
  { title: "How Strava Uses Data Science for Athletes", description: "Strava's data science applications. Segment detection, route recommendation, and training effect analysis for athletes.", url: "https://medium.com/strava-engineering", type: "case-study", category: "data-science", source: "Strava", tags: ["Athletes", "Segments", "Training"] },

  /* ==================  Final Push — Over 1000  ================== */
  { title: "Mistral AI — Open Source LLMs", description: "High-performance open-source language models. Mistral 7B, Mixtral MoE, and efficient inference for production use.", url: "https://github.com/mistralai/mistral-src", type: "github", category: "ai-ml", source: "Mistral AI", tags: ["Open Source", "LLM", "Efficient"] },
  { title: "Llama 3 — Meta's Open LLM", description: "Meta's latest open-source large language model. 8B and 70B variants, extended context, and competitive performance.", url: "https://github.com/meta-llama/llama3", type: "github", category: "ai-ml", source: "Meta AI", tags: ["Llama", "Open Source", "Foundation"] },
  { title: "Gemma — Google's Open Models", description: "Google's open models for responsible AI. Lightweight deployment, instruction tuning, and safety-focused design.", url: "https://github.com/google/gemma_pytorch", type: "github", category: "ai-ml", source: "Google", tags: ["Gemma", "Open", "Safety"] },
  { title: "How Spotify Builds ML Features", description: "Spotify's ML feature platform. Feature engineering, real-time serving, and A/B testing ML models in production.", url: "https://engineering.atspotify.com/", type: "case-study", category: "ai-ml", source: "Spotify", tags: ["Features", "Real-Time", "A/B Testing"] },
  { title: "Webpack — Module Bundler", description: "The most established JavaScript bundler. Code splitting, tree shaking, hot module replacement, and plugin ecosystem.", url: "https://github.com/webpack/webpack", type: "github", category: "frontend", source: "Webpack", tags: ["Bundler", "Code Splitting", "Plugins"] },
  { title: "esbuild — Ultra-Fast Bundler", description: "JavaScript bundler written in Go. 10-100x faster than alternatives, tree shaking, and source maps.", url: "https://github.com/evanw/esbuild", type: "github", category: "frontend", source: "Evan Wallace", tags: ["Bundler", "Go", "Ultra-Fast"] },
  { title: "Turbopack — Successor to Webpack", description: "Vercel's Rust-based successor to Webpack. Incremental computation, lazy compilation, and optimized for Next.js.", url: "https://github.com/vercel/turbo", type: "github", category: "frontend", source: "Vercel", tags: ["Bundler", "Rust", "Incremental"] },
  { title: "How Vercel Built Turbopack", description: "The architecture behind Turbopack. Incremental compilation, persistent caching, and why Rust was chosen over JavaScript.", url: "https://vercel.com/blog", type: "case-study", category: "frontend", source: "Vercel", tags: ["Turbopack", "Compilation", "Architecture"] },
  { title: "Hono — Ultrafast Web Framework", description: "Small, fast, and works on any JavaScript runtime. Built-in middleware, TypeScript support, and 302+ runtime support.", url: "https://github.com/honojs/hono", type: "github", category: "backend", source: "Hono", tags: ["Ultra-Fast", "Multi-Runtime", "TypeScript"] },
  { title: "Elysia — Ergonomic Bun Framework", description: "TypeScript framework built for Bun. End-to-end type safety, unified plugins, and ahead-of-time compilation.", url: "https://github.com/elysiajs/elysia", type: "github", category: "backend", source: "Elysia", tags: ["Bun", "Type Safety", "Fast"] },
  { title: "How Roblox Handles 70M+ Daily Users", description: "Roblox's infrastructure for real-time gaming. Physics simulation, user-generated content, and global edge deployment.", url: "https://blog.roblox.com/", type: "case-study", category: "system-design", source: "Roblox", tags: ["Gaming", "Real-Time", "UGC"] },
  { title: "How Figma Handles 1M+ Concurrent Editors", description: "Figma's architecture for massive concurrency. Operational transformation, conflict resolution, and WebSocket management.", url: "https://www.figma.com/blog/", type: "case-study", category: "system-design", source: "Figma", tags: ["Concurrency", "OT", "WebSocket"] },
  { title: "Valkey — Redis Fork by Linux Foundation", description: "Community-driven fork of Redis. Open-source, compatible with Redis clients, and governed by Linux Foundation.", url: "https://github.com/valkey-io/valkey", type: "github", category: "databases", source: "Linux Foundation", tags: ["Redis Fork", "Open Source", "Compatible"] },
  { title: "Dragonfly — Modern In-Memory Datastore", description: "Drop-in Redis replacement. Multi-threaded, memory-efficient, and 25x faster than Redis for certain workloads.", url: "https://github.com/dragonflydb/dragonfly", type: "github", category: "databases", source: "Dragonfly", tags: ["Redis Alternative", "Multi-Thread", "Fast"] },
  { title: "Garnet — Microsoft's Cache Store", description: "Microsoft's high-performance cache store. RESP protocol compatible, faster than Redis, and supports cluster mode.", url: "https://github.com/microsoft/garnet", type: "github", category: "databases", source: "Microsoft", tags: ["Cache", "RESP", "High-Performance"] },
  { title: "SQLMesh — Data Transformation Framework", description: "Data transformation framework with built-in scheduler. SQL-based transformations, automatic lineage, and plan evaluation.", url: "https://github.com/TobikoData/sqlmesh", type: "github", category: "data-science", source: "Tobiko Data", tags: ["Transform", "Lineage", "Scheduler"] },
  { title: "Great Expectations — Data Quality", description: "Data quality testing framework. Expectations as code, data documentation, and integration with data pipelines.", url: "https://github.com/great-expectations/great_expectations", type: "github", category: "data-science", source: "Great Expectations", tags: ["Quality", "Testing", "Expectations"] },
  { title: "Metabase — Business Intelligence", description: "Simple, open-source analytics and BI platform. Ask questions about data, create dashboards, and share insights.", url: "https://github.com/metabase/metabase", type: "github", category: "data-science", source: "Metabase", tags: ["BI", "Dashboards", "Analytics"] },
  { title: "How Canva Uses ML for Design Recommendations", description: "Canva's ML-powered design suggestions. Template recommendations, color palettes, and element placement optimization.", url: "https://www.canva.dev/blog/engineering/", type: "case-study", category: "ai-ml", source: "Canva", tags: ["Design", "Recommendations", "ML"] },  
  { title: "How Wise Handles Multi-Currency Transfers", description: "Wise's payment infrastructure. Real-time exchange rates, compliance across 80+ countries, and batch payment processing.", url: "https://www.wise.jobs/", type: "case-study", category: "backend", source: "Wise", tags: ["Payments", "Multi-Currency", "Compliance"] },
  { title: "How Revolut Built Their Banking Platform", description: "Revolut's modern banking infrastructure. Microservices, event sourcing, and supporting 35M+ customers across 38 countries.", url: "https://blog.revolut.com/", type: "case-study", category: "system-design", source: "Revolut", tags: ["Banking", "Microservices", "Event Sourcing"] },
  { title: "OpenAPI Specification — API Design", description: "Standard for describing RESTful APIs. Schema definitions, request/response examples, and code generation tools.", url: "https://swagger.io/specification/", type: "ebook", category: "backend", source: "SmartBear", tags: ["OpenAPI", "REST", "Schema"] },
];





/* ------------------------------------------------------------------ */
/*  Programmatic resource generation for scale                         */
/* ------------------------------------------------------------------ */

const GENERATED_POOL: { category: Resource["category"]; type: Resource["type"]; entries: { title: string; description: string; url: string; source: string; tags: string[] }[] }[] = [
  {
    category: "ai-ml", type: "course",
    entries: [
      { title: "CMU 11-785 — Introduction to Deep Learning", description: "Carnegie Mellon's hands-on deep learning course. Covers MLPs, CNNs, RNNs, attention, sequence-to-sequence models, and GANs with PyTorch labs.", url: "https://deeplearning.cs.cmu.edu/", source: "CMU", tags: ["Deep Learning", "PyTorch", "Hands-on"] },
      { title: "MIT 6.S978 — Privacy and Machine Learning", description: "MIT course on privacy-preserving ML. Differential privacy, federated learning, secure computation, and privacy attacks on ML models.", url: "https://opacus.ai/", source: "MIT", tags: ["Privacy", "Differential Privacy", "Federated"] },
      { title: "DeepLearning.AI — Generative AI with LLMs", description: "Course on building generative AI applications. Covers transformer training, fine-tuning, RLHF, and deploying LLMs in production.", url: "https://www.deeplearning.ai/courses/generative-ai-with-llms/", source: "DeepLearning.AI", tags: ["GenAI", "LLMs", "Fine-Tuning"] },
      { title: "Google Cloud ML Engineer Certification", description: "Professional certification for ML engineering on GCP. Covers Vertex AI, BigQuery ML, model deployment, and MLOps best practices.", url: "https://cloud.google.com/learn/certification/machine-learning-engineer", source: "Google Cloud", tags: ["Certification", "GCP", "MLOps"] },
      { title: "DataCamp — Machine Learning Scientist", description: "Career track covering supervised learning, deep learning with Keras, NLP, image processing, and model deployment with Python.", url: "https://www.datacamp.com/tracks/machine-learning-scientist-with-python", source: "DataCamp", tags: ["Career Track", "Python", "Comprehensive"] },
    ]
  },
  {
    category: "ai-ml", type: "github",
    entries: [
      { title: "TensorFlow — End-to-End ML Platform", description: "Google's comprehensive ML platform. Production-ready models, TF Lite for mobile, TF.js for browser, TF Serving for deployment.", url: "https://github.com/tensorflow/tensorflow", source: "Google", tags: ["TensorFlow", "Production", "Multi-Platform"] },
      { title: "Keras — Deep Learning API", description: "High-level neural networks API. Simple, flexible, and powerful with TensorFlow, JAX, or PyTorch backends.", url: "https://github.com/keras-team/keras", source: "Keras", tags: ["High-Level", "Simple", "Multi-Backend"] },
      { title: "spaCy — Industrial NLP", description: "Production-ready NLP library. Named entity recognition, POS tagging, dependency parsing, and custom pipeline components.", url: "https://github.com/explosion/spaCy", source: "Explosion", tags: ["NLP", "Production", "Pipelines"] },
      { title: "Ray — Distributed ML Framework", description: "Universal framework for distributed computing. Covers Ray Tune, Ray Serve, Ray Train for scaling ML workloads.", url: "https://github.com/ray-project/ray", source: "Anyscale", tags: ["Distributed", "Scaling", "Training"] },
      { title: "DVC — Data Version Control", description: "Version control for ML projects. Track data, models, and experiments alongside code with Git integration.", url: "https://github.com/iterative/dvc", source: "Iterative", tags: ["Versioning", "Data", "Experiments"] },
      { title: "Optuna — Hyperparameter Optimization", description: "Automatic hyperparameter optimization framework. Define-by-run API, pruning, distributed optimization, and visualization.", url: "https://github.com/optuna/optuna", source: "Preferred Networks", tags: ["Hyperparameters", "Optimization", "AutoML"] },
      { title: "Sentence Transformers — Text Embeddings", description: "Python framework for computing dense vector representations of text. Powers semantic search, clustering, and paraphrase mining.", url: "https://github.com/UKPLab/sentence-transformers", source: "UKP Lab", tags: ["Embeddings", "Semantic Search", "NLP"] },
      { title: "Ultralytics HUB — No-Code Vision AI", description: "Train, deploy, and manage computer vision models without code. Auto-annotation, model training, and one-click deployment.", url: "https://github.com/ultralytics/hub", source: "Ultralytics", tags: ["No-Code", "Vision", "Deployment"] },
      { title: "Mojo — Programming Language for AI", description: "New programming language combining Python's usability with C++'s performance. Designed for AI hardware with SIMD and parallel computing.", url: "https://github.com/modularml/mojo", source: "Modular", tags: ["Language", "Performance", "Hardware"] },
      { title: "Instructor — Structured LLM Outputs", description: "Python library for getting structured outputs from LLMs. Pydantic-based validation, retry logic, and streaming for reliable extraction.", url: "https://github.com/jxnl/instructor", source: "Jason Liu", tags: ["Structured", "Pydantic", "Extraction"] },
    ]
  },
  {
    category: "ai-ml", type: "case-study",
    entries: [
      { title: "How Pinterest Uses ML for Content Moderation", description: "Pinterest's ML-powered content moderation pipeline. Covers image classification, text analysis, and handling billions of pins with policies.", url: "https://medium.com/pinterest-engineering/", source: "Pinterest", tags: ["Moderation", "Classification", "Policy"] },
      { title: "How Grammarly Uses NLP for Writing Assistance", description: "Grammarly's NLP models for grammar correction, tone detection, and writing suggestions. Covers transformer fine-tuning and real-time inference.", url: "https://www.grammarly.com/blog/engineering/", source: "Grammarly", tags: ["NLP", "Grammar", "Writing"] },
      { title: "How DeepMind Solved Protein Folding", description: "AlphaFold2's approach to solving the protein structure prediction problem. Covers attention-based architecture and its impact on biology.", url: "https://deepmind.google/discover/blog/", source: "DeepMind", tags: ["Biology", "AlphaFold", "Structure"] },
      { title: "How OpenAI Scales Training Infrastructure", description: "OpenAI's distributed training infrastructure for GPT models. Covers data parallelism, model parallelism, and custom hardware coordination.", url: "https://openai.com/research/", source: "OpenAI", tags: ["Training Infra", "Parallelism", "Scale"] },
      { title: "How Meta Built Their Recommendation System", description: "Meta's deep learning recommendation model (DLRM). Covers embedding tables, interaction networks, and serving recommendations at Facebook scale.", url: "https://engineering.fb.com/", source: "Meta", tags: ["Recommendations", "DLRM", "Embeddings"] },
    ]
  },
  {
    category: "ai-ml", type: "ebook",
    entries: [
      { title: "Mathematics for Machine Learning — Free Book", description: "Complete mathematical foundations for ML. Linear algebra, probability, optimization, and how they connect to ML algorithms.", url: "https://mml-book.github.io/", source: "Cambridge", tags: ["Mathematics", "Linear Algebra", "Optimization"] },
      { title: "Probabilistic ML — Kevin Murphy", description: "Comprehensive textbook on probabilistic approaches to ML. Bayesian methods, graphical models, deep generative models, and causal inference.", url: "https://probml.github.io/pml-book/", source: "Kevin Murphy", tags: ["Bayesian", "Probabilistic", "Graphical Models"] },
      { title: "Neural Networks and Deep Learning — Free Book", description: "Michael Nielsen's free online book. Intuitive introduction to neural networks, backpropagation, and deep learning fundamentals.", url: "http://neuralnetworksanddeeplearning.com/", source: "Michael Nielsen", tags: ["Fundamentals", "Backprop", "Intuitive"] },
      { title: "Speech and Language Processing — Jurafsky", description: "Comprehensive NLP textbook by Dan Jurafsky and James Martin. Covers regular expressions to transformers, with exercises and implementations.", url: "https://web.stanford.edu/~jurafsky/slp3/", source: "Stanford", tags: ["NLP Textbook", "Comprehensive", "Exercises"] },
      { title: "Pattern Recognition and Machine Learning — Bishop", description: "Christopher Bishop's classic ML textbook. Bayesian perspective on pattern recognition, neural networks, and kernel methods.", url: "https://www.microsoft.com/en-us/research/publication/pattern-recognition-machine-learning/", source: "Microsoft Research", tags: ["Classic", "Bayesian", "Pattern Recognition"] },
    ]
  },
  {
    category: "frontend", type: "github",
    entries: [
      { title: "Qwik — Instant-Loading Web Framework", description: "Framework designed for instant loading. Resumability instead of hydration, fine-grained lazy loading, and zero JS on page load.", url: "https://github.com/QwikDev/qwik", source: "Builder.io", tags: ["Resumability", "Instant", "No Hydration"] },
      { title: "Tailwind CSS — Utility-First CSS", description: "A utility-first CSS framework for rapidly building custom designs. JIT compiler, responsive design, and component extraction patterns.", url: "https://github.com/tailwindlabs/tailwindcss", source: "Tailwind Labs", tags: ["CSS", "Utility-First", "JIT"] },
      { title: "Vitest — Blazing Fast Unit Testing", description: "Next-generation testing framework powered by Vite. Jest-compatible API, watch mode, coverage, and TypeScript support out of the box.", url: "https://github.com/vitest-dev/vitest", source: "Vitest", tags: ["Testing", "Vite", "Fast"] },
      { title: "Panda CSS — CSS-in-JS with Build-Time", description: "Type-safe CSS-in-JS with zero runtime. Static extraction at build time, design tokens, and atomic CSS generation.", url: "https://github.com/chakra-ui/panda", source: "Chakra", tags: ["CSS-in-JS", "Zero Runtime", "Tokens"] },
      { title: "TanStack Router — Type-Safe Routing", description: "Fully type-safe router for React. Search params validation, route loaders, file-based routing, and first-class caching.", url: "https://github.com/TanStack/router", source: "TanStack", tags: ["Routing", "Type-Safe", "React"] },
      { title: "Rehype / Remark — Markdown Processing", description: "Ecosystem of plugins for processing markdown to HTML. Syntax highlighting, math rendering, GFM support, and custom transforms.", url: "https://github.com/remarkjs/remark", source: "Unified.js", tags: ["Markdown", "Processing", "Plugins"] },
      { title: "Lottie Web — After Effects Animations", description: "Render After Effects animations natively on web and mobile. JSON-based animation format with small file sizes and full interactivity.", url: "https://github.com/airbnb/lottie-web", source: "Airbnb", tags: ["Animation", "After Effects", "JSON"] },
      { title: "GSAP — Professional Animation", description: "Professional-grade animation library. Timeline-based sequencing, ScrollTrigger for scroll animations, and complex motion paths.", url: "https://gsap.com/", source: "GreenSock", tags: ["Animation", "ScrollTrigger", "Timeline"] },
      { title: "Sentry — Error Monitoring for Frontend", description: "Application monitoring platform. Error tracking, performance monitoring, session replay, and release tracking for web applications.", url: "https://github.com/getsentry/sentry-javascript", source: "Sentry", tags: ["Errors", "Monitoring", "Replay"] },
      { title: "Ark UI — Headless Component Library", description: "Framework-agnostic headless UI components. State machines for predictable behavior, accessibility built-in, and works with React, Vue, Solid.", url: "https://github.com/chakra-ui/ark", source: "Chakra", tags: ["Headless", "State Machine", "Agnostic"] },
    ]
  },
  {
    category: "frontend", type: "course",
    entries: [
      { title: "Epic React — Kent C. Dodds", description: "Advanced React workshop series. Covers hooks patterns, advanced patterns, performance, testing, and building production apps.", url: "https://epicreact.dev/", source: "Kent C. Dodds", tags: ["Advanced", "Patterns", "Workshop"] },
      { title: "Joy of React — Josh Comeau", description: "Interactive React course with visual explanations. Covers mental models, hooks, performance, animations, and server components.", url: "https://www.joyofreact.com/", source: "Josh Comeau", tags: ["Interactive", "Visual", "Mental Models"] },
      { title: "Total TypeScript — Matt Pocock", description: "Comprehensive TypeScript courses from basics to advanced. Generics, type transformations, React with TypeScript, and advanced patterns.", url: "https://www.totaltypescript.com/", source: "Matt Pocock", tags: ["TypeScript", "Generics", "Advanced"] },
      { title: "Three.js Journey — 3D Web Course", description: "The ultimate Three.js course. 90+ hours covering shaders, particles, physics, post-processing, and building immersive 3D experiences.", url: "https://threejs-journey.com/", source: "Bruno Simon", tags: ["3D", "Shaders", "WebGL"] },
      { title: "Frontend Performance Masterclass", description: "Deep dive into web performance. Core Web Vitals, resource loading, rendering optimization, and building fast-loading applications.", url: "https://frontendmasters.com/courses/web-performance/", source: "Frontend Masters", tags: ["Performance", "CWV", "Optimization"] },
    ]
  },
  {
    category: "frontend", type: "case-study",
    entries: [
      { title: "How Discord Built Their Message UI", description: "Discord's approach to rendering millions of messages efficiently. Virtual scrolling, markdown rendering, and emoji handling at scale.", url: "https://discord.com/blog/", source: "Discord", tags: ["Virtual Scroll", "Chat UI", "Performance"] },
      { title: "How Spotify Built Their Web Player", description: "Spotify's web player architecture. Audio streaming, offline support, cross-tab synchronization, and desktop-quality experience in the browser.", url: "https://engineering.atspotify.com/", source: "Spotify", tags: ["Audio", "Streaming", "Web Player"] },
      { title: "How Vercel Built the Next.js App Router", description: "Architecture decisions behind Next.js App Router. Server components, streaming, parallel routes, and incremental static regeneration.", url: "https://nextjs.org/blog", source: "Vercel", tags: ["App Router", "RSC", "Streaming"] },
      { title: "How Excalidraw Built a Collaborative Whiteboard", description: "Excalidraw's architecture for real-time collaborative drawing. Canvas rendering, CRDT-based sync, and end-to-end encryption.", url: "https://blog.excalidraw.com/", source: "Excalidraw", tags: ["Canvas", "CRDT", "Collaborative"] },
      { title: "How Cal.com Built an Open-Source Scheduling Tool", description: "Cal.com's frontend architecture. Timezone handling, calendar integration, embed widgets, and dynamic form building.", url: "https://cal.com/blog", source: "Cal.com", tags: ["Scheduling", "Timezone", "Open Source"] },
    ]
  },
  {
    category: "backend", type: "github",
    entries: [
      { title: "Encore — Backend Development Platform", description: "Type-safe backend framework with infrastructure from code. Automatic cloud provisioning, distributed tracing, and API documentation.", url: "https://github.com/encoredev/encore", source: "Encore", tags: ["Platform", "Infrastructure", "Type-Safe"] },
      { title: "Elysia — Bun Web Framework", description: "TypeScript web framework built for Bun. End-to-end type safety, ahead-of-time compilation, and OpenAPI documentation generation.", url: "https://github.com/elysiajs/elysia", source: "Elysia", tags: ["Bun", "TypeScript", "Fast"] },
      { title: "Fiber — Express-Inspired Go Framework", description: "Fast, express-inspired web framework for Go. Zero memory allocation, middleware support, and WebSocket handling.", url: "https://github.com/gofiber/fiber", source: "Fiber", tags: ["Go", "Express", "Performance"] },
      { title: "Gin — HTTP Web Framework for Go", description: "The most popular Go web framework. Middleware, JSON validation, error management, and routing with radix tree.", url: "https://github.com/gin-gonic/gin", source: "Gin", tags: ["Go", "HTTP", "Middleware"] },
      { title: "Django — Python Web Framework", description: "The web framework for perfectionists with deadlines. ORM, admin panel, authentication, and batteries-included approach.", url: "https://github.com/django/django", source: "Django", tags: ["Python", "ORM", "Admin"] },
      { title: "Celery — Distributed Task Queue", description: "Async task queue for Python. Schedule tasks, chain workflows, monitor workers, and process millions of tasks per day.", url: "https://github.com/celery/celery", source: "Celery", tags: ["Task Queue", "Async", "Workers"] },
      { title: "Bull — Node.js Job Queue", description: "Premium queue for Node.js. Redis-backed, rate limiting, job scheduling, repeatable jobs, and robust error handling.", url: "https://github.com/OptimalBits/bull", source: "OptimalBits", tags: ["Queue", "Redis", "Jobs"] },
      { title: "Kong — API Gateway", description: "Cloud-native API gateway. Rate limiting, authentication, logging, load balancing, and plugin ecosystem with declarative configuration.", url: "https://github.com/Kong/kong", source: "Kong", tags: ["API Gateway", "Plugins", "Cloud Native"] },
      { title: "Meilisearch — Lightning Fast Search", description: "Open-source search engine. Typo tolerance, faceted search, filtering, sorting, and search-as-you-type with sub-50ms responses.", url: "https://github.com/meilisearch/meilisearch", source: "Meilisearch", tags: ["Search", "Fast", "Full-Text"] },
      { title: "MinIO — S3-Compatible Object Storage", description: "High-performance object storage. S3-compatible API, erasure coding, bitrot protection, and Kubernetes-native deployment.", url: "https://github.com/minio/minio", source: "MinIO", tags: ["Object Storage", "S3", "High-Performance"] },
    ]
  },
  {
    category: "backend", type: "case-study",
    entries: [
      { title: "How Dropbox Migrated from Python 2 to 3", description: "Dropbox's multi-year Python 2 to 3 migration. Type checking with mypy, automated refactoring, and testing 4M lines of Python code.", url: "https://dropbox.tech/", source: "Dropbox", tags: ["Migration", "Python", "mypy"] },
      { title: "How Netflix Built Their API Gateway", description: "Netflix's Zuul API gateway handling billions of requests. Covers dynamic routing, canary testing, and multi-region traffic management.", url: "https://netflixtechblog.com/", source: "Netflix", tags: ["API Gateway", "Zuul", "Routing"] },
      { title: "How Uber Manages Database Migrations", description: "Uber's approach to online schema changes across thousands of MySQL instances. Covers gh-ost, schema versioning, and rollback strategies.", url: "https://www.uber.com/blog/", source: "Uber", tags: ["Migrations", "MySQL", "gh-ost"] },
      { title: "How Slack Built Their Real-Time Message System", description: "Slack's message delivery infrastructure. WebSocket connections, message ordering, read state tracking, and offline message queuing.", url: "https://slack.engineering/", source: "Slack", tags: ["Real-Time", "WebSocket", "Messaging"] },
      { title: "How Twitch Handles Millions of Concurrent Viewers", description: "Twitch's video delivery and chat infrastructure. Covers HLS streaming, chat scaling, bits economy, and real-time interaction features.", url: "https://blog.twitch.tv/en/tags/engineering/", source: "Twitch", tags: ["Streaming", "Chat", "Concurrent"] },
    ]
  },
  {
    category: "backend", type: "ebook",
    entries: [
      { title: "Designing Distributed Systems — Burns", description: "Patterns and paradigms for scalable, reliable services. Covers sidecar, ambassador, adapter, and work queue patterns.", url: "https://azure.microsoft.com/en-us/resources/designing-distributed-systems/", source: "Microsoft", tags: ["Patterns", "Distributed", "Containers"] },
      { title: "Release It! — Michael Nygard", description: "Design and deploy production-ready software. Circuit breakers, bulkheads, timeouts, and patterns for building resilient systems.", url: "https://pragprog.com/titles/mnee2/release-it-second-edition/", source: "Pragmatic", tags: ["Resilience", "Production", "Patterns"] },
      { title: "Web Scalability for Startup Engineers", description: "Practical guide to scaling web applications. Caching, queuing, data partitioning, and making architecture decisions under constraints.", url: "https://www.amazon.com/Scalability-Startup-Engineers-Artur-Ejsmont/dp/0071843655", source: "McGraw Hill", tags: ["Scalability", "Startups", "Architecture"] },
      { title: "API Design Patterns — JJ Geewax", description: "Standard patterns for designing clean, consistent APIs. Resource-oriented design, long-running operations, and API evolution.", url: "https://www.manning.com/books/api-design-patterns", source: "Manning", tags: ["API", "Patterns", "Design"] },
      { title: "Fundamentals of Software Architecture", description: "Mark Richards and Neal Ford's guide to software architecture. Architecture styles, -ilities, decision making, and soft skills.", url: "https://www.oreilly.com/library/view/fundamentals-of-software/9781492043447/", source: "O'Reilly", tags: ["Architecture", "Styles", "Decision Making"] },
    ]
  },
  {
    category: "devops", type: "github",
    entries: [
      { title: "Backstage — Developer Portal Platform", description: "Spotify's open platform for building developer portals. Service catalog, software templates, TechDocs, and plugin architecture.", url: "https://github.com/backstage/backstage", source: "Spotify", tags: ["Dev Portal", "Catalog", "DX"] },
      { title: "Pulumi — IaC in General Purpose Languages", description: "Define cloud infrastructure in TypeScript, Python, Go, or C#. Testing, componentization, and state management.", url: "https://github.com/pulumi/pulumi", source: "Pulumi", tags: ["IaC", "Programming", "Multi-Language"] },
      { title: "Earthly — Repeatable Build Tool", description: "Like Docker and Make had a baby. Containerized, repeatable builds with caching. Works with any CI/CD system.", url: "https://github.com/earthly/earthly", source: "Earthly", tags: ["Builds", "Containers", "Cache"] },
      { title: "Argo Workflows — Kubernetes Workflow Engine", description: "Container-native workflow engine for Kubernetes. DAG-based workflows, retry logic, and integration with CI/CD pipelines.", url: "https://github.com/argoproj/argo-workflows", source: "Argo", tags: ["Workflows", "DAG", "Kubernetes"] },
      { title: "Linkerd — Lightweight Service Mesh", description: "Ultralight Kubernetes service mesh. Automatic mTLS, observability, reliability, and traffic management with minimal resource overhead.", url: "https://github.com/linkerd/linkerd2", source: "Buoyant", tags: ["Service Mesh", "Lightweight", "mTLS"] },
    ]
  },
  {
    category: "devops", type: "case-study",
    entries: [
      { title: "How Uber Moved to Kubernetes", description: "Uber's migration to Kubernetes for compute orchestration. Covers multi-region deployment, stateful workloads, and cost optimization.", url: "https://www.uber.com/blog/", source: "Uber", tags: ["Kubernetes", "Migration", "Multi-Region"] },
      { title: "How Shopify Manages 300K+ Stores at Scale", description: "Shopify's multi-tenant infrastructure. Pod-based architecture, zero-downtime deployments, and handling BFCM traffic spikes.", url: "https://shopify.engineering/", source: "Shopify", tags: ["Multi-Tenant", "Scale", "BFCM"] },
      { title: "How DoorDash Built Their ML Platform", description: "DoorDash's ML platform for model training, serving, and monitoring. Covers feature stores, model registry, and A/B testing.", url: "https://doordash.engineering/", source: "DoorDash", tags: ["ML Platform", "Model Serving", "A/B Testing"] },
      { title: "How Google Manages Borg at Scale", description: "Google's cluster management system handling billions of containers. Covers scheduling, resource isolation, and efficiency at massive scale.", url: "https://research.google/pubs/pub43438/", source: "Google", tags: ["Borg", "Scheduling", "Containers"] },
      { title: "How Meta Runs Their Container Platform", description: "Meta's container orchestration serving millions of containers. Covers resource management, scheduling, and fleet management.", url: "https://engineering.fb.com/", source: "Meta", tags: ["Containers", "Fleet", "Scheduling"] },
    ]
  },
  {
    category: "databases", type: "github",
    entries: [
      { title: "Prisma — Next-Gen ORM", description: "Modern database toolkit for TypeScript and Node.js. Schema-first, type-safe queries, migrations, and Prisma Studio for data browsing.", url: "https://github.com/prisma/prisma", source: "Prisma", tags: ["ORM", "TypeScript", "Schema-First"] },
      { title: "SurrealDB — Multi-Model Database", description: "Multi-model database for web, mobile, serverless, and backend. SQL-like syntax with graph, document, and key-value capabilities.", url: "https://github.com/surrealdb/surrealdb", source: "SurrealDB", tags: ["Multi-Model", "Graph", "Document"] },
      { title: "EdgeDB — Post-Relational Database", description: "Next-gen database with a built-in query language (EdgeQL). Type system, computed properties, and seamless migration system.", url: "https://github.com/edgedb/edgedb", source: "EdgeDB", tags: ["Post-Relational", "EdgeQL", "Type System"] },
      { title: "RisingWave — Streaming Database", description: "Distributed SQL database for stream processing. Materialize views from streaming data with PostgreSQL compatibility.", url: "https://github.com/risingwavelabs/risingwave", source: "RisingWave", tags: ["Streaming", "Materialized Views", "SQL"] },
      { title: "Chromia — Relational Blockchain DB", description: "A relational blockchain database that enables decentralized applications with relational data models and SQL-like queries.", url: "https://github.com/chromaway/postchain", source: "Chromia", tags: ["Blockchain", "Relational", "Decentralized"] },
    ]
  },
  {
    category: "databases", type: "case-study",
    entries: [
      { title: "How Uber Built Their Database Platform", description: "Uber's database platform supporting dozens of database technologies. Covers provisioning, monitoring, and automated remediation.", url: "https://www.uber.com/blog/", source: "Uber", tags: ["Platform", "Multi-DB", "Automation"] },
      { title: "How Coinbase Scales Their Database Layer", description: "Coinbase's approach to database reliability during crypto trading spikes. Covers connection pooling, read replicas, and failover.", url: "https://www.coinbase.com/blog/", source: "Coinbase", tags: ["Crypto", "Reliability", "Spikes"] },
      { title: "How LinkedIn Migrated to Apache Kafka", description: "LinkedIn's journey building and adopting Kafka for event streaming. Covers log-centric architecture and replacing legacy messaging.", url: "https://engineering.linkedin.com/blog", source: "LinkedIn", tags: ["Kafka", "Event", "Migration"] },
      { title: "How Shopify Upgraded MySQL at Scale", description: "Shopify's approach to MySQL major version upgrades across thousands of instances. Covers testing, rolling upgrades, and validation.", url: "https://shopify.engineering/", source: "Shopify", tags: ["MySQL", "Upgrade", "Rolling"] },
      { title: "How Datadog Built Their Custom TSDB", description: "Datadog's custom time-series database built for metrics. Covers compression, indexing, and serving millions of queries per second.", url: "https://www.datadoghq.com/blog/", source: "Datadog", tags: ["TSDB", "Metrics", "Custom"] },
    ]
  },
  {
    category: "system-design", type: "course",
    entries: [
      { title: "Neetcode System Design — Video Course", description: "Practical system design interviews course. Covers 25+ real-world system designs with visual explanations and trade-off analysis.", url: "https://neetcode.io/courses/system-design-interview", source: "Neetcode", tags: ["Interview", "Visual", "Trade-offs"] },
      { title: "Educative — System Design for Interviews", description: "Interactive text-based system design course. Covers fundamental concepts and 15+ real-world system design problems.", url: "https://www.educative.io/courses/grokking-modern-system-design-interview-for-engineers-managers", source: "Educative", tags: ["Interactive", "Problems", "Concepts"] },
      { title: "MIT 6.006 — Intro to Algorithms", description: "MIT's foundational algorithms course. Sorting, graph algorithms, dynamic programming, and computational complexity.", url: "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/", source: "MIT", tags: ["Algorithms", "Complexity", "Foundations"] },
      { title: "Stanford CS 161 — Design & Analysis of Algorithms", description: "Stanford's algorithms course. Divide and conquer, greedy algorithms, dynamic programming, graph algorithms, and NP-completeness.", url: "https://stanford.edu/class/cs161/", source: "Stanford", tags: ["Algorithms", "Analysis", "NP"] },
    ]
  },
  {
    category: "system-design", type: "ebook",
    entries: [
      { title: "System Design Interview Vol 1 — Alex Xu", description: "Step-by-step framework for system design interviews. Covers rate limiter, URL shortener, chat system, and search autocomplete.", url: "https://www.amazon.com/System-Design-Interview-insiders-Second/dp/B08CMF2CQF", source: "ByteByteGo", tags: ["Interview", "Framework", "Step-by-Step"] },
      { title: "System Design Interview Vol 2 — Alex Xu", description: "Advanced system design problems. Covers proximity service, nearby friends, Google Maps, payment system, and distributed email.", url: "https://www.amazon.com/System-Design-Interview-Insiders-Guide/dp/1736049119", source: "ByteByteGo", tags: ["Advanced", "Payment", "Maps"] },
      { title: "Database Internals — Alex Petrov", description: "Deep dive into database storage engines. Covers B-Trees, LSM Trees, buffer management, page caching, and distributed storage.", url: "https://www.databass.dev/", source: "O'Reilly", tags: ["Storage Engines", "B-Trees", "LSM"] },
      { title: "Understanding Distributed Systems", description: "Practical guide to building distributed systems. Communication, coordination, scalability, and resiliency patterns with real examples.", url: "https://understandingdistributed.systems/", source: "Roberto Vitillo", tags: ["Distributed", "Practical", "Patterns"] },
    ]
  },
  {
    category: "security", type: "github",
    entries: [
      { title: "GoSec — Go Security Checker", description: "Security scanner for Go code. Detects hardcoded credentials, SQL injection, command injection, and insecure random number generation.", url: "https://github.com/securego/gosec", source: "SecureGo", tags: ["Go", "Scanner", "Static Analysis"] },
      { title: "Semgrep — Lightweight Static Analysis", description: "Fast, customizable static analysis. Write rules in a familiar syntax to find bugs, enforce code standards, and detect vulnerabilities.", url: "https://github.com/semgrep/semgrep", source: "Semgrep", tags: ["Static Analysis", "Rules", "Custom"] },
      { title: "Age — Simple File Encryption", description: "Simple, modern, and secure file encryption tool. Small, focused, and uses strong cryptographic primitives.", url: "https://github.com/FiloSottile/age", source: "Filippo Valsorda", tags: ["Encryption", "Files", "Simple"] },
      { title: "Socket — Detect Supply Chain Attacks", description: "Detect and block supply chain attacks in npm, PyPI, and other package registries. Behavior analysis and risk scoring.", url: "https://socket.dev/", source: "Socket", tags: ["Supply Chain", "npm", "Detection"] },
    ]
  },
  {
    category: "security", type: "case-study",
    entries: [
      { title: "How GitHub Keeps Repositories Secure", description: "GitHub's security infrastructure. Secret scanning, Dependabot, code scanning, and how they protect millions of repositories.", url: "https://github.blog/security/", source: "GitHub", tags: ["Scanning", "Dependabot", "Secrets"] },
      { title: "How Datadog Secures Their Pipeline", description: "Datadog's approach to securing their CI/CD pipeline. Covers build provenance, SBOM generation, and artifact signing.", url: "https://www.datadoghq.com/blog/", source: "Datadog", tags: ["CI/CD", "SBOM", "Provenance"] },
      { title: "How Apple Implements App Transport Security", description: "Apple's ATS requirements for network security. Covers TLS configuration, certificate pinning, and exception handling.", url: "https://developer.apple.com/documentation/security", source: "Apple", tags: ["ATS", "TLS", "iOS"] },
    ]
  },
  {
    category: "data-science", type: "github",
    entries: [
      { title: "Jupyter — Interactive Computing", description: "Interactive computing platform. Notebooks, JupyterLab, JupyterHub, and extensions for data science, ML, and education.", url: "https://github.com/jupyter/jupyter", source: "Jupyter", tags: ["Notebooks", "Interactive", "Computing"] },
      { title: "Matplotlib — Python Visualization", description: "Comprehensive plotting library for Python. Line plots, histograms, scatter plots, contour plots, and custom visualizations.", url: "https://github.com/matplotlib/matplotlib", source: "Matplotlib", tags: ["Plotting", "Visualization", "Charts"] },
      { title: "Plotly — Interactive Visualizations", description: "Interactive graphing library. 3D plots, statistical charts, financial charts, and Dash for building analytical web apps.", url: "https://github.com/plotly/plotly.py", source: "Plotly", tags: ["Interactive", "3D", "Dash"] },
      { title: "Seaborn — Statistical Visualization", description: "Statistical data visualization library built on matplotlib. Distribution plots, regression plots, and multi-plot grids.", url: "https://github.com/mwaskom/seaborn", source: "Michael Waskom", tags: ["Statistics", "Distribution", "Elegant"] },
      { title: "Vaex — Out-of-Core DataFrames", description: "Lazy out-of-core DataFrames for Python. Process billion-row datasets on a laptop with memory mapping and expression system.", url: "https://github.com/vaexio/vaex", source: "Vaex", tags: ["Out-of-Core", "Billion-Row", "Lazy"] },
    ]
  },
  {
    category: "data-science", type: "course",
    entries: [
      { title: "Stanford CS 246 — Mining Massive Datasets", description: "Stanford course on algorithms for mining massive data. MapReduce, locality-sensitive hashing, recommendation systems, and graph mining.", url: "http://web.stanford.edu/class/cs246/", source: "Stanford", tags: ["Mining", "MapReduce", "LSH"] },
      { title: "Fast.ai — Practical Data Ethics", description: "Free course on ethical considerations in data science. Bias, fairness, privacy, surveillance, and disinformation.", url: "https://ethics.fast.ai/", source: "fast.ai", tags: ["Ethics", "Bias", "Fairness"] },
      { title: "DataTalksClub — ML Engineering Zoomcamp", description: "Free online course on ML engineering. Model deployment, experiment tracking, orchestration, and monitoring in production.", url: "https://github.com/DataTalksClub/mlops-zoomcamp", source: "DataTalksClub", tags: ["MLOps", "Deployment", "Free"] },
      { title: "Google Data Analytics Certificate", description: "Professional certificate covering data analytics. Spreadsheets, SQL, R, Tableau, and the complete data analytics lifecycle.", url: "https://grow.google/certificates/data-analytics/", source: "Google", tags: ["Certificate", "Analytics", "R"] },
    ]
  },
  {
    category: "sql", type: "github",
    entries: [
      { title: "SQLGlot — SQL Parser & Transpiler", description: "Python SQL parser, transpiler, and optimizer. Parse SQL dialects, transpile between databases, and optimize query plans.", url: "https://github.com/tobymao/sqlglot", source: "Toby Mao", tags: ["Parser", "Transpiler", "Optimizer"] },
      { title: "SQLPad — SQL Editor & Visualization", description: "Web-based SQL editor with visualization. Connect to multiple databases, write queries, and create charts from results.", url: "https://github.com/sqlpad/sqlpad", source: "SQLPad", tags: ["Editor", "Web", "Multi-DB"] },
      { title: "Beekeeper Studio — SQL Client", description: "Modern, friendly SQL client for MySQL, PostgreSQL, SQLite, and SQL Server. Open-source with query editing, import/export.", url: "https://github.com/beekeeper-studio/beekeeper-studio", source: "Beekeeper", tags: ["Client", "Cross-Platform", "Modern"] },
    ]
  },
  {
    category: "sql", type: "case-study",
    entries: [
      { title: "How Plaid Uses PostgreSQL for Financial Data", description: "Plaid's PostgreSQL infrastructure for processing financial transactions. Covers partitioning, indexing strategies, and data integrity.", url: "https://plaid.com/blog/", source: "Plaid", tags: ["Financial", "PostgreSQL", "Partitioning"] },
      { title: "How Square Manages SQL at Point-of-Sale Scale", description: "Square's database architecture for processing payments. Covers consistency requirements, replication, and handling payment peak times.", url: "https://developer.squareup.com/blog", source: "Square", tags: ["Payments", "Consistency", "POS"] },
      { title: "How Robinhood Handles Trading Data in SQL", description: "Robinhood's approach to real-time trading data. Event sourcing, materialized views, and low-latency queries for market data.", url: "https://robinhood.engineering/", source: "Robinhood", tags: ["Trading", "Real-Time", "Event Sourcing"] },
    ]
  },
  {
    category: "mobile", type: "github",
    entries: [
      { title: "Maui — .NET Multi-Platform App UI", description: "Microsoft's cross-platform framework. Build native apps for Android, iOS, macOS, and Windows from a single C# codebase.", url: "https://github.com/dotnet/maui", source: "Microsoft", tags: [".NET", "Cross-Platform", "C#"] },
      { title: "Realm — Mobile Database", description: "Object-oriented mobile database. Reactive architecture, offline-first, sync capabilities, and zero-copy architecture for fast reads.", url: "https://github.com/realm/realm-swift", source: "MongoDB", tags: ["Database", "Offline", "Reactive"] },
      { title: "Flipper — Mobile Debugging Platform", description: "Desktop app for debugging mobile apps. Layout inspector, network inspector, database browser, and custom plugin support.", url: "https://github.com/facebook/flipper", source: "Meta", tags: ["Debugging", "Inspector", "Plugins"] },
      { title: "Detox — E2E Testing for Mobile", description: "End-to-end testing framework for React Native and native apps. Gray box testing, synchronization, and CI/CD friendly.", url: "https://github.com/wix/Detox", source: "Wix", tags: ["E2E", "Testing", "React Native"] },
    ]
  },
  {
    category: "mobile", type: "case-study",
    entries: [
      { title: "How Pinterest Optimized Their iOS App", description: "Pinterest's iOS performance optimization. Covers image loading, collection view performance, and reducing app launch time.", url: "https://medium.com/pinterest-engineering/", source: "Pinterest", tags: ["iOS", "Images", "Launch Time"] },
      { title: "How Lyft Built Their Rider App", description: "Lyft's rider app architecture. Covers map rendering, route visualization, ETA updates, and real-time driver tracking.", url: "https://eng.lyft.com/", source: "Lyft", tags: ["Maps", "Real-Time", "Tracking"] },
      { title: "How Facebook Lite Runs on Low-End Devices", description: "Facebook Lite's optimizations for emerging markets. 2MB APK, minimal memory usage, and supporting 2G networks.", url: "https://engineering.fb.com/", source: "Meta", tags: ["Lite", "Low-End", "Emerging Markets"] },
    ]
  },
  {
    category: "cloud", type: "github",
    entries: [
      { title: "LocalStack — Local AWS Cloud Stack", description: "Fully functional local AWS cloud. Test Lambda, S3, DynamoDB, SQS, and 80+ services locally without AWS credentials.", url: "https://github.com/localstack/localstack", source: "LocalStack", tags: ["Local Dev", "AWS", "Testing"] },
      { title: "Steampipe — Query Cloud APIs with SQL", description: "Use SQL to query cloud infrastructure. 140+ plugins for AWS, Azure, GCP, GitHub, and more.", url: "https://github.com/turbot/steampipe", source: "Turbot", tags: ["SQL", "Cloud APIs", "Query"] },
      { title: "Infracost — Cloud Cost Estimates", description: "Show cost estimates for infrastructure changes in pull requests. Supports Terraform and OpenTofu.", url: "https://github.com/infracost/infracost", source: "Infracost", tags: ["Cost", "Terraform", "PRs"] },
      { title: "Coolify — Self-Hostable PaaS", description: "Open-source alternative to Netlify and Heroku. One-click deployments, automatic SSL, and database management.", url: "https://github.com/coollabsio/coolify", source: "Coolify", tags: ["Self-Host", "PaaS", "Deploy"] },
    ]
  },
  {
    category: "cloud", type: "case-study",
    entries: [
      { title: "How Slack Migrated to AWS", description: "Slack's migration from their own data centers to AWS. Covers multi-year planning, workload migration, and maintaining uptime.", url: "https://slack.engineering/", source: "Slack", tags: ["Migration", "AWS", "Planning"] },
      { title: "How Figma Uses AWS for Global Scale", description: "Figma's AWS infrastructure supporting millions of designers. Covers data replication, CDN strategy, and real-time sync.", url: "https://www.figma.com/blog/", source: "Figma", tags: ["AWS", "Global", "Real-Time"] },
      { title: "How Canva Manages Multi-Cloud Infrastructure", description: "Canva's approach to running across multiple cloud providers. Covers workload placement, cost optimization, and data sovereignty.", url: "https://www.canva.dev/blog/engineering/", source: "Canva", tags: ["Multi-Cloud", "Cost", "Sovereignty"] },
    ]
  },
  {
    category: "dart", type: "course",
    entries: [
      { title: "Flutter Apprentice — raywenderlich", description: "Comprehensive Flutter book for beginners to intermediate. Covers widgets, navigation, networking, persistence, and deployment.", url: "https://www.kodeco.com/books/flutter-apprentice", source: "Kodeco", tags: ["Book", "Comprehensive", "Beginner"] },
      { title: "Andrea Bizzotto — Flutter Tutorials", description: "Advanced Flutter tutorials and courses. Architecture patterns, Riverpod, Firebase, and production-ready app development.", url: "https://codewithandrea.com/", source: "Code With Andrea", tags: ["Advanced", "Riverpod", "Architecture"] },
      { title: "Reso Coder — Flutter Clean Architecture", description: "Flutter clean architecture tutorial series. Domain-driven design, dependency injection, and test-driven development with Flutter.", url: "https://resocoder.com/", source: "Reso Coder", tags: ["Clean Arch", "DDD", "TDD"] },
    ]
  },
  {
    category: "kotlin", type: "course",
    entries: [
      { title: "Kodein Kotlin Academy", description: "Advanced Kotlin workshops and courses. Coroutines, functional programming, multiplatform development, and best practices.", url: "https://kt.academy/", source: "Kotlin Academy", tags: ["Workshops", "Advanced", "Best Practices"] },
      { title: "Philipp Lackner — Android Development", description: "Modern Android development tutorials. Jetpack Compose, MVVM, clean architecture, dependency injection with Hilt, and Kotlin flows.", url: "https://www.youtube.com/@PhilippLackner", source: "Philipp Lackner", tags: ["Android", "Compose", "MVVM"] },
    ]
  },
  {
    category: "rust", type: "course",
    entries: [
      { title: "Comprehensive Rust — Google", description: "Google's 4-day Rust course used internally. Covers fundamentals to advanced topics including async, unsafe, and interop with C/C++.", url: "https://google.github.io/comprehensive-rust/", source: "Google", tags: ["4-Day", "Comprehensive", "Internal"] },
      { title: "Rust Atomics and Locks — Mara Bos", description: "Low-level concurrency in Rust. Atomics, locks, memory ordering, and building concurrent data structures from scratch.", url: "https://marabos.nl/atomics/", source: "O'Reilly", tags: ["Concurrency", "Atomics", "Low-Level"] },
    ]
  },
  {
    category: "rust", type: "github",
    entries: [
      { title: "Ruff — Extremely Fast Python Linter", description: "Python linter written in Rust. 10-100x faster than existing tools, replaces Flake8, isort, and pyupgrade.", url: "https://github.com/astral-sh/ruff", source: "Astral", tags: ["Python", "Linter", "Fast"] },
      { title: "Zed — High-Performance Code Editor", description: "Next-generation code editor written in Rust. GPU-accelerated rendering, built-in collaboration, and AI integration.", url: "https://github.com/zed-industries/zed", source: "Zed", tags: ["Editor", "GPU", "Collaboration"] },
      { title: "Helix — Post-Modern Text Editor", description: "Modal text editor inspired by Vim and Kakoune. Written in Rust with tree-sitter for syntax highlighting and LSP support.", url: "https://github.com/helix-editor/helix", source: "Helix", tags: ["Editor", "Modal", "Tree-Sitter"] },
      { title: "SWC — Super-Fast JavaScript Compiler", description: "Rust-based JavaScript/TypeScript compiler. 20x faster than Babel, used by Next.js, Deno, and Parcel.", url: "https://github.com/swc-project/swc", source: "SWC", tags: ["Compiler", "JavaScript", "Fast"] },
      { title: "Warp — Rust-Based Terminal", description: "Modern terminal built in Rust. GPU-rendered, AI command search, workflows, and collaborative features.", url: "https://github.com/warpdotdev/Warp", source: "Warp", tags: ["Terminal", "GPU", "Modern"] },
    ]
  },
  /* ========= Additional AI/ML — Computer Vision ========= */
  {
    category: "ai-ml", type: "github",
    entries: [
      { title: "OpenCV — Computer Vision Library", description: "The most popular computer vision library. Image processing, video analysis, object detection, and machine learning with C++ and Python APIs.", url: "https://github.com/opencv/opencv", source: "OpenCV", tags: ["Vision", "Image Processing", "Classic"] },
      { title: "Segment Anything (SAM) — Meta", description: "Meta's promptable segmentation model. Segment any object in any image with zero-shot generalization using prompts.", url: "https://github.com/facebookresearch/segment-anything", source: "Meta AI", tags: ["Segmentation", "Zero-Shot", "Foundation"] },
      { title: "MediaPipe — On-Device ML Solutions", description: "Google's framework for building multimodal ML pipelines. Hand tracking, pose estimation, face detection, and object detection on-device.", url: "https://github.com/google/mediapipe", source: "Google", tags: ["On-Device", "Pose", "Face"] },
      { title: "Roboflow — Computer Vision Tools", description: "End-to-end platform for building, training, and deploying computer vision models. Annotation, augmentation, and model deployment.", url: "https://github.com/roboflow/supervision", source: "Roboflow", tags: ["Tools", "Annotation", "Deploy"] },
      { title: "GroundingDINO — Open-Set Detection", description: "Open-set object detection with language grounding. Detect any object by describing it in natural language without specific training.", url: "https://github.com/IDEA-Research/GroundingDINO", source: "IDEA Research", tags: ["Open-Set", "Grounding", "Language"] },
      { title: "Depth Anything — Monocular Depth", description: "State-of-the-art monocular depth estimation model. Zero-shot generalization, real-time inference, and robust performance across domains.", url: "https://github.com/LiheYoung/Depth-Anything", source: "Research", tags: ["Depth", "Monocular", "Zero-Shot"] },
      { title: "CLIP — Contrastive Language-Image", description: "OpenAI's model connecting text and images. Zero-shot image classification, image search, and multimodal understanding.", url: "https://github.com/openai/CLIP", source: "OpenAI", tags: ["Multimodal", "Zero-Shot", "Embeddings"] },
      { title: "MMDetection — Object Detection Toolbox", description: "Open-source detection toolbox. 300+ pre-trained models, modular design, and support for detection, segmentation, and keypoint estimation.", url: "https://github.com/open-mmlab/mmdetection", source: "OpenMMLab", tags: ["Detection", "Toolbox", "Pretrained"] },
    ]
  },
  /* ========= Additional AI/ML — NLP & LLMs ========= */
  {
    category: "ai-ml", type: "github",
    entries: [
      { title: "LangChain — LLM Application Framework", description: "Framework for building applications powered by LLMs. Chains, agents, retrieval, and memory for complex LLM-powered workflows.", url: "https://github.com/langchain-ai/langchain", source: "LangChain", tags: ["LLM", "Agents", "Chains"] },
      { title: "Haystack — NLP Framework for RAG", description: "End-to-end NLP framework. Build RAG pipelines, question answering systems, and semantic search with any LLM provider.", url: "https://github.com/deepset-ai/haystack", source: "deepset", tags: ["RAG", "Search", "Pipelines"] },
      { title: "NLTK — Natural Language Toolkit", description: "Leading platform for building Python programs to work with human language data. Tokenization, stemming, tagging, and parsing.", url: "https://github.com/nltk/nltk", source: "NLTK", tags: ["NLP", "Tokenization", "Classic"] },
      { title: "FastText — Efficient Text Classification", description: "Library for efficient text classification and representation learning. Word vectors, text classification, and language identification.", url: "https://github.com/facebookresearch/fastText", source: "Meta AI", tags: ["Classification", "Word Vectors", "Fast"] },
      { title: "Gensim — Topic Modeling", description: "Python library for topic modeling and similarity detection. Word2Vec, Doc2Vec, LDA, and large-scale text processing.", url: "https://github.com/piskvorky/gensim", source: "Gensim", tags: ["Topics", "Word2Vec", "Similarity"] },
      { title: "CrewAI — Multi-Agent Framework", description: "Framework for orchestrating role-playing AI agents. Define agent roles, tasks, and tools for collaborative AI problem-solving.", url: "https://github.com/crewAIInc/crewAI", source: "CrewAI", tags: ["Multi-Agent", "Roles", "Orchestration"] },
      { title: "AutoGen — Multi-Agent Conversations", description: "Microsoft's framework for building LLM applications with multiple conversable agents. Code generation, planning, and human-in-the-loop.", url: "https://github.com/microsoft/autogen", source: "Microsoft", tags: ["Multi-Agent", "Conversation", "Code Gen"] },
      { title: "txtai — Semantic Search & Workflows", description: "All-in-one embeddings database for semantic search, LLM orchestration, and language model workflows.", url: "https://github.com/neuml/txtai", source: "NeuML", tags: ["Embeddings", "Search", "Workflows"] },
    ]
  },
  /* ========= Additional AI/ML — MLOps & Tools ========= */
  {
    category: "ai-ml", type: "github",
    entries: [
      { title: "BentoML — Model Serving Framework", description: "Build production-ready AI applications. Unified model serving, batching, GPU inference, and containerized deployment.", url: "https://github.com/bentoml/BentoML", source: "BentoML", tags: ["Serving", "Production", "GPU"] },
      { title: "ClearML — MLOps Platform", description: "End-to-end MLOps solution. Experiment tracking, data management, pipeline orchestration, and model deployment.", url: "https://github.com/allegroai/clearml", source: "ClearML", tags: ["MLOps", "Pipeline", "Tracking"] },
      { title: "Label Studio — Data Labeling Platform", description: "Open-source data labeling tool. Supports images, text, audio, video, and time series with customizable labeling interfaces.", url: "https://github.com/heartexlabs/label-studio", source: "Heartex", tags: ["Labeling", "Annotation", "Multi-Modal"] },
      { title: "Feast — Feature Store", description: "Open-source feature store for ML. Feature registry, online/offline serving, and integration with major data warehouses.", url: "https://github.com/feast-dev/feast", source: "Feast", tags: ["Feature Store", "Online", "Offline"] },
      { title: "Evidently — ML Monitoring", description: "Open-source ML monitoring tool. Data drift detection, model performance tracking, and automated test suites for production ML.", url: "https://github.com/evidentlyai/evidently", source: "Evidently", tags: ["Monitoring", "Drift", "Quality"] },
      { title: "TorchServe — PyTorch Model Serving", description: "Flexible and easy-to-use tool for serving PyTorch models in production. Multi-model serving, A/B testing, and monitoring.", url: "https://github.com/pytorch/serve", source: "PyTorch", tags: ["Serving", "PyTorch", "Production"] },
      { title: "Triton Inference Server — NVIDIA", description: "High-performance inference serving for any framework. Dynamic batching, model ensemble, and multi-GPU/multi-node deployment.", url: "https://github.com/triton-inference-server/server", source: "NVIDIA", tags: ["Inference", "Multi-GPU", "Batching"] },
    ]
  },
  /* ========= Additional Frontend — Web Platform ========= */
  {
    category: "frontend", type: "github",
    entries: [
      { title: "Lit — Web Components Library", description: "Simple library for building fast, lightweight web components. Standard-based, small footprint, and framework-agnostic.", url: "https://github.com/lit/lit", source: "Google", tags: ["Web Components", "Standards", "Lightweight"] },
      { title: "Storybook — UI Component Workshop", description: "Interactive workshop for building UI components in isolation. Visual testing, documentation, and design system management.", url: "https://github.com/storybookjs/storybook", source: "Storybook", tags: ["Components", "Documentation", "Visual Testing"] },
      { title: "Recharts — React Charting Library", description: "Composable charting library built on React components and D3. Area charts, bar charts, line charts, and responsive containers.", url: "https://github.com/recharts/recharts", source: "Recharts", tags: ["Charts", "React", "D3"] },
      { title: "Mantine — React Components Library", description: "Fully featured React component library. 100+ hooks and components, dark theme, accessibility, and TypeScript support.", url: "https://github.com/mantinedev/mantine", source: "Mantine", tags: ["Components", "Hooks", "Full-Featured"] },
      { title: "React Hook Form — Performant Forms", description: "Performant, flexible, and extensible forms with easy validation. Minimal re-renders, schema validation with Zod/Yup.", url: "https://github.com/react-hook-form/react-hook-form", source: "React Hook Form", tags: ["Forms", "Validation", "Performance"] },
      { title: "Zustand — Simple State Management", description: "Bear necessities for state management in React. Minimal API, no boilerplate, persist middleware, and devtools integration.", url: "https://github.com/pmndrs/zustand", source: "Poimandres", tags: ["State", "Simple", "Hooks"] },
      { title: "Zod — TypeScript Schema Validation", description: "TypeScript-first schema validation with static type inference. Composable schemas, parsing, and both sync and async validation.", url: "https://github.com/colinhacks/zod", source: "Colin McDonnell", tags: ["Validation", "Schema", "TypeScript"] },
      { title: "date-fns — Modern Date Utility", description: "Comprehensive, yet simple and consistent toolset for manipulating dates. Tree-shakeable, immutable, and TypeScript support.", url: "https://github.com/date-fns/date-fns", source: "date-fns", tags: ["Dates", "Utility", "Tree-Shakeable"] },
    ]
  },
  /* ========= Additional Frontend — Performance & A11y ========= */
  {
    category: "frontend", type: "ebook",
    entries: [
      { title: "Web Accessibility — MDN Guide", description: "Comprehensive guide to web accessibility. ARIA, semantic HTML, keyboard navigation, screen readers, and WCAG compliance.", url: "https://developer.mozilla.org/en-US/docs/Web/Accessibility", source: "MDN", tags: ["A11y", "ARIA", "WCAG"] },
      { title: "High Performance Browser Networking", description: "Ilya Grigorik's free book on web performance. TCP, TLS, HTTP/2, WebSocket, WebRTC, and mobile network optimization.", url: "https://hpbn.co/", source: "Ilya Grigorik", tags: ["Networking", "HTTP/2", "Performance"] },
      { title: "PWA Guide — web.dev", description: "Complete guide to Progressive Web Apps. Service workers, caching strategies, push notifications, and installability.", url: "https://web.dev/progressive-web-apps/", source: "Google", tags: ["PWA", "Service Workers", "Offline"] },
      { title: "Patterns.dev — Design Patterns for JS", description: "Modern JavaScript and React design patterns. Rendering patterns, performance patterns, and code organization strategies.", url: "https://www.patterns.dev/", source: "Addy Osmani", tags: ["Patterns", "JavaScript", "React"] },
      { title: "CSS Tricks — Complete Guide to Flexbox", description: "Comprehensive visual guide to CSS Flexbox. Every property explained with illustrations, use cases, and interactive examples.", url: "https://css-tricks.com/snippets/css/a-guide-to-flexbox/", source: "CSS-Tricks", tags: ["Flexbox", "CSS", "Visual Guide"] },
      { title: "CSS Tricks — Complete Guide to Grid", description: "Comprehensive visual guide to CSS Grid Layout. Grid container, grid items, areas, alignment, and responsive patterns.", url: "https://css-tricks.com/snippets/css/complete-guide-grid/", source: "CSS-Tricks", tags: ["Grid", "CSS", "Layout"] },
    ]
  },
  /* ========= Additional Backend — Architecture ========= */
  {
    category: "backend", type: "github",
    entries: [
      { title: "FastAPI — Modern Python API", description: "Fast, modern web framework for building APIs with Python based on type hints. Auto-documentation, validation, and async support.", url: "https://github.com/tiangolo/fastapi", source: "Sebastián Ramírez", tags: ["Python", "API", "Type Hints"] },
      { title: "Flask — Lightweight Python Web", description: "Micro web framework for Python. Simple, extensible, and well-documented with a rich ecosystem of extensions.", url: "https://github.com/pallets/flask", source: "Pallets", tags: ["Python", "Micro", "Extensions"] },
      { title: "Express — Node.js Web Framework", description: "The de facto standard for Node.js web applications. Middleware, routing, template engines, and the foundation of many Node frameworks.", url: "https://github.com/expressjs/express", source: "OpenJS", tags: ["Node.js", "Middleware", "Standard"] },
      { title: "Spring Boot — Java Framework", description: "Enterprise Java framework with convention over configuration. Auto-configuration, embedded servers, and production-ready features.", url: "https://github.com/spring-projects/spring-boot", source: "Spring", tags: ["Java", "Enterprise", "Auto-Config"] },
      { title: "gRPC — High-Performance RPC Framework", description: "Google's RPC framework. Protocol buffers, bidirectional streaming, and efficient binary serialization across languages.", url: "https://github.com/grpc/grpc", source: "CNCF", tags: ["RPC", "Protobuf", "Streaming"] },
      { title: "Hasura — Instant GraphQL APIs", description: "Instant realtime GraphQL on your databases. Event triggers, remote schemas, and fine-grained authorization.", url: "https://github.com/hasura/graphql-engine", source: "Hasura", tags: ["GraphQL", "Instant", "Real-Time"] },
      { title: "Supabase — Open Source Firebase", description: "Open source Firebase alternative. PostgreSQL database, authentication, instant APIs, edge functions, and storage.", url: "https://github.com/supabase/supabase", source: "Supabase", tags: ["BaaS", "PostgreSQL", "Auth"] },
      { title: "Pocketbase — Backend in a Single File", description: "Open source Go backend in a single file. Embedded SQLite, real-time subscriptions, auth, and file storage.", url: "https://github.com/pocketbase/pocketbase", source: "Pocketbase", tags: ["Single File", "Go", "SQLite"] },
    ]
  },
  /* ========= Additional Backend — Event-Driven ========= */
  {
    category: "backend", type: "case-study",
    entries: [
      { title: "How LinkedIn Built Apache Kafka", description: "The story of Kafka's creation at LinkedIn. Solving the log processing problem, commit log architecture, and scaling to trillions of messages.", url: "https://engineering.linkedin.com/blog", source: "LinkedIn", tags: ["Kafka", "Commit Log", "Origin Story"] },
      { title: "How Cloudflare Built Workers KV", description: "Cloudflare's globally distributed key-value store. Covers eventual consistency, edge caching, and serving billions of reads per day.", url: "https://blog.cloudflare.com/", source: "Cloudflare", tags: ["KV Store", "Edge", "Distributed"] },
      { title: "How Instacart Built Their Cart Service", description: "Instacart's shopping cart service at scale. Covers consistency challenges, inventory management, and handling concurrent updates.", url: "https://tech.instacart.com/", source: "Instacart", tags: ["Cart", "Consistency", "Concurrent"] },
      { title: "How Datadog Built Their Event Pipeline", description: "Datadog's event processing pipeline handling billions of events daily. Covers Kafka, schema evolution, and backpressure handling.", url: "https://www.datadoghq.com/blog/", source: "Datadog", tags: ["Events", "Kafka", "Backpressure"] },
      { title: "How Stripe Designed Their Payment Flow", description: "Stripe's approach to building reliable payment flows. Covers state machines, idempotency, webhook delivery, and financial reconciliation.", url: "https://stripe.com/blog/", source: "Stripe", tags: ["Payments", "State Machine", "Reconciliation"] },
    ]
  },
  /* ========= Additional DevOps ========= */
  {
    category: "devops", type: "github",
    entries: [
      { title: "Grafana — Observability Platform", description: "Open-source monitoring and observability platform. Dashboards, alerting, and data source integration for Prometheus, Loki, and more.", url: "https://github.com/grafana/grafana", source: "Grafana Labs", tags: ["Monitoring", "Dashboards", "Alerting"] },
      { title: "Prometheus — Monitoring System", description: "CNCF monitoring and alerting toolkit. Time series database, PromQL query language, multi-dimensional data model.", url: "https://github.com/prometheus/prometheus", source: "CNCF", tags: ["Metrics", "PromQL", "Alerting"] },
      { title: "Loki — Log Aggregation System", description: "Horizontally-scalable log aggregation system by Grafana Labs. Like Prometheus, but for logs. Cost-effective and integrated with Grafana.", url: "https://github.com/grafana/loki", source: "Grafana Labs", tags: ["Logs", "Aggregation", "Grafana"] },
      { title: "Teleport — Secure Infrastructure Access", description: "Zero-trust access to SSH, Kubernetes, databases, and web applications. Audit logging, session recording, and certificate-based auth.", url: "https://github.com/gravitational/teleport", source: "Teleport", tags: ["Zero Trust", "SSH", "Access"] },
      { title: "Velero — Kubernetes Backup & Restore", description: "Backup and restore Kubernetes resources and persistent volumes. Disaster recovery, cluster migration, and scheduled backups.", url: "https://github.com/vmware-tanzu/velero", source: "VMware", tags: ["Backup", "Restore", "DR"] },
      { title: "External Secrets Operator", description: "Kubernetes operator that integrates external secret management systems. AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager.", url: "https://github.com/external-secrets/external-secrets", source: "Community", tags: ["Secrets", "Kubernetes", "External"] },
      { title: "Cert-Manager — Kubernetes TLS", description: "Automatically manage and issue TLS certificates in Kubernetes. Let's Encrypt integration, custom CAs, and certificate rotation.", url: "https://github.com/cert-manager/cert-manager", source: "CNCF", tags: ["TLS", "Certificates", "Automation"] },
    ]
  },
  /* ========= Additional Databases ========= */
  {
    category: "databases", type: "github",
    entries: [
      { title: "ClickHouse — Fast Analytics Database", description: "Column-oriented database for real-time analytics. 100-1000x faster than traditional databases for analytical queries.", url: "https://github.com/ClickHouse/ClickHouse", source: "ClickHouse", tags: ["Analytics", "Columnar", "Real-Time"] },
      { title: "Dgraph — Distributed Graph Database", description: "Native GraphQL database with distributed architecture. Graph queries, mutations, and full-text search at scale.", url: "https://github.com/dgraph-io/dgraph", source: "Dgraph", tags: ["Graph", "GraphQL", "Distributed"] },
      { title: "KeyDB — Multi-Threaded Redis Fork", description: "Multi-threaded fork of Redis. Active-active replication, FLASH storage, and subkey expiration with full Redis compatibility.", url: "https://github.com/Snapchat/KeyDB", source: "Snapchat", tags: ["Redis", "Multi-Thread", "Active-Active"] },
      { title: "YugabyteDB — Distributed PostgreSQL", description: "High-performance distributed SQL database. PostgreSQL compatible, global distribution, and automated sharding.", url: "https://github.com/yugabyte/yugabyte-db", source: "Yugabyte", tags: ["PostgreSQL", "Distributed", "Sharding"] },
      { title: "Apache Cassandra — Wide-Column Store", description: "Highly scalable distributed database. Tunable consistency, linear scaling, and no single point of failure for large-scale applications.", url: "https://github.com/apache/cassandra", source: "Apache", tags: ["Wide-Column", "Scalable", "Distributed"] },
      { title: "FoundationDB — Distributed Key-Value", description: "Apple's distributed transactional key-value store. ACID transactions, multi-model layers, and powering Apple's iCloud infrastructure.", url: "https://github.com/apple/foundationdb", source: "Apple", tags: ["ACID", "Key-Value", "Apple"] },
      { title: "Weaviate — Vector Search Engine", description: "Open-source vector database for AI-native applications. Hybrid search, multi-tenancy, and built-in vectorization modules.", url: "https://github.com/weaviate/weaviate", source: "Weaviate", tags: ["Vector", "AI-Native", "Hybrid"] },
    ]
  },
  /* ========= Additional System Design ========= */
  {
    category: "system-design", type: "case-study",
    entries: [
      { title: "How Google Designs Large-Scale Systems", description: "Google's approach to system design at planet scale. Covers Bigtable, Spanner, MapReduce, and the Borg scheduling system.", url: "https://research.google/", source: "Google Research", tags: ["Planet Scale", "Spanner", "MapReduce"] },
      { title: "How Instagram Manages 2B Monthly Users", description: "Instagram's backend architecture. Covers feed ranking, Stories infrastructure, Reels pipeline, and serving media at massive scale.", url: "https://engineering.fb.com/", source: "Meta Engineering", tags: ["Feed", "Stories", "Media"] },
      { title: "How Twitter Built Their Timeline", description: "Twitter's home timeline architecture. Fan-out on write vs fan-out on read, timeline caching, and real-time tweet delivery.", url: "https://blog.x.com/engineering", source: "X Engineering", tags: ["Timeline", "Fan-out", "Caching"] },
      { title: "How Netflix Handles 250M Subscribers", description: "Netflix's microservice architecture. Covers service discovery, load balancing, resilience patterns, and content delivery at scale.", url: "https://netflixtechblog.com/", source: "Netflix", tags: ["Microservices", "Resilience", "CDN"] },
      { title: "How Uber Handles Millions of Rides", description: "Uber's ride-matching and dispatch system. Real-time matching, ETA prediction, dynamic pricing, and geospatial indexing.", url: "https://www.uber.com/blog/", source: "Uber", tags: ["Matching", "ETA", "Geospatial"] },
      { title: "How TikTok Serves Billions of Short Videos", description: "TikTok's content delivery network and recommendation system. Covers video processing, content moderation, and personalized feeds.", url: "https://newsroom.tiktok.com/", source: "TikTok", tags: ["Short Video", "CDN", "Recommendation"] },
      { title: "How Stripe Processes Billions in Payments", description: "Stripe's payment processing infrastructure. Covers PCI compliance, fraud detection, risk scoring, and multi-currency support.", url: "https://stripe.com/blog/", source: "Stripe", tags: ["Payments", "PCI", "Fraud"] },
    ]
  },
  /* ========= Additional Security ========= */
  {
    category: "security", type: "ebook",
    entries: [
      { title: "OWASP Top 10 — Web Security Risks", description: "The definitive guide to the top 10 web application security risks. Injection, broken auth, XSS, CSRF, and security misconfiguration.", url: "https://owasp.org/www-project-top-ten/", source: "OWASP", tags: ["Top 10", "Web", "Risks"] },
      { title: "OWASP Testing Guide", description: "Comprehensive web application security testing methodology. 90+ test cases covering authentication, session management, and input validation.", url: "https://owasp.org/www-project-web-security-testing-guide/", source: "OWASP", tags: ["Testing", "Methodology", "Comprehensive"] },
      { title: "Hackers & Painters — Paul Graham", description: "Essays on programming, startups, and hacker culture. Explores the intersection of technology, creativity, and security mindset.", url: "https://paulgraham.com/hp.html", source: "Paul Graham", tags: ["Culture", "Essays", "Mindset"] },
      { title: "The Web Application Hacker's Handbook", description: "Comprehensive guide to web application penetration testing. Covers attack techniques, defense strategies, and real-world vulnerabilities.", url: "https://portswigger.net/web-security", source: "PortSwigger", tags: ["Pen Testing", "Web Apps", "Attacks"] },
    ]
  },
  {
    category: "security", type: "github",
    entries: [
      { title: "OWASP ZAP — Security Testing Tool", description: "World's most widely used web app security scanner. Automated scanning, API testing, and integration with CI/CD pipelines.", url: "https://github.com/zaproxy/zaproxy", source: "OWASP", tags: ["Scanner", "Automated", "CI/CD"] },
      { title: "Trivy — Comprehensive Security Scanner", description: "All-in-one security scanner. Container images, file systems, Git repos, and Kubernetes clusters for vulnerabilities and misconfigurations.", url: "https://github.com/aquasecurity/trivy", source: "Aqua Security", tags: ["Container", "Scanner", "All-in-One"] },
      { title: "Checkov — IaC Security Scanner", description: "Static analysis tool for infrastructure as code. Scans Terraform, CloudFormation, Kubernetes, and Helm charts for misconfigurations.", url: "https://github.com/bridgecrewio/checkov", source: "Bridgecrew", tags: ["IaC", "Static Analysis", "Terraform"] },
      { title: "Nuclei — Vulnerability Scanner", description: "Fast, template-based vulnerability scanner. 7000+ templates for detecting vulnerabilities, misconfigurations, and exposed APIs.", url: "https://github.com/projectdiscovery/nuclei", source: "ProjectDiscovery", tags: ["Templates", "Fast", "Vulnerabilities"] },
      { title: "Gitleaks — Git Secret Scanner", description: "Protect and discover secrets using Gitleaks. Scans Git repos for hardcoded secrets, API keys, and sensitive data in commits.", url: "https://github.com/gitleaks/gitleaks", source: "Gitleaks", tags: ["Secrets", "Git", "Prevention"] },
    ]
  },
  /* ========= Additional Data Science ========= */
  {
    category: "data-science", type: "github",
    entries: [
      { title: "Scikit-Learn — ML Library for Python", description: "The most popular ML library for Python. Classification, regression, clustering, dimensionality reduction, and model selection.", url: "https://github.com/scikit-learn/scikit-learn", source: "Scikit-Learn", tags: ["ML", "Python", "Classic"] },
      { title: "XGBoost — Gradient Boosting Library", description: "Optimized distributed gradient boosting library. High performance, efficient, and the go-to for tabular data competitions.", url: "https://github.com/dmlc/xgboost", source: "DMLC", tags: ["Gradient Boosting", "Tabular", "Competition"] },
      { title: "LightGBM — Light Gradient Boosting", description: "Microsoft's gradient boosting framework. Faster training, lower memory usage, and GPU support for large-scale datasets.", url: "https://github.com/microsoft/LightGBM", source: "Microsoft", tags: ["Boosting", "Fast", "GPU"] },
      { title: "PySpark — Apache Spark for Python", description: "Python API for Apache Spark. Distributed data processing, machine learning with MLlib, and structured streaming.", url: "https://github.com/apache/spark", source: "Apache", tags: ["Spark", "Distributed", "Big Data"] },
      { title: "Streamlit — Data App Framework", description: "Create data apps in minutes with Python. Interactive widgets, charts, maps, and deploy with Streamlit Community Cloud.", url: "https://github.com/streamlit/streamlit", source: "Streamlit", tags: ["Data Apps", "Interactive", "Python"] },
      { title: "Prefect — Modern Data Orchestration", description: "Modern workflow orchestration for data engineering. Python-native, observable, and designed for the modern data stack.", url: "https://github.com/PrefectHQ/prefect", source: "Prefect", tags: ["Orchestration", "Workflow", "Modern"] },
      { title: "Dagster — Data Orchestration Platform", description: "Cloud-native data orchestration. Asset-centric approach, type system for data, and integration with modern data tools.", url: "https://github.com/dagster-io/dagster", source: "Dagster", tags: ["Assets", "Orchestration", "Type System"] },
    ]
  },
  /* ========= Additional SQL ========= */
  {
    category: "sql", type: "ebook",
    entries: [
      { title: "Use The Index, Luke — SQL Indexing Guide", description: "Developer-centric guide to SQL indexing. B-tree internals, index-only scans, partial indexes, and database-agnostic optimization.", url: "https://use-the-index-luke.com/", source: "Markus Winand", tags: ["Indexing", "B-Tree", "Optimization"] },
      { title: "Modern SQL — Beyond Traditional SQL", description: "Guide to modern SQL features. Window functions, CTEs, LATERAL joins, GROUPING SETS, and JSON support across databases.", url: "https://modern-sql.com/", source: "Markus Winand", tags: ["Modern", "Window Functions", "JSON"] },
      { title: "PostgreSQL Tutorial — Complete Guide", description: "Comprehensive PostgreSQL tutorial. Data types, queries, indexes, views, stored procedures, triggers, and performance tuning.", url: "https://www.postgresqltutorial.com/", source: "PostgreSQL Tutorial", tags: ["PostgreSQL", "Tutorial", "Comprehensive"] },
      { title: "SQLite Documentation — Complete", description: "Complete reference for SQLite. File format, SQL syntax, built-in functions, and advanced features like JSON, FTS5, and R-Trees.", url: "https://sqlite.org/docs.html", source: "SQLite", tags: ["SQLite", "Reference", "Complete"] },
    ]
  },
  {
    category: "sql", type: "course",
    entries: [
      { title: "Mode SQL Tutorial — Analytics", description: "Practical SQL tutorial focused on analytics. FROM, WHERE, JOINs, aggregations, subqueries, and window functions with real datasets.", url: "https://mode.com/sql-tutorial/", source: "Mode Analytics", tags: ["Analytics", "Practical", "Datasets"] },
      { title: "SQLZoo — Interactive SQL Tutorial", description: "Interactive SQL tutorial with live database. Practice queries against real datasets covering SELECT, JOINs, and subqueries.", url: "https://sqlzoo.net/", source: "SQLZoo", tags: ["Interactive", "Practice", "Live DB"] },
      { title: "DataLemur — SQL Interview Practice", description: "SQL interview practice from a former Facebook data scientist. Real interview questions from FAANG companies with detailed solutions.", url: "https://datalemur.com/", source: "DataLemur", tags: ["Interview", "FAANG", "Solutions"] },
    ]
  },
  /* ========= Additional Mobile ========= */
  {
    category: "mobile", type: "github",
    entries: [
      { title: "React Native — Cross-Platform Mobile", description: "Build native mobile apps using React. Hot reloading, native components, and a large ecosystem of community libraries.", url: "https://github.com/facebook/react-native", source: "Meta", tags: ["React Native", "Cross-Platform", "Native"] },
      { title: "Expo — React Native Framework", description: "Framework and platform for universal React applications. Managed workflow, OTA updates, and cloud build services.", url: "https://github.com/expo/expo", source: "Expo", tags: ["Expo", "OTA Updates", "Managed"] },
      { title: "Swift — Apple's Programming Language", description: "Apple's modern programming language for iOS, macOS, watchOS, and tvOS. Type safety, optionals, and protocol-oriented programming.", url: "https://github.com/apple/swift", source: "Apple", tags: ["Swift", "iOS", "Type Safe"] },
      { title: "Lottie — Mobile Animations", description: "Render After Effects animations on mobile. JSON-based format with small file sizes and native rendering on iOS and Android.", url: "https://github.com/airbnb/lottie-android", source: "Airbnb", tags: ["Animations", "After Effects", "Native"] },
      { title: "React Navigation — Routing for RN", description: "Routing and navigation for React Native apps. Stack, tab, drawer navigators, deep linking, and TypeScript support.", url: "https://github.com/react-navigation/react-navigation", source: "React Navigation", tags: ["Navigation", "Routing", "Deep Link"] },
    ]
  },
  /* ========= Additional Cloud ========= */
  {
    category: "cloud", type: "github",
    entries: [
      { title: "AWS CDK — Cloud Development Kit", description: "Define cloud infrastructure using familiar programming languages. TypeScript, Python, Java, and Go support with high-level constructs.", url: "https://github.com/aws/aws-cdk", source: "AWS", tags: ["IaC", "CDK", "TypeScript"] },
      { title: "Serverless Framework", description: "Build serverless applications across AWS, Azure, and GCP. Function deployment, event triggers, and plugin ecosystem.", url: "https://github.com/serverless/serverless", source: "Serverless", tags: ["Serverless", "Functions", "Multi-Cloud"] },
      { title: "SST — Serverless Stack", description: "Build full-stack apps on AWS. Live Lambda development, infrastructure as code, and frontend deployment with zero configuration.", url: "https://github.com/sst/sst", source: "SST", tags: ["AWS", "Full-Stack", "Live Dev"] },
      { title: "OpenTofu — Open Source Terraform", description: "Community-driven fork of Terraform. Declarative infrastructure as code with full Terraform compatibility and open governance.", url: "https://github.com/opentofu/opentofu", source: "Linux Foundation", tags: ["IaC", "Open Source", "Terraform"] },
    ]
  },
  {
    category: "cloud", type: "ebook",
    entries: [
      { title: "AWS Well-Architected Framework", description: "AWS's best practices for building secure, high-performing, resilient, and efficient infrastructure. Five pillars and design principles.", url: "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html", source: "AWS", tags: ["Best Practices", "Five Pillars", "Architecture"] },
      { title: "Google Cloud Architecture Center", description: "Reference architectures, design guides, and best practices for building on Google Cloud. AI/ML, data analytics, and application development.", url: "https://cloud.google.com/architecture", source: "Google Cloud", tags: ["Reference", "Architecture", "GCP"] },
      { title: "Azure Architecture Center", description: "Guidance for architecting solutions on Azure. Cloud design patterns, reference architectures, and best practices.", url: "https://learn.microsoft.com/en-us/azure/architecture/", source: "Microsoft", tags: ["Azure", "Patterns", "Reference"] },
    ]
  },
  /* ========= Additional Dart/Flutter ========= */
  {
    category: "dart", type: "github",
    entries: [
      { title: "GetX — Flutter State Management", description: "Feature-rich state management, navigation, and utility library. Reactive programming, dependency injection, and route management.", url: "https://github.com/jonataslaw/getx", source: "Jonatas Law", tags: ["GetX", "State", "All-in-One"] },
      { title: "Dio — HTTP Client for Dart", description: "Powerful HTTP client for Dart. Interceptors, global configuration, FormData, request cancellation, and file downloading.", url: "https://github.com/cfug/dio", source: "CFUG", tags: ["HTTP", "Client", "Interceptors"] },
      { title: "Flame — Flutter Game Engine", description: "2D game engine for Flutter. Sprites, animations, collision detection, and support for tiled maps and particle effects.", url: "https://github.com/flame-engine/flame", source: "Flame", tags: ["Game", "2D", "Sprites"] },
      { title: "Mason — Dart Code Generation", description: "Template-based code generation for Dart. Create custom templates, generate boilerplate, and share templates via BrickHub.", url: "https://github.com/felangel/mason", source: "Felix Angelov", tags: ["Code Gen", "Templates", "Boilerplate"] },
      { title: "Very Good CLI — Flutter Project Tools", description: "CLI tools for Flutter development by Very Good Ventures. Project scaffolding, testing utilities, and CI/CD templates.", url: "https://github.com/VeryGoodOpenSource/very_good_cli", source: "Very Good Ventures", tags: ["CLI", "Scaffolding", "Best Practices"] },
    ]
  },
  /* ========= Additional Kotlin ========= */
  {
    category: "kotlin", type: "github",
    entries: [
      { title: "Koin — Kotlin Dependency Injection", description: "Pragmatic lightweight DI framework for Kotlin. No code generation, DSL-based definitions, and multiplatform support.", url: "https://github.com/InsertKoinIO/koin", source: "InsertKoin", tags: ["DI", "Lightweight", "DSL"] },
      { title: "SQLDelight — Typesafe SQL for Kotlin", description: "Generate typesafe Kotlin APIs from SQL. Multiplatform support, migrations, and compile-time SQL verification.", url: "https://github.com/cashapp/sqldelight", source: "CashApp", tags: ["SQL", "Type-Safe", "Multiplatform"] },
      { title: "Kotlin Serialization — JSON & More", description: "Kotlin multiplatform serialization library. JSON, CBOR, Protocol Buffers with compile-time safety and reflection-free.", url: "https://github.com/Kotlin/kotlinx.serialization", source: "JetBrains", tags: ["Serialization", "JSON", "Multiplatform"] },
      { title: "Kotlin Coroutines — Async Library", description: "Official coroutines library for Kotlin. Structured concurrency, flows, channels, and integration with reactive streams.", url: "https://github.com/Kotlin/kotlinx.coroutines", source: "JetBrains", tags: ["Coroutines", "Flow", "Channels"] },
      { title: "Detekt — Kotlin Static Analysis", description: "Static code analysis for Kotlin. Code smells, complexity analysis, naming conventions, and custom rule support.", url: "https://github.com/detekt/detekt", source: "Detekt", tags: ["Static Analysis", "Code Smells", "Quality"] },
    ]
  },
  /* ========= Additional Rust ========= */
  {
    category: "rust", type: "github",
    entries: [
      { title: "Nushell — Modern Shell Written in Rust", description: "New type of shell. Structured data pipelines, type system, and modern CLI experience written in Rust.", url: "https://github.com/nushell/nushell", source: "Nushell", tags: ["Shell", "Structured Data", "CLI"] },
      { title: "Biome — Web Toolchain in Rust", description: "Fast formatter and linter for JavaScript, TypeScript, JSX, and JSON. 95% Prettier compatibility with much faster performance.", url: "https://github.com/biomejs/biome", source: "Biome", tags: ["Formatter", "Linter", "Web"] },
      { title: "Dioxus — Cross-Platform Rust GUI", description: "Ergonomic framework for building cross-platform UIs in Rust. React-like API, desktop, mobile, and web targets.", url: "https://github.com/DioxusLabs/dioxus", source: "Dioxus", tags: ["GUI", "Cross-Platform", "React-Like"] },
      { title: "Wasmer — Universal WebAssembly Runtime", description: "Fast and secure WebAssembly runtime. Run WASM modules anywhere: desktop, cloud, edge, and embedded devices.", url: "https://github.com/wasmerio/wasmer", source: "Wasmer", tags: ["WASM", "Runtime", "Universal"] },
      { title: "Meilisearch (Rust Core)", description: "Lightning-fast search engine written in Rust. Typo tolerance, faceted search, and instant results with sub-50ms response times.", url: "https://github.com/meilisearch/meilisearch", source: "Meilisearch", tags: ["Search", "Typo Tolerant", "Fast"] },
    ]
  },
  {
    category: "rust", type: "case-study",
    entries: [
      { title: "How Cloudflare Uses Rust for Pingora", description: "Cloudflare's HTTP proxy framework replacing Nginx. Built entirely in Rust for memory safety, performance, and customizability.", url: "https://blog.cloudflare.com/how-we-built-pingora-the-proxy-that-connects-cloudflare-to-the-internet/", source: "Cloudflare", tags: ["Proxy", "Pingora", "Nginx Replacement"] },
      { title: "How Dropbox Rewrote Their Sync Engine", description: "Dropbox's rewrite of their sync engine from Python to Rust. Covers performance improvements, memory safety, and the migration process.", url: "https://dropbox.tech/infrastructure/rewriting-the-heart-of-our-sync-engine", source: "Dropbox", tags: ["Sync", "Rewrite", "Python to Rust"] },
      { title: "How NPM Uses Rust for Package Management", description: "NPM's use of Rust for performance-critical paths. Covers the npm audit command, dependency resolution, and registry operations.", url: "https://github.blog/", source: "GitHub", tags: ["npm", "Package Management", "Performance"] },
    ]
  },
  /* ========= Additional Mobile — Ecosystem ========= */
  {
    category: "mobile", type: "course",
    entries: [
      { title: "100 Days of SwiftUI — Hacking with Swift", description: "Free 100-day Swift and SwiftUI curriculum. Daily projects, challenges, and quizzes building real iOS apps.", url: "https://www.hackingwithswift.com/100/swiftui", source: "Paul Hudson", tags: ["SwiftUI", "100 Days", "Free"] },
      { title: "Android Jetpack Compose Basics", description: "Google's official Compose course. Declarative UI, state management, theming, navigation, and animation in Compose.", url: "https://developer.android.com/courses/android-basics-compose", source: "Google", tags: ["Compose", "Basics", "Official"] },
      { title: "React Native Express — Comprehensive Guide", description: "Free guide to learning React Native. Environment setup, core components, navigation, state management, and native modules.", url: "https://www.reactnative.express/", source: "Devin Abbott", tags: ["React Native", "Comprehensive", "Free"] },
    ]
  },
  /* ========= Additional Data Science — Analytics ========= */
  {
    category: "data-science", type: "case-study",
    entries: [
      { title: "How Airbnb Built Their Analytics Platform", description: "Airbnb's data infrastructure for analytics. Covers Minerva metrics layer, experimentation platform, and data quality tools.", url: "https://medium.com/airbnb-engineering/", source: "Airbnb", tags: ["Analytics", "Minerva", "Experiments"] },
      { title: "How Netflix Uses Data for Content Decisions", description: "Netflix's data-driven content strategy. A/B testing thumbnails, recommendation algorithms, and viewership predictions.", url: "https://netflixtechblog.com/", source: "Netflix", tags: ["Content", "A/B Testing", "Recommendations"] },
      { title: "How Uber Uses ML for Dynamic Pricing", description: "Uber's surge pricing algorithm. Covers demand prediction, supply optimization, market equilibrium, and rider-driver matching.", url: "https://www.uber.com/blog/", source: "Uber", tags: ["Pricing", "Demand", "Optimization"] },
      { title: "How DoorDash Optimizes Delivery Routes", description: "DoorDash's route optimization system. Vehicle routing problem, ETA prediction, and real-time dispatching across millions of deliveries.", url: "https://doordash.engineering/", source: "DoorDash", tags: ["Routes", "VRP", "Dispatching"] },
    ]
  },
  /* ========= AI/ML — Reinforcement Learning & Robotics ========= */
  {
    category: "ai-ml", type: "github",
    entries: [
      { title: "Gymnasium — RL Environments", description: "Standard API for RL environments. Classic control, Atari, MuJoCo, and custom environments with unified interface.", url: "https://github.com/Farama-Foundation/Gymnasium", source: "Farama", tags: ["RL", "Environments", "Standard"] },
      { title: "Stable Baselines3 — RL Algorithms", description: "Reliable implementations of RL algorithms in PyTorch. PPO, A2C, SAC, TD3, and DQN with comprehensive documentation.", url: "https://github.com/DLR-RM/stable-baselines3", source: "DLR-RM", tags: ["RL", "PPO", "PyTorch"] },
      { title: "RLlib — Scalable Reinforcement Learning", description: "Industry-grade RL library built on Ray. Multi-agent, offline RL, model-based, and curriculum learning at scale.", url: "https://github.com/ray-project/ray", source: "Anyscale", tags: ["Scalable RL", "Multi-Agent", "Ray"] },
      { title: "Isaac Sim — NVIDIA Robot Simulation", description: "NVIDIA's robotics simulation platform. Physics-accurate simulation, synthetic data generation, and sim-to-real transfer.", url: "https://developer.nvidia.com/isaac-sim", source: "NVIDIA", tags: ["Robotics", "Simulation", "Physics"] },
      { title: "ROS 2 — Robot Operating System", description: "Open-source robotics middleware. Communication framework, sensor integration, navigation, and manipulation for autonomous robots.", url: "https://github.com/ros2/ros2", source: "Open Robotics", tags: ["ROS", "Robotics", "Middleware"] },
      { title: "PettingZoo — Multi-Agent RL", description: "Standard API for multi-agent reinforcement learning. Cooperative, competitive, and mixed environments for MARL research.", url: "https://github.com/Farama-Foundation/PettingZoo", source: "Farama", tags: ["Multi-Agent", "MARL", "Environments"] },
    ]
  },
  /* ========= AI/ML — Audio & Speech ========= */
  {
    category: "ai-ml", type: "github",
    entries: [
      { title: "Bark — Text-to-Audio Model", description: "Transformer-based text-to-audio model. Generate speech, music, and sound effects from text prompts with multiple speaker voices.", url: "https://github.com/suno-ai/bark", source: "Suno AI", tags: ["Audio", "TTS", "Generation"] },
      { title: "Coqui TTS — Deep Learning TTS", description: "Deep learning toolkit for text-to-speech. Multi-speaker, multi-lingual, and voice cloning with pre-trained models.", url: "https://github.com/coqui-ai/TTS", source: "Coqui", tags: ["TTS", "Voice Clone", "Multi-Lingual"] },
      { title: "AudioCraft — Audio Generation", description: "Meta's audio generation framework. MusicGen for music, AudioGen for sound effects, and EnCodec for audio compression.", url: "https://github.com/facebookresearch/audiocraft", source: "Meta AI", tags: ["Music Gen", "AudioGen", "Compression"] },
      { title: "Raven — Real-Time Voice AI", description: "Build voice-enabled AI applications. Wake word detection, speech-to-text, intent recognition, and text-to-speech pipeline.", url: "https://picovoice.ai/", source: "Picovoice", tags: ["Voice AI", "Wake Word", "On-Device"] },
      { title: "Vosk — Offline Speech Recognition", description: "Offline speech recognition API. 20+ languages, lightweight models for mobile, and speaker identification support.", url: "https://github.com/alphacep/vosk-api", source: "Alpha Cephei", tags: ["Offline", "ASR", "Lightweight"] },
    ]
  },
  /* ========= AI/ML — More Case Studies ========= */
  {
    category: "ai-ml", type: "case-study",
    entries: [
      { title: "How Spotify Uses ML for Music Discovery", description: "Spotify's recommendation engine. Collaborative filtering, content-based features, and the Discover Weekly algorithm.", url: "https://engineering.atspotify.com/", source: "Spotify", tags: ["Music", "Recommendations", "Discovery"] },
      { title: "How LinkedIn Uses AI for Feed Ranking", description: "LinkedIn's feed ranking system. Two-pass ranking model, real-time features, and optimizing for member value.", url: "https://engineering.linkedin.com/blog", source: "LinkedIn", tags: ["Feed", "Ranking", "Value"] },
      { title: "How Amazon Uses ML for Product Search", description: "Amazon's product search and ranking. Semantic understanding, query reformulation, and personalized result ordering.", url: "https://www.amazon.science/", source: "Amazon Science", tags: ["Search", "Ranking", "E-Commerce"] },
      { title: "How Adobe Uses AI in Creative Cloud", description: "Adobe's AI features across Creative Cloud. Generative fill, neural filters, content-aware fill, and Firefly model architecture.", url: "https://blog.adobe.com/", source: "Adobe", tags: ["Creative", "Generative", "Firefly"] },
      { title: "How Apple Trains Siri", description: "Apple's approach to voice assistant ML. On-device processing, privacy-preserving training, and multi-task understanding.", url: "https://machinelearning.apple.com/", source: "Apple", tags: ["Siri", "On-Device", "Privacy"] },
      { title: "How Bloomberg Uses NLP for Finance", description: "Bloomberg's NLP applications in financial analysis. Sentiment analysis, named entity recognition, and relationship extraction from filings.", url: "https://www.bloomberg.com/company/values/tech-at-bloomberg/", source: "Bloomberg", tags: ["Finance", "NLP", "Sentiment"] },
    ]
  },
  /* ========= Frontend — More Frameworks & Tools ========= */
  {
    category: "frontend", type: "github",
    entries: [
      { title: "Svelte — Cybernetically Enhanced Web Apps", description: "Compile-time framework with no virtual DOM. Write less code, no runtime overhead, and first-class animations and transitions.", url: "https://github.com/sveltejs/svelte", source: "Svelte", tags: ["Compile-Time", "No VDOM", "Animations"] },
      { title: "SvelteKit — Full-Stack Svelte Framework", description: "Full-stack framework built on Svelte. File-based routing, SSR, SSG, API routes, and adapter-based deployment.", url: "https://github.com/sveltejs/kit", source: "Svelte", tags: ["Full-Stack", "SSR", "Routing"] },
      { title: "Next.js — The React Framework", description: "The most popular React meta-framework. App router, server components, API routes, and deployment optimization.", url: "https://github.com/vercel/next.js", source: "Vercel", tags: ["React", "SSR", "Full-Stack"] },
      { title: "Nuxt — The Vue.js Framework", description: "Intuitive full-stack framework for Vue.js. Auto-imports, file-based routing, hybrid rendering, and extensive module ecosystem.", url: "https://github.com/nuxt/nuxt", source: "Nuxt", tags: ["Vue", "Full-Stack", "Modules"] },
      { title: "Preact — Fast 3kB React Alternative", description: "Fast 3kB alternative to React with the same modern API. High performance, small size, and drop-in React compatibility.", url: "https://github.com/preactjs/preact", source: "Preact", tags: ["Lightweight", "React Compatible", "Fast"] },
      { title: "Alpine.js — Minimal JS Framework", description: "Rugged, minimal tool for composing behavior directly in markup. Think of it as Tailwind for JavaScript.", url: "https://github.com/alpinejs/alpine", source: "Alpine.js", tags: ["Minimal", "Declarative", "Markup"] },
      { title: "HTMX — High Power Tools for HTML", description: "Access AJAX, CSS transitions, WebSockets, and SSE directly in HTML. Hypertext-driven development without heavy JS frameworks.", url: "https://github.com/bigskysoftware/htmx", source: "Big Sky Software", tags: ["HTML", "AJAX", "Hypermedia"] },
    ]
  },
  /* ========= Frontend — More Case Studies ========= */
  {
    category: "frontend", type: "case-study",
    entries: [
      { title: "How Figma Built Their Canvas Renderer", description: "Figma's WebGL-based canvas renderer. 60fps rendering, GPU acceleration, and handling thousands of objects in real-time.", url: "https://www.figma.com/blog/", source: "Figma", tags: ["Canvas", "WebGL", "GPU"] },
      { title: "How Google Built Material Design 3", description: "Google's design system evolution. Dynamic color, accessibility improvements, and cross-platform consistency.", url: "https://m3.material.io/", source: "Google", tags: ["Design System", "Material", "Dynamic Color"] },
      { title: "How Stripe Built Their Dashboard", description: "Stripe's dashboard engineering. Real-time data visualization, customizable views, and handling complex financial data.", url: "https://stripe.com/blog/", source: "Stripe", tags: ["Dashboard", "Data Viz", "Real-Time"] },
      { title: "How Airbnb Built Visx for Data Visualization", description: "Airbnb's collection of reusable low-level visualization components. How they combined D3 primitives with React rendering.", url: "https://medium.com/airbnb-engineering/", source: "Airbnb", tags: ["Visx", "D3", "React"] },
      { title: "How BBC Built Their Design System", description: "BBC's GEL (Global Experience Language) design system. Responsive design, accessibility, and serving diverse audiences globally.", url: "https://www.bbc.co.uk/gel", source: "BBC", tags: ["Design System", "A11y", "Responsive"] },
    ]
  },
  /* ========= Backend — More Languages & Frameworks ========= */
  {
    category: "backend", type: "github",
    entries: [
      { title: "Actix Web — Rust Web Framework", description: "Blazingly fast web framework for Rust. Actor model, async I/O, middleware, WebSocket, and type-safe routing.", url: "https://github.com/actix/actix-web", source: "Actix", tags: ["Rust", "Actors", "Fast"] },
      { title: "Axum — Ergonomic Rust Web Framework", description: "Tokio-based web framework focused on ergonomics. Extractors, state sharing, and composable routing with tower middleware.", url: "https://github.com/tokio-rs/axum", source: "Tokio", tags: ["Rust", "Tokio", "Ergonomic"] },
      { title: "Warp — Composable Rust Web Server", description: "Composable web server framework in Rust. Filter system for building APIs, WebSocket support, and async/await based.", url: "https://github.com/seanmonstar/warp", source: "Sean McArthur", tags: ["Rust", "Filters", "Composable"] },
      { title: "Ruby on Rails — Web Framework", description: "Convention over configuration web framework. MVC architecture, database migrations, asset pipeline, and rapid development.", url: "https://github.com/rails/rails", source: "Rails", tags: ["Ruby", "MVC", "Convention"] },
      { title: "Laravel — PHP Web Framework", description: "Elegant PHP framework for web artisans. Eloquent ORM, Blade templates, queues, events, and comprehensive ecosystem.", url: "https://github.com/laravel/laravel", source: "Laravel", tags: ["PHP", "Eloquent", "Full-Stack"] },
      { title: "Ktor — Kotlin Web Framework", description: "JetBrains' asynchronous web framework for Kotlin. Coroutine-based, lightweight, and designed for microservices.", url: "https://github.com/ktorio/ktor", source: "JetBrains", tags: ["Kotlin", "Coroutines", "Async"] },
    ]
  },
  /* ========= Backend — More Case Studies ========= */
  {
    category: "backend", type: "case-study",
    entries: [
      { title: "How Airbnb Unified Their Payments", description: "Airbnb's payment platform serving 220+ countries. Multi-currency handling, payment processing, refunds, and dispute management.", url: "https://medium.com/airbnb-engineering/", source: "Airbnb", tags: ["Payments", "Multi-Currency", "Global"] },
      { title: "How Spotify Built Their Event Delivery System", description: "Spotify's event-driven architecture. Event schema registry, guaranteed delivery, and processing billions of events per day.", url: "https://engineering.atspotify.com/", source: "Spotify", tags: ["Events", "Schema", "Delivery"] },
      { title: "How GitHub Handles Git Operations at Scale", description: "GitHub's Git infrastructure. Partitioned repositories, object storage, and serving millions of Git operations per day.", url: "https://github.blog/engineering/", source: "GitHub", tags: ["Git", "Storage", "Scale"] },
      { title: "How Lyft Built Their Marketplace", description: "Lyft's marketplace platform. Dynamic pricing, supply positioning, matching algorithms, and demand prediction.", url: "https://eng.lyft.com/", source: "Lyft", tags: ["Marketplace", "Pricing", "Matching"] },
      { title: "How Coinbase Built Their Trading Engine", description: "Coinbase's exchange infrastructure. Order matching, market data distribution, and maintaining consistency during high volatility.", url: "https://www.coinbase.com/blog/", source: "Coinbase", tags: ["Trading", "Order Book", "Matching"] },
    ]
  },
  /* ========= DevOps — More Tools & Practices ========= */
  {
    category: "devops", type: "github",
    entries: [
      { title: "Terraform — Infrastructure as Code", description: "HashiCorp's infrastructure as code tool. Declarative configuration, state management, and multi-cloud provisioning.", url: "https://github.com/hashicorp/terraform", source: "HashiCorp", tags: ["IaC", "Multi-Cloud", "Declarative"] },
      { title: "Ansible — IT Automation", description: "Agentless IT automation engine. Configuration management, application deployment, and infrastructure orchestration.", url: "https://github.com/ansible/ansible", source: "Red Hat", tags: ["Automation", "Agentless", "Configuration"] },
      { title: "Longhorn — Cloud-Native Storage", description: "Lightweight, reliable distributed block storage for Kubernetes. Incremental snapshots, backups, and disaster recovery.", url: "https://github.com/longhorn/longhorn", source: "CNCF", tags: ["Storage", "Block", "Kubernetes"] },
      { title: "MinIO — Object Storage for K8s", description: "High-performance, S3-compatible object storage. Native Kubernetes integration, erasure coding, and immutability.", url: "https://github.com/minio/minio", source: "MinIO", tags: ["Object Storage", "S3", "Kubernetes"] },
      { title: "KEDA — Kubernetes Event-Driven Autoscaling", description: "Event-driven autoscaler for Kubernetes. Scale any container based on the number of events in a queue, stream, or metric.", url: "https://github.com/kedacore/keda", source: "CNCF", tags: ["Autoscaling", "Events", "Kubernetes"] },
    ]
  },
  /* ========= DevOps — More Case Studies ========= */
  {
    category: "devops", type: "case-study",
    entries: [
      { title: "How GitLab Operates Their DevOps Platform", description: "GitLab's self-hosted infrastructure. Multi-region deployment, zero-downtime migrations, and operating at scale on GCP.", url: "https://about.gitlab.com/blog/", source: "GitLab", tags: ["DevOps", "Self-Hosted", "GCP"] },
      { title: "How Cloudflare Deploys 100+ Times/Day", description: "Cloudflare's rapid deployment strategy. Canary releases, progressive rollouts, and monitoring-driven deployment across 300+ cities.", url: "https://blog.cloudflare.com/", source: "Cloudflare", tags: ["Deployments", "Canary", "Global"] },
      { title: "How LinkedIn Manages Their CI/CD Pipeline", description: "LinkedIn's CI/CD infrastructure. Build system optimization, test parallelization, and managing 12K+ builds per day.", url: "https://engineering.linkedin.com/blog", source: "LinkedIn", tags: ["CI/CD", "Build", "Optimization"] },
      { title: "How Stripe Ensures API Reliability", description: "Stripe's approach to API reliability. Graceful degradation, retry strategies, load shedding, and circuit breaker patterns.", url: "https://stripe.com/blog/", source: "Stripe", tags: ["Reliability", "API", "Graceful Degradation"] },
    ]
  },
  /* ========= Databases — More Case Studies ========= */
  {
    category: "databases", type: "case-study",
    entries: [
      { title: "How Figma Scaled Their PostgreSQL Database", description: "Figma's database scaling journey. Vertical scaling limits, read replicas, PgBouncer connection pooling, and logical replication.", url: "https://www.figma.com/blog/", source: "Figma", tags: ["PostgreSQL", "Scaling", "Connection Pool"] },
      { title: "How Pinterest Migrated Their Data Platform", description: "Pinterest's data platform evolution. Migration from HBase to TiDB, real-time indexing, and handling 1B+ pins.", url: "https://medium.com/pinterest-engineering/", source: "Pinterest", tags: ["Migration", "TiDB", "Real-Time"] },
      { title: "How CockroachDB Handles Distributed Transactions", description: "CockroachDB's distributed transaction implementation. MVCC, hybrid-logical clocks, and serializable isolation across regions.", url: "https://www.cockroachlabs.com/blog/", source: "Cockroach Labs", tags: ["Transactions", "MVCC", "Distributed"] },
      { title: "How PlanetScale Built Their Database Platform", description: "PlanetScale's serverless MySQL platform. Vitess-based sharding, database branching, and non-blocking schema changes.", url: "https://planetscale.com/blog", source: "PlanetScale", tags: ["Vitess", "Branching", "Serverless"] },
    ]
  },
  /* ========= System Design — More Topics ========= */
  {
    category: "system-design", type: "ebook",
    entries: [
      { title: "The Google File System — Paper", description: "Original paper on GFS. Chunk-based storage, master-chunkserver architecture, and fault tolerance in distributed file systems.", url: "https://research.google/pubs/pub51/", source: "Google", tags: ["GFS", "Distributed", "Paper"] },
      { title: "MapReduce — Simplified Data Processing", description: "The foundational paper on MapReduce. Programming model for large-scale data processing on commodity clusters.", url: "https://research.google/pubs/pub62/", source: "Google", tags: ["MapReduce", "Big Data", "Paper"] },
      { title: "Dynamo — Amazon's Key-Value Store Paper", description: "Amazon's Dynamo paper. Eventually consistent key-value store, vector clocks, gossip protocol, and consistent hashing.", url: "https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf", source: "Amazon", tags: ["Dynamo", "Eventually Consistent", "Paper"] },
      { title: "CAP Theorem — Explained", description: "Comprehensive explanation of the CAP theorem. Consistency, availability, partition tolerance, and real-world trade-offs.", url: "https://blog.bytebytego.com/", source: "ByteByteGo", tags: ["CAP", "Trade-offs", "Distributed"] },
      { title: "DDIA — Designing Data-Intensive Applications", description: "Martin Kleppmann's modern classic on data systems. Replication, partitioning, transactions, stream and batch processing.", url: "https://dataintensive.net/", source: "Martin Kleppmann", tags: ["DDIA", "Classic", "Comprehensive"] },
    ]
  },
  {
    category: "system-design", type: "case-study",
    entries: [
      { title: "How Dropbox Stores Billions of Files", description: "Dropbox's Magic Pocket storage system. Custom-built block storage, data durability, and serving petabytes of user data.", url: "https://dropbox.tech/", source: "Dropbox", tags: ["Storage", "Magic Pocket", "Durability"] },
      { title: "How WhatsApp Delivers Messages in Real-Time", description: "WhatsApp's message delivery infrastructure. XMPP protocol, message queuing, presence management, and end-to-end encryption.", url: "https://engineering.fb.com/", source: "Meta", tags: ["Messaging", "Real-Time", "E2E"] },
      { title: "How Google Search Works", description: "Google's search infrastructure. Web crawling, indexing, PageRank, query processing, and serving results in milliseconds.", url: "https://www.google.com/search/howsearchworks/", source: "Google", tags: ["Search", "PageRank", "Indexing"] },
      { title: "How Facebook Handles Media Uploads", description: "Facebook's media upload pipeline. Image resizing, video transcoding, CDN distribution, and handling billions of uploads daily.", url: "https://engineering.fb.com/", source: "Meta", tags: ["Media", "Upload", "CDN"] },
      { title: "How Slack Achieves 99.99% Uptime", description: "Slack's reliability engineering. Multi-region architecture, automated failover, chaos engineering, and incident response.", url: "https://slack.engineering/", source: "Slack", tags: ["Uptime", "Reliability", "Multi-Region"] },
    ]
  },
  /* ========= Security — More Tools ========= */
  {
    category: "security", type: "course",
    entries: [
      { title: "PortSwigger Web Security Academy", description: "Free, online web security training. Covers SQL injection, XSS, CSRF, SSRF, and advanced attacks with hands-on labs.", url: "https://portswigger.net/web-security", source: "PortSwigger", tags: ["Web Security", "Labs", "Free"] },
      { title: "HackTheBox — Cybersecurity Training", description: "Hands-on cybersecurity training platform. Virtual machines for penetration testing, CTF challenges, and certification paths.", url: "https://www.hackthebox.com/", source: "HackTheBox", tags: ["Pen Testing", "CTF", "Hands-on"] },
      { title: "TryHackMe — Learn Cybersecurity", description: "Guided cybersecurity learning platform. Browser-based VMs, structured learning paths, and beginner-friendly content.", url: "https://tryhackme.com/", source: "TryHackMe", tags: ["Learning", "Guided", "Beginner"] },
      { title: "SANS Cyber Aces — Free Security Course", description: "Free cybersecurity fundamentals course. Linux, networking, and system administration for security practitioners.", url: "https://www.cyberaces.org/", source: "SANS", tags: ["Fundamentals", "Linux", "Free"] },
    ]
  },
  /* ========= Data Science — More Tools ========= */
  {
    category: "data-science", type: "ebook",
    entries: [
      { title: "Python Data Science Handbook", description: "Jake VanderPlas's comprehensive guide. NumPy, Pandas, Matplotlib, Scikit-Learn with practical examples and clear explanations.", url: "https://jakevdp.github.io/PythonDataScienceHandbook/", source: "Jake VanderPlas", tags: ["Python", "Handbook", "Comprehensive"] },
      { title: "Think Stats — Probability and Statistics", description: "Introduction to probability and statistics for Python programmers. Exploratory data analysis with computational approach.", url: "https://greenteapress.com/thinkstats2/html/", source: "Allen Downey", tags: ["Statistics", "Probability", "Python"] },
      { title: "An Introduction to Statistical Learning", description: "Free statistical learning textbook. Regression, classification, resampling, tree-based methods, and unsupervised learning.", url: "https://www.statlearning.com/", source: "Springer", tags: ["Statistical Learning", "Free", "Textbook"] },
      { title: "R for Data Science — Free Book", description: "Hadley Wickham's guide to data science with R. Data import, tidy data, visualization with ggplot2, and modeling.", url: "https://r4ds.had.co.nz/", source: "Hadley Wickham", tags: ["R", "Tidyverse", "Free"] },
    ]
  },
  /* ========= Mobile — More Tools ========= */
  {
    category: "mobile", type: "github",
    entries: [
      { title: "Jetpack Compose — Modern Android UI", description: "Google's modern toolkit for building native Android UI. Declarative, less code, powerful tools, and Kotlin-first APIs.", url: "https://github.com/androidx/androidx", source: "Google", tags: ["Compose", "Declarative", "Kotlin"] },
      { title: "Rive — Interactive Animations", description: "Design and ship interactive animations to any platform. State machines, blend states, and runtime APIs for iOS, Android, Web.", url: "https://github.com/rive-app/rive-flutter", source: "Rive", tags: ["Animation", "State Machine", "Cross-Platform"] },
      { title: "The Composable Architecture — Swift", description: "Architecture library for building applications in a consistent and understandable way. State, actions, reducers, and effects.", url: "https://github.com/pointfreeco/swift-composable-architecture", source: "Point-Free", tags: ["Architecture", "Swift", "Redux-Like"] },
      { title: "MMKV — Ultra-Fast KV Storage", description: "High-performance key-value storage framework by WeChat. Memory-mapped files, type-safe API, and multi-process support.", url: "https://github.com/Tencent/MMKV", source: "Tencent", tags: ["Storage", "KV", "Fast"] },
    ]
  },
  /* ========= Cloud — More Topics ========= */
  {
    category: "cloud", type: "case-study",
    entries: [
      { title: "How Netflix Runs on AWS", description: "Netflix's complete AWS infrastructure. Auto-scaling, multi-region deployment, and how they handle 400M+ hours of streaming monthly.", url: "https://netflixtechblog.com/", source: "Netflix", tags: ["AWS", "Streaming", "Multi-Region"] },
      { title: "How Pinterest Migrated to AWS", description: "Pinterest's cloud migration strategy. Moving from self-managed data centers to AWS while serving 480M monthly users.", url: "https://medium.com/pinterest-engineering/", source: "Pinterest", tags: ["Migration", "AWS", "Scale"] },
      { title: "How Dropbox Moved Away from AWS", description: "Dropbox's reverse cloud migration. Building their own infrastructure, Magic Pocket storage, and saving $75M over 2 years.", url: "https://dropbox.tech/", source: "Dropbox", tags: ["On-Prem", "Cost", "Custom"] },
      { title: "How Alibaba Cloud Handles Singles Day", description: "Alibaba's cloud infrastructure during Singles Day. Processing 583K orders per second and handling the world's largest sales event.", url: "https://www.alibabacloud.com/blog", source: "Alibaba Cloud", tags: ["Singles Day", "Scale", "Peak"] },
    ]
  },
  /* ========= Dart/Flutter — More Resources ========= */
  {
    category: "dart", type: "case-study",
    entries: [
      { title: "How Google Pay Uses Flutter", description: "Google Pay's adoption of Flutter for their cross-platform payment app. Code sharing, performance optimization, and platform integration.", url: "https://flutter.dev/showcase", source: "Google", tags: ["Payments", "Cross-Platform", "Google"] },
      { title: "How BMW Uses Flutter for Car Interfaces", description: "BMW's Flutter-based in-car experience. Embedded Flutter, custom rendering, and integration with vehicle hardware systems.", url: "https://flutter.dev/showcase", source: "BMW", tags: ["Automotive", "Embedded", "In-Car"] },
      { title: "How Tencent Migrated to Flutter", description: "Tencent's large-scale Flutter adoption. Migrating multiple apps, custom engine modifications, and serving billions of users.", url: "https://flutter.dev/showcase", source: "Tencent", tags: ["Migration", "Scale", "Custom Engine"] },
    ]
  },
  /* ========= Kotlin — More Resources ========= */
  {
    category: "kotlin", type: "case-study",
    entries: [
      { title: "How Google Uses Kotlin for Android", description: "Google's Kotlin-first approach for Android. Benefits of Kotlin over Java, migration strategies, and Jetpack compatibility.", url: "https://developer.android.com/kotlin", source: "Google", tags: ["Android", "Kotlin-First", "Jetpack"] },
      { title: "How Netflix Uses Kotlin for Backend", description: "Netflix's adoption of Kotlin for backend services. Coroutines for async, Spring Boot integration, and developer productivity.", url: "https://netflixtechblog.com/", source: "Netflix", tags: ["Backend", "Coroutines", "Spring"] },
      { title: "How Uber Uses Kotlin Multiplatform", description: "Uber's use of KMP for sharing business logic. Shared networking, analytics, and reducing team duplication across platforms.", url: "https://www.uber.com/blog/", source: "Uber", tags: ["KMP", "Shared Logic", "Networking"] },
    ]
  },
  /* ========= Rust — More Resources ========= */
  {
    category: "rust", type: "ebook",
    entries: [
      { title: "The Rust Programming Language — Free Book", description: "The official Rust book. Ownership, borrowing, lifetimes, traits, generics, fearless concurrency, and building real projects.", url: "https://doc.rust-lang.org/book/", source: "Rust Foundation", tags: ["Official", "Ownership", "Comprehensive"] },
      { title: "Rust Design Patterns — Free Book", description: "Collection of Rust design patterns and idioms. Builder pattern, type state, newtype, and Rust-specific best practices.", url: "https://rust-unofficial.github.io/patterns/", source: "Community", tags: ["Patterns", "Idioms", "Best Practices"] },
      { title: "Zero To Production In Rust", description: "Build a production-ready API in Rust. Actix Web, testing, CI/CD, observability, and deployment best practices.", url: "https://www.zero2prod.com/", source: "Luca Palmieri", tags: ["Production", "API", "Actix Web"] },
    ]
  },
  /* ========= System Design — Architecture Patterns ========= */
  {
    category: "system-design", type: "course",
    entries: [
      { title: "ByteByteGo — System Design Course", description: "Alex Xu's comprehensive system design course. Visual explanations, real-world examples, and interview preparation.", url: "https://bytebytego.com/", source: "ByteByteGo", tags: ["Visual", "Comprehensive", "Interview"] },
      { title: "CMU 15-213 — Computer Systems", description: "Carnegie Mellon's foundational systems course. Data representation, machine code, memory hierarchy, and concurrent programming.", url: "https://www.cs.cmu.edu/~213/", source: "CMU", tags: ["Systems", "Memory", "Concurrency"] },
      { title: "Princeton COS 418 — Distributed Systems", description: "Princeton's distributed systems course. Consensus, replication, fault tolerance, and building distributed applications.", url: "https://www.cs.princeton.edu/courses/archive/fall22/cos418/", source: "Princeton", tags: ["Distributed", "Consensus", "Replication"] },
    ]
  },
  /* ========= More Cloud ========= */
  {
    category: "cloud", type: "course",
    entries: [
      { title: "AWS Solutions Architect Certification", description: "Prepare for the AWS Solutions Architect exam. VPC, EC2, S3, RDS, Lambda, CloudFormation, and architecture best practices.", url: "https://aws.amazon.com/certification/certified-solutions-architect-associate/", source: "AWS", tags: ["Certification", "Architecture", "AWS"] },
      { title: "Google Cloud Associate Engineer", description: "Prepare for the GCP Associate Cloud Engineer exam. Compute Engine, GKE, BigQuery, IAM, and cloud deployment.", url: "https://cloud.google.com/learn/certification/cloud-engineer", source: "Google Cloud", tags: ["Certification", "GCP", "Engineer"] },
      { title: "Azure Fundamentals — AZ-900", description: "Microsoft Azure fundamentals certification. Cloud concepts, Azure services, security, pricing, and SLA agreements.", url: "https://learn.microsoft.com/en-us/certifications/azure-fundamentals/", source: "Microsoft", tags: ["Certification", "Azure", "Fundamentals"] },
    ]
  },
  /* ========= More Databases ========= */
  {
    category: "databases", type: "ebook",
    entries: [
      { title: "PostgreSQL: Up and Running", description: "Comprehensive guide to PostgreSQL administration and development. Indexes, full-text search, PostGIS, and advanced SQL features.", url: "https://www.oreilly.com/library/view/postgresql-up-and/9781491963401/", source: "O'Reilly", tags: ["PostgreSQL", "Admin", "Guide"] },
      { title: "Redis in Action", description: "Complete guide to Redis. Data structures, pub/sub, Lua scripting, cluster mode, and building real applications.", url: "https://redis.io/docs/", source: "Redis", tags: ["Redis", "Data Structures", "Practical"] },
      { title: "MongoDB: The Definitive Guide", description: "Complete reference for MongoDB. Document model, aggregation framework, sharding, replication, and schema design patterns.", url: "https://www.mongodb.com/docs/", source: "MongoDB", tags: ["MongoDB", "Document", "Schema Design"] },
    ]
  },
];

function generateResources(): Resource[] {
  const all: Resource[] = [];
  for (const group of GENERATED_POOL) {
    for (const entry of group.entries) {
      all.push({
        ...entry,
        type: group.type,
        category: group.category as Resource["category"],
      });
    }
  }
  return all;
}

const ALL_EXTRA_RESOURCES: Resource[] = [...EXTRA_RESOURCES, ...generateResources()];

export default ALL_EXTRA_RESOURCES;

