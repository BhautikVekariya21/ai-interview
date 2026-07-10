export interface SystemDesignProblem {
  id: number;
  title: string;
  company: string[];
  difficulty: "Medium" | "Hard" | "Expert";
  estimatedTime: string;
  description: string;
  requirements: {
    functional: string[];
    nonFunctional: string[];
  };
  highLevelDesign: {
    components: string[];
    diagram: string; // ASCII-art style description
  };
  deepDive: {
    title: string;
    content: string;
  }[];
  bottlenecks: string[];
  scaling: string[];
  keyTakeaways: string[];
}

export const SYSTEM_DESIGN_PROBLEMS: SystemDesignProblem[] = [
  {
    id: 1,
    title: "Design a URL Shortener (TinyURL)",
    company: ["Google", "Meta", "Microsoft"],
    difficulty: "Medium",
    estimatedTime: "35 min",
    description:
      "Design a service that takes long URLs and creates short, unique aliases for them. Users can visit the short URL and be redirected to the original.",
    requirements: {
      functional: [
        "Given a URL, generate a short and unique alias",
        "When a short URL is accessed, redirect to the original URL",
        "Links can have a configurable expiration time",
        "Users can create custom short URLs",
      ],
      nonFunctional: [
        "System should be highly available",
        "URL redirection should be real-time with minimal latency",
        "Shortened links should not be predictable",
      ],
    },
    highLevelDesign: {
      components: [
        "API Gateway / Load Balancer",
        "Application Servers",
        "Key Generation Service (KGS)",
        "Database (NoSQL – e.g. DynamoDB)",
        "Cache (Redis) for hot URLs",
        "Analytics Service",
      ],
      diagram:
        "Client → LB → App Server → KGS (pre-generated keys) → DB\n                                  ↘ Cache (Redis) for reads",
    },
    deepDive: [
      {
        title: "Key Generation Strategy",
        content:
          "Use Base62 encoding (a-z, A-Z, 0-9) for 6-char keys, yielding ~56 billion unique URLs. A Key Generation Service pre-generates keys and stores them in a key-DB. App servers request a batch of keys from KGS, ensuring uniqueness without collision.",
      },
      {
        title: "Database Schema",
        content:
          "Primary table: shortUrl (PK), longUrl, userId, createdAt, expireAt. Use a NoSQL store for horizontal scalability. Partition by hash of shortUrl for even distribution.",
      },
      {
        title: "Caching Strategy",
        content:
          "Cache frequently accessed URLs in Redis (LRU eviction). 80/20 rule: 20% of URLs generate 80% of traffic. Cache those 20% to significantly reduce DB load.",
      },
    ],
    bottlenecks: [
      "Write-heavy during viral campaigns",
      "Cache invalidation on URL expiry",
      "Key exhaustion in KGS under extreme load",
    ],
    scaling: [
      "Database sharding by hash of short URL",
      "Multiple KGS instances with non-overlapping key ranges",
      "CDN for geographic distribution of redirects",
      "Rate limiting to prevent abuse",
    ],
    keyTakeaways: [
      "Pre-generation avoids collision at write time",
      "Base62 gives compact, URL-safe keys",
      "Cache read-heavy workloads aggressively",
      "NoSQL for horizontal scale",
    ],
  },
  {
    id: 2,
    title: "Design Twitter / News Feed",
    company: ["Meta", "Google", "Amazon"],
    difficulty: "Hard",
    estimatedTime: "45 min",
    description:
      "Design a social media feed system where users can post tweets, follow others, and see a personalized timeline of recent posts from people they follow.",
    requirements: {
      functional: [
        "Users can post new tweets (text, media)",
        "Users can follow/unfollow other users",
        "Users see a home timeline of recent tweets from followed users",
        "Tweets can be liked, retweeted, and replied to",
      ],
      nonFunctional: [
        "Timeline generation should be fast (< 200ms)",
        "System should handle 500M+ users",
        "Eventual consistency is acceptable for the feed",
        "High availability over strong consistency",
      ],
    },
    highLevelDesign: {
      components: [
        "API Gateway / Load Balancer",
        "Tweet Service (write path)",
        "Fan-out Service",
        "Timeline Service (read path)",
        "User Service & Graph DB",
        "Media Storage (S3/CDN)",
        "Cache (Redis) for timelines",
        "Message Queue (Kafka)",
      ],
      diagram:
        "Post Tweet → Tweet Service → Kafka → Fan-out Service → Push to follower timelines (Redis)\nRead Feed → Timeline Service → Redis cache → Merge & Rank",
    },
    deepDive: [
      {
        title: "Fan-out on Write vs. Read",
        content:
          "Fan-out on Write: When a user posts, push the tweet to all followers' timeline caches. Fast reads but expensive for users with millions of followers (celebrities). Fan-out on Read: Assemble the timeline at read time by querying tweets from followed users. For a hybrid approach: fan-out on write for normal users, fan-out on read for celebrities.",
      },
      {
        title: "Timeline Ranking",
        content:
          "Rank tweets by a combination of recency, engagement score, user affinity, and content relevance. An ML-based ranking model can be applied at read time after fetching candidate tweets.",
      },
      {
        title: "Data Storage",
        content:
          "Tweets table: tweetId, authorId, content, mediaUrl, timestamp. Timeline cache: userId → sorted set of tweetIds (Redis ZSET by timestamp). User graph: follow relationships stored in a graph DB or adjacency list in a relational DB.",
      },
    ],
    bottlenecks: [
      "Celebrity fan-out (millions of followers)",
      "Hot partition for trending tweets",
      "Timeline cache memory for 500M users",
    ],
    scaling: [
      "Hybrid fan-out (write for normal, read for celebrities)",
      "Shard timelines by userId",
      "CDN for media delivery",
      "Kafka for async fan-out processing",
    ],
    keyTakeaways: [
      "Fan-out trade-off is the core design decision",
      "Hybrid approach balances write cost and read latency",
      "Redis ZSET is perfect for ranked timelines",
      "Eventually consistent reads are acceptable",
    ],
  },
  {
    id: 3,
    title: "Design a Chat System (WhatsApp)",
    company: ["Meta", "Google", "Microsoft"],
    difficulty: "Hard",
    estimatedTime: "45 min",
    description:
      "Design a real-time messaging system supporting 1-on-1 and group chats with delivery receipts, online status, and message history.",
    requirements: {
      functional: [
        "1-on-1 messaging with real-time delivery",
        "Group chats (up to 256 members)",
        "Message delivery status (sent, delivered, read)",
        "Online/last-seen status",
        "Media sharing (images, files)",
      ],
      nonFunctional: [
        "Low latency message delivery (< 100ms)",
        "Message ordering guarantee within a conversation",
        "High availability with minimal message loss",
        "End-to-end encryption",
      ],
    },
    highLevelDesign: {
      components: [
        "WebSocket Gateway (per-connection state)",
        "Chat Service (message routing)",
        "Message Queue (Kafka / RabbitMQ)",
        "Presence Service (online status)",
        "Message Store (Cassandra)",
        "Media Service (S3 + CDN)",
        "Push Notification Service",
      ],
      diagram:
        "User A ↔ WebSocket Gateway ↔ Chat Service ↔ Kafka ↔ WebSocket Gateway ↔ User B\n                                            ↓\n                                    Cassandra (persist)",
    },
    deepDive: [
      {
        title: "WebSocket Connection Management",
        content:
          "Each user maintains a persistent WebSocket connection. A Connection Manager maps userId → WebSocket server. When a message arrives, the Chat Service queries the Connection Manager to find the recipient's server and routes the message.",
      },
      {
        title: "Message Ordering & ID Generation",
        content:
          "Use a Snowflake-like ID generator: timestamp + machineId + sequence. This gives globally unique, roughly time-ordered IDs. Within a conversation, messages are ordered by this ID.",
      },
      {
        title: "Group Messaging",
        content:
          "For group messages, the Chat Service publishes to a group topic in Kafka. Each member's WebSocket server subscribes to relevant group topics. For large groups, fan-out through the message queue avoids connection-level fan-out.",
      },
    ],
    bottlenecks: [
      "WebSocket server memory with millions of connections",
      "Group message fan-out for large groups",
      "Presence updates at scale (millions of online users)",
    ],
    scaling: [
      "Consistent hashing for WebSocket server assignment",
      "Cassandra partitioned by conversationId",
      "Presence service with heartbeat + TTL in Redis",
      "Region-based deployment for latency",
    ],
    keyTakeaways: [
      "WebSockets are essential for real-time bidirectional communication",
      "Message queues decouple senders from receivers",
      "Snowflake IDs solve ordering without coordination",
      "Separate presence from messaging for scalability",
    ],
  },
  {
    id: 4,
    title: "Design a Rate Limiter",
    company: ["Google", "Amazon", "Netflix"],
    difficulty: "Medium",
    estimatedTime: "30 min",
    description:
      "Design a rate limiter that throttles requests based on configurable rules (e.g. 100 requests per minute per user).",
    requirements: {
      functional: [
        "Limit requests per user/IP/API key",
        "Configurable rate (e.g. 100/min, 1000/hour)",
        "Return appropriate HTTP 429 when throttled",
        "Support different rules per API endpoint",
      ],
      nonFunctional: [
        "Low latency (must not add significant overhead)",
        "Distributed — works across multiple servers",
        "Highly available (failing open is preferable to blocking all)",
        "Accurate counting even under high concurrency",
      ],
    },
    highLevelDesign: {
      components: [
        "Rate Limiter Middleware (API Gateway)",
        "Rules Engine (configuration)",
        "Redis (distributed counter store)",
        "Monitoring & Alerting",
      ],
      diagram:
        "Client → API Gateway → Rate Limiter Middleware → (Check Redis) → Backend Service\n                                              ↓ 429 if throttled",
    },
    deepDive: [
      {
        title: "Token Bucket Algorithm",
        content:
          "Each user has a bucket with capacity N tokens. Tokens refill at rate R per second. Each request consumes one token. If no tokens remain, the request is throttled. Store {tokens, last_refill_timestamp} per user in Redis. On each request: calculate tokens to add based on elapsed time, deduct one, update atomically.",
      },
      {
        title: "Sliding Window Log",
        content:
          "Store timestamps of all requests in a sorted set. For each new request, remove entries older than the window, count remaining, and reject if count > limit. More accurate than fixed windows but uses more memory.",
      },
      {
        title: "Distributed Rate Limiting",
        content:
          "Use Redis with Lua scripts for atomic check-and-update. For multi-region, use local rate limiters with a global sync (slightly over-counting is acceptable). Race conditions are handled by Redis single-threaded execution.",
      },
    ],
    bottlenecks: [
      "Redis hotspot for high-traffic users",
      "Clock synchronization in distributed environments",
      "Memory for storing per-user state at scale",
    ],
    scaling: [
      "Redis cluster with hash-based sharding by userId",
      "Local in-memory limiter + periodic sync for ultra-low latency",
      "Fail-open strategy when Redis is unavailable",
    ],
    keyTakeaways: [
      "Token bucket is the most common and flexible algorithm",
      "Redis + Lua scripts enable atomic distributed operations",
      "Always have a fail-open strategy for availability",
      "Place rate limiter at the API gateway layer",
    ],
  },
  {
    id: 5,
    title: "Design YouTube / Video Streaming",
    company: ["Google", "Netflix", "Amazon"],
    difficulty: "Hard",
    estimatedTime: "45 min",
    description:
      "Design a video sharing and streaming platform supporting upload, transcoding, storage, and adaptive bitrate playback.",
    requirements: {
      functional: [
        "Users can upload videos",
        "Videos are transcoded into multiple resolutions",
        "Adaptive bitrate streaming for playback",
        "Search and recommendation feed",
        "Like, comment, subscribe functionality",
      ],
      nonFunctional: [
        "Smooth playback with minimal buffering",
        "Handle millions of concurrent viewers",
        "Cost-efficient storage for petabytes of video",
        "Fast upload-to-playback pipeline",
      ],
    },
    highLevelDesign: {
      components: [
        "Upload Service (chunked upload)",
        "Transcoding Pipeline (workers)",
        "Object Storage (S3)",
        "CDN (CloudFront)",
        "Metadata Service (MySQL/DynamoDB)",
        "Search Service (Elasticsearch)",
        "Recommendation Engine",
      ],
      diagram:
        "Upload → Upload Service → S3 (raw) → Transcoding Queue → Workers → S3 (processed) → CDN\nPlayback → CDN edge → manifest file → adaptive chunks",
    },
    deepDive: [
      {
        title: "Video Transcoding Pipeline",
        content:
          "Split the uploaded video into segments. Transcode each segment into multiple resolutions (360p, 720p, 1080p, 4K) and codecs (H.264, VP9, AV1). Generate a manifest file (HLS/DASH) that lists available quality levels. Workers pull jobs from a queue (SQS/Kafka).",
      },
      {
        title: "Adaptive Bitrate Streaming",
        content:
          "The player starts with a low-quality segment, then measures bandwidth. Based on network conditions, the player requests higher or lower quality segments using the manifest file. This is handled by HLS (m3u8 playlist) or DASH (MPD manifest).",
      },
      {
        title: "CDN & Caching",
        content:
          "Popular videos are cached at CDN edge locations globally. Long-tail content is served from origin. Pre-warm CDN caches for trending content. Use multi-tier caching: edge → regional → origin.",
      },
    ],
    bottlenecks: [
      "Transcoding latency for upload-to-playback time",
      "Storage costs for multiple quality levels per video",
      "CDN cache miss thundering herd for viral videos",
    ],
    scaling: [
      "Parallel segment transcoding across worker fleet",
      "Tiered storage (hot/warm/cold) for cost optimization",
      "CDN pre-warming for trending content",
      "Chunked upload with resume capability",
    ],
    keyTakeaways: [
      "Transcoding is the critical pipeline — parallelize it",
      "HLS/DASH manifests enable adaptive quality",
      "CDN is essential — most reads hit the edge",
      "Separate hot and cold storage for cost",
    ],
  },
  {
    id: 6,
    title: "Design Uber / Ride-Sharing",
    company: ["Uber", "Google", "Amazon"],
    difficulty: "Hard",
    estimatedTime: "45 min",
    description:
      "Design a ride-sharing service that matches riders with nearby drivers in real-time, handles trip management, and supports pricing.",
    requirements: {
      functional: [
        "Riders request rides with pickup/dropoff locations",
        "Match riders with nearby available drivers",
        "Real-time driver location tracking",
        "Trip management (start, in-progress, complete)",
        "Dynamic pricing (surge)",
        "Payment processing",
      ],
      nonFunctional: [
        "Match a rider to a driver in < 10 seconds",
        "Handle millions of concurrent location updates",
        "High availability (99.99% for matching)",
        "Accurate ETA calculations",
      ],
    },
    highLevelDesign: {
      components: [
        "API Gateway",
        "Matching Service",
        "Location Service (real-time tracking)",
        "Trip Service",
        "Pricing Service",
        "Payment Service",
        "Geospatial Index (QuadTree / GeoHash)",
        "Message Queue (Kafka)",
        "Database (rides: SQL, locations: Redis)",
      ],
      diagram:
        "Rider Request → API → Matching Service → Query Location Service (QuadTree) → Find nearby drivers\n                                     ↓\n                              Push notification to driver → Accept/Reject\nDriver Location → Location Service → Redis (GeoHash) → Update every 3s",
    },
    deepDive: [
      {
        title: "Geospatial Indexing",
        content:
          "Use GeoHash or QuadTree to index driver locations. GeoHash converts (lat, lng) into a string prefix — nearby locations share prefixes. Query by prefix to find drivers within a radius. Redis GEO commands provide built-in geospatial queries.",
      },
      {
        title: "Matching Algorithm",
        content:
          "Find all available drivers within a radius (e.g. 5km). Rank by distance, ETA, driver rating, and accept rate. Send the ride request to the best match. If declined, send to the next. Timeout after N seconds and expand the search radius.",
      },
      {
        title: "Dynamic Pricing (Surge)",
        content:
          "Monitor supply (available drivers) and demand (ride requests) per geographic cell. When demand/supply ratio exceeds a threshold, apply a surge multiplier. Update pricing every few minutes. Smooth transitions to avoid price shock.",
      },
    ],
    bottlenecks: [
      "Millions of driver location updates per second",
      "Hot geographic areas (city centers, airports)",
      "Matching latency during surge periods",
    ],
    scaling: [
      "Shard location data by GeoHash region",
      "Ring buffer in Redis for location history",
      "Separate read/write paths for location service",
      "Stateless matching with cached driver pools",
    ],
    keyTakeaways: [
      "GeoHash/QuadTree is the core data structure",
      "Redis GEO commands simplify geospatial queries",
      "Separate matching, location, and trip services",
      "Dynamic pricing = supply/demand ratio per cell",
    ],
  },
  {
    id: 7,
    title: "Design a Web Crawler",
    company: ["Google", "Microsoft", "Amazon"],
    difficulty: "Medium",
    estimatedTime: "35 min",
    description:
      "Design a web crawler that systematically discovers and downloads web pages for indexing by a search engine.",
    requirements: {
      functional: [
        "Crawl the web starting from seed URLs",
        "Extract and follow links from downloaded pages",
        "Store page content for indexing",
        "Respect robots.txt and crawl delays",
        "Handle duplicate URL detection",
      ],
      nonFunctional: [
        "Crawl billions of pages efficiently",
        "Politeness — don't overwhelm any single domain",
        "Scalability — horizontally scalable crawler fleet",
        "Fault tolerance — resume after crashes",
      ],
    },
    highLevelDesign: {
      components: [
        "URL Frontier (priority queue of URLs to crawl)",
        "Fetcher (HTTP downloader)",
        "DNS Resolver (with cache)",
        "Content Parser (extract links, text)",
        "URL Dedup Service (Bloom filter)",
        "Content Store (distributed filesystem)",
        "Politeness Enforcer (per-domain rate limiter)",
      ],
      diagram:
        "Seed URLs → URL Frontier → Fetcher → Parser → Extract links → Dedup → URL Frontier (loop)\n                                         ↓\n                                Content Store → Indexer",
    },
    deepDive: [
      {
        title: "URL Frontier Design",
        content:
          "Two-queue architecture: a 'front queue' for priority (PageRank, freshness) and a 'back queue' for politeness (one queue per domain, rate-limited). The front queue feeds URLs into the appropriate back queue. Workers pull from back queues respecting per-domain delays.",
      },
      {
        title: "Deduplication",
        content:
          "URL dedup: use a Bloom filter for approximate membership testing (very memory efficient for billions of URLs). Content dedup: compute a fingerprint (SimHash) of page content to detect near-duplicate pages. Store fingerprints in a lookup service.",
      },
      {
        title: "Politeness & robots.txt",
        content:
          "Before crawling a domain, fetch and cache its robots.txt. Enforce a minimum delay between requests to the same domain (e.g. 1 second). Use a per-domain token bucket to regulate request rate.",
      },
    ],
    bottlenecks: [
      "DNS resolution at scale (cache aggressively)",
      "URL frontier memory for billions of pending URLs",
      "Handling spider traps (infinite URL generation)",
    ],
    scaling: [
      "Partition URL frontier by domain hash",
      "Distributed fetcher fleet with consistent hashing",
      "Blob storage for raw pages, metadata in DB",
      "Checkpoint/resume for fault tolerance",
    ],
    keyTakeaways: [
      "URL Frontier is the heart of the crawler",
      "Bloom filters enable scalable deduplication",
      "Politeness is a hard requirement, not optional",
      "Two-queue frontier separates priority from politeness",
    ],
  },
  {
    id: 8,
    title: "Design a Notification System",
    company: ["Meta", "Amazon", "Apple"],
    difficulty: "Medium",
    estimatedTime: "35 min",
    description:
      "Design a scalable notification system supporting push notifications, SMS, and email with user preferences and delivery tracking.",
    requirements: {
      functional: [
        "Send push, SMS, and email notifications",
        "User preference management (opt-in/out per channel)",
        "Rate limiting (no notification spam)",
        "Template management for notification content",
        "Delivery tracking and analytics",
      ],
      nonFunctional: [
        "Deliver notifications within seconds",
        "Handle millions of notifications per day",
        "At-least-once delivery guarantee",
        "Graceful degradation if one channel is down",
      ],
    },
    highLevelDesign: {
      components: [
        "API / Event Trigger",
        "Notification Service (orchestrator)",
        "User Preference Store",
        "Template renderer",
        "Message Queues (per channel)",
        "Push Provider (APNs, FCM)",
        "SMS Provider (Twilio)",
        "Email Provider (SES)",
        "Delivery Tracker (analytics DB)",
      ],
      diagram:
        "Event → Notification Service → Check Preferences → Render Template → Route to Channel Queue\n                                                                            ↓\n                                                                    Push / SMS / Email Workers → Provider APIs → Delivery Tracker",
    },
    deepDive: [
      {
        title: "Message Queue Architecture",
        content:
          "Use separate queues per channel (push, SMS, email) for independent scaling and failure isolation. Each queue has dedicated workers that call the respective provider API. Dead-letter queues capture failed deliveries for retry.",
      },
      {
        title: "Delivery Guarantees",
        content:
          "Use idempotency keys to prevent duplicate notifications. Workers acknowledge messages only after successful delivery. Implement exponential backoff for retries. Track delivery status: queued → sent → delivered → read.",
      },
      {
        title: "Rate Limiting & Batching",
        content:
          "Rate limit per user (e.g. max 5 push per hour) and per template (e.g. max 1 promo per day). Batch similar notifications (e.g. '3 new comments' instead of 3 separate notifications). Use a digest mode for low-priority notifications.",
      },
    ],
    bottlenecks: [
      "Provider rate limits (APNs, FCM, Twilio)",
      "Notification storms from viral events",
      "Preferences lookup latency at scale",
    ],
    scaling: [
      "Channel-specific queues for independent scaling",
      "Cache user preferences in Redis",
      "Multi-provider failover (e.g. Twilio → Nexmo)",
      "Priority queues for urgent vs. marketing notifications",
    ],
    keyTakeaways: [
      "Separate queues per channel for isolation",
      "Rate limiting prevents user notification fatigue",
      "Idempotency keys prevent duplicate sends",
      "Dead-letter queues are essential for reliability",
    ],
  },
  {
    id: 9,
    title: "Design a Key-Value Store (Redis-like)",
    company: ["Amazon", "Google", "Meta"],
    difficulty: "Hard",
    estimatedTime: "45 min",
    description:
      "Design a distributed key-value store that supports get/put operations with high availability, partition tolerance, and tunable consistency.",
    requirements: {
      functional: [
        "put(key, value) — store a key-value pair",
        "get(key) — retrieve a value by key",
        "delete(key) — remove a key-value pair",
        "Support for TTL (time-to-live)",
      ],
      nonFunctional: [
        "High availability (AP in CAP theorem)",
        "Eventual consistency with tunable quorum",
        "Low latency reads and writes (< 10ms)",
        "Horizontal scalability to petabyte scale",
      ],
    },
    highLevelDesign: {
      components: [
        "Client Library (consistent hashing ring)",
        "Coordinator Node",
        "Storage Nodes (with local storage engine)",
        "Gossip Protocol (failure detection)",
        "Merkle Trees (anti-entropy sync)",
        "Write-Ahead Log",
        "Compaction (SSTables / LSM tree)",
      ],
      diagram:
        "Client → Coordinator → Hash Ring → Responsible Node(s)\n                                    ↓\n                   Write to W replicas → Return success\n                   Read from R replicas → Return latest (quorum)",
    },
    deepDive: [
      {
        title: "Consistent Hashing & Partitioning",
        content:
          "Place nodes on a hash ring. Each key maps to the first node clockwise from its hash position. Use virtual nodes (vnodes) for even distribution. When nodes join/leave, only adjacent keys are redistributed.",
      },
      {
        title: "Replication & Quorum",
        content:
          "Replicate each key to N successive nodes on the ring (e.g. N=3). Write quorum W: wait for W successful writes. Read quorum R: read from R replicas and return the latest version. W + R > N ensures strong consistency; W + R ≤ N gives higher availability with eventual consistency.",
      },
      {
        title: "Conflict Resolution",
        content:
          "Use vector clocks to track causality. When conflicting versions are detected, either last-write-wins (LWW) by timestamp or return all versions to the client for application-level resolution (shopping cart pattern).",
      },
    ],
    bottlenecks: [
      "Hot keys (celebrity profiles, config keys)",
      "Network partitions causing divergent replicas",
      "Compaction storms during heavy writes",
    ],
    scaling: [
      "Virtual nodes for balanced distribution",
      "Hinted handoff for temporary node failures",
      "Merkle trees for efficient anti-entropy repair",
      "Read repair on every read for consistency convergence",
    ],
    keyTakeaways: [
      "Consistent hashing minimizes data movement",
      "Quorum (W + R > N) is the consistency tuning knob",
      "Vector clocks track causality without timestamps",
      "Gossip protocol enables decentralized failure detection",
    ],
  },
  {
    id: 10,
    title: "Design an Autocomplete / Typeahead System",
    company: ["Google", "Microsoft", "Amazon"],
    difficulty: "Medium",
    estimatedTime: "35 min",
    description:
      "Design a typeahead suggestion system that provides real-time search suggestions as the user types.",
    requirements: {
      functional: [
        "Return top 5-10 suggestions for a given prefix",
        "Suggestions ranked by popularity / relevance",
        "Support multi-language queries",
        "Update suggestions based on new search data",
      ],
      nonFunctional: [
        "Response time < 100ms",
        "Handle millions of QPS",
        "Suggestions should be fresh (within hours of new trends)",
        "Don't suggest offensive or harmful content",
      ],
    },
    highLevelDesign: {
      components: [
        "Trie data structure (prefix tree)",
        "Aggregation Service (count search frequencies)",
        "Data Collection Service (log queries)",
        "Trie Builder (offline/batch)",
        "Trie Servers (serve queries)",
        "Cache layer (top queries per prefix)",
        "Filter Service (block offensive terms)",
      ],
      diagram:
        "User types → API → Trie Server → Lookup prefix → Return top-K suggestions\nSearch logs → Data Collection → Aggregation (MapReduce) → Trie Builder → Deploy to Trie Servers",
    },
    deepDive: [
      {
        title: "Trie with Frequency Data",
        content:
          "Each trie node stores: children, top-K suggestions for that prefix (pre-computed). When a user types 'be', traverse to 'b' → 'e' and return the pre-computed top-K list. This makes lookups O(prefix length) with O(1) result retrieval.",
      },
      {
        title: "Data Pipeline",
        content:
          "Collect search queries in a log. Periodically aggregate frequencies (hourly/daily MapReduce job). Build a new trie from aggregated data. Deploy to trie servers via a blue-green rollout. For real-time trending, maintain a separate small trie of recent queries merged at query time.",
      },
      {
        title: "Browser Caching",
        content:
          "Cache suggestions on the client-side. For common prefixes (1-2 chars), responses rarely change. Debounce requests (wait 100-300ms after last keystroke). Only send request if prefix changed since last response.",
      },
    ],
    bottlenecks: [
      "Memory for the full trie at scale",
      "Trie rebuild time for billions of queries",
      "Trending topics making the trie stale",
    ],
    scaling: [
      "Shard trie by first character / prefix range",
      "Two-tier trie: real-time (small) + batch (full)",
      "CDN caching for top prefixes",
      "Client-side caching with debounce",
    ],
    keyTakeaways: [
      "Pre-compute top-K at each trie node for fast retrieval",
      "Trie is the core data structure for prefix matching",
      "Separate offline (batch) pipeline from online serving",
      "Client-side caching + debounce reduces server load by 80%+",
    ],
  },
  {
    id: 11,
    title: "Design a Distributed Message Queue (Kafka)",
    company: ["Amazon", "Google", "Netflix"],
    difficulty: "Hard",
    estimatedTime: "40 min",
    description:
      "Design a distributed, high-throughput, fault-tolerant message queue supporting pub-sub and point-to-point messaging patterns.",
    requirements: {
      functional: [
        "Producers publish messages to named topics",
        "Consumers subscribe to topics and consume messages",
        "Support for consumer groups (parallel processing)",
        "Message ordering within a partition",
        "Message retention for configurable duration",
      ],
      nonFunctional: [
        "High throughput (millions of messages/sec)",
        "Durability — no message loss after acknowledgment",
        "Low latency (< 10ms end-to-end for 99th percentile)",
        "Horizontal scalability",
      ],
    },
    highLevelDesign: {
      components: [
        "Producers (client library)",
        "Brokers (message storage & serving)",
        "ZooKeeper / Raft consensus (metadata, leader election)",
        "Topics & Partitions (unit of parallelism)",
        "Consumer groups (coordination)",
        "Replication (leader + followers per partition)",
      ],
      diagram:
        "Producer → Broker (partition leader) → Write to commit log → Replicate to followers\nConsumer Group → Broker → Read from commit log → Track offset per consumer",
    },
    deepDive: [
      {
        title: "Partitioning & Ordering",
        content:
          "Each topic is divided into partitions. Messages are appended to a partition's commit log (append-only). Ordering is guaranteed within a partition (not across). Producers choose a partition by key hash (same key → same partition) or round-robin for distribution.",
      },
      {
        title: "Replication & Durability",
        content:
          "Each partition has a leader and N-1 follower replicas. Writes go to the leader and are replicated to in-sync replicas (ISR). A message is committed only when replicated to min ISR count. If the leader fails, a follower from ISR is elected. Committed messages are never lost.",
      },
      {
        title: "Consumer Groups & Offset Tracking",
        content:
          "Consumers in a group split partitions among themselves (each partition assigned to one consumer). Consumers commit their offset (position in the log) periodically or after processing. On rebalance (consumer join/leave), partitions are reassigned.",
      },
    ],
    bottlenecks: [
      "Partition hotspot (all messages to one partition)",
      "Consumer rebalancing storms",
      "Disk I/O during high-throughput writes",
    ],
    scaling: [
      "Increase partitions for higher parallelism",
      "Zero-copy transfer for consumer reads",
      "Page cache utilization for sequential reads",
      "Batch compression for network efficiency",
    ],
    keyTakeaways: [
      "Append-only commit log is the fundamental abstraction",
      "Partitions are the unit of parallelism and ordering",
      "ISR-based replication balances durability and latency",
      "Consumer groups enable horizontal scaling of consumers",
    ],
  },
  {
    id: 12,
    title: "Design Google Docs (Collaborative Editing)",
    company: ["Google", "Microsoft", "Meta"],
    difficulty: "Expert",
    estimatedTime: "50 min",
    description:
      "Design a real-time collaborative document editing system where multiple users can edit the same document simultaneously.",
    requirements: {
      functional: [
        "Multiple users edit the same document in real-time",
        "See other users' cursors and selections",
        "Version history and undo/redo",
        "Rich text formatting (bold, italic, headers)",
        "Comments and suggestions mode",
      ],
      nonFunctional: [
        "Zero perceived latency for local edits",
        "Consistent document state across all collaborators",
        "Handle 100+ concurrent editors per document",
        "No data loss on conflicts or crashes",
      ],
    },
    highLevelDesign: {
      components: [
        "WebSocket Gateway (real-time sync)",
        "Document Service (CRUD, versioning)",
        "Conflict Resolution Engine (OT or CRDT)",
        "Operation Log (append-only)",
        "Document Store (snapshot + ops)",
        "Presence Service (cursors, selections)",
        "Media Service (embedded images)",
      ],
      diagram:
        "User edits → Local apply (instant) → Send op to server → Transform against concurrent ops → Broadcast to collaborators\nServer: Receive op → OT transform → Append to op log → Broadcast transformed op → Periodic snapshot",
    },
    deepDive: [
      {
        title: "Operational Transformation (OT)",
        content:
          "Each edit is represented as an operation (insert, delete, retain). When concurrent ops arrive, the server transforms one against the other to preserve intent. Example: if User A inserts at position 3 and User B deletes at position 1, User A's insert position is adjusted to 2. The server maintains a sequence of transformed ops that all clients converge to.",
      },
      {
        title: "CRDTs as Alternative",
        content:
          "Conflict-free Replicated Data Types avoid transformation by designing data structures that are inherently merge-safe. A text CRDT (e.g., RGA, YATA) assigns each character a unique, causally-ordered ID. Inserts and deletes commute naturally. Higher memory overhead but simpler conflict resolution.",
      },
      {
        title: "Versioning & Snapshots",
        content:
          "Store the full operation log from document creation. Periodically take snapshots (full document state at op N) to avoid replaying all ops. To load a document: fetch the latest snapshot + all ops since that snapshot. Version history is built by replaying ops to any point in time.",
      },
    ],
    bottlenecks: [
      "OT server becomes a single point of serialization",
      "Large documents with 100+ editors",
      "Operation log growing unbounded",
    ],
    scaling: [
      "Document-level sharding (one server per document)",
      "CRDT for truly decentralized editing",
      "Periodic snapshotting + log compaction",
      "Edge caching for read-only viewers",
    ],
    keyTakeaways: [
      "OT: transformation-based, widely used (Google Docs)",
      "CRDT: merge-based, newer approach (Figma, Notion)",
      "Optimistic local apply + async server sync eliminates perceived latency",
      "Operation log + snapshots = efficient version history",
    ],
  },
];
