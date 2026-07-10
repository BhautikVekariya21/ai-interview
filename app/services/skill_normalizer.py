"""
Skill normalization service.
Maps extracted skill mentions to a canonical taxonomy
with categorization and deduplication.
"""

import json
import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from loguru import logger

from app.core.config import settings
from app.services.rust_accelerator import get_rust_accelerator


# Embedded skill taxonomy (subset — full version would be in JSON file)
DEFAULT_SKILL_TAXONOMY = {
    "languages": {
        "Python": ["python", "python3", "py"],
        "Java": ["java", "java8", "java11", "java17"],
        "JavaScript": [
            "javascript", "js", "es6", "es2015",
            "ecmascript"
        ],
        "TypeScript": ["typescript", "ts"],
        "C++": ["c++", "cpp", "c plus plus"],
        "C#": ["c#", "csharp", "c sharp"],
        "Go": ["go", "golang"],
        "Rust": ["rust", "rust-lang"],
        "Ruby": ["ruby", "rb"],
        "Swift": ["swift"],
        "Kotlin": ["kotlin", "kt"],
        "PHP": ["php", "php7", "php8"],
        "Scala": ["scala"],
        "R": ["r", "r-lang", "rlang"],
        "MATLAB": ["matlab"],
        "SQL": ["sql", "structured query language"],
        "Bash": ["bash", "shell", "sh", "zsh"],
        "Dart": ["dart"],
        "Perl": ["perl"],
        "Lua": ["lua"],
        "Haskell": ["haskell"],
        "Elixir": ["elixir"],
        "Julia": ["julia"],
    },
    "frameworks": {
        "React": ["react", "reactjs", "react.js"],
        "Angular": ["angular", "angularjs", "angular.js"],
        "Vue.js": ["vue", "vuejs", "vue.js"],
        "Next.js": ["next", "nextjs", "next.js"],
        "Node.js": ["node", "nodejs", "node.js"],
        "Express.js": ["express", "expressjs", "express.js"],
        "Django": ["django"],
        "Flask": ["flask"],
        "FastAPI": ["fastapi", "fast api"],
        "Spring Boot": ["spring boot", "springboot", "spring"],
        "Ruby on Rails": ["rails", "ruby on rails", "ror"],
        ".NET": [".net", "dotnet", "asp.net"],
        "Laravel": ["laravel"],
        "Svelte": ["svelte", "sveltejs"],
        "jQuery": ["jquery"],
        "Bootstrap": ["bootstrap"],
        "Tailwind CSS": ["tailwind", "tailwindcss", "tailwind css"],
    },
    "ml_frameworks": {
        "PyTorch": ["pytorch", "torch"],
        "PyTorch Lightning": ["pytorch lightning", "lightning", "pl"],
        "scikit-learn": [
            "scikit-learn", "sklearn", "scikit learn"
        ],
        "Hugging Face": [
            "huggingface", "hugging face", "transformers"
        ],
        "OpenCV": ["opencv", "cv2"],
        "NLTK": ["nltk"],
        "spaCy": ["spacy"],
        "XGBoost": ["xgboost", "xgb"],
        "LightGBM": ["lightgbm", "lgbm"],
        "Pandas": ["pandas", "pd"],
        "NumPy": ["numpy", "np"],
        "Matplotlib": ["matplotlib", "plt"],
        "Seaborn": ["seaborn", "sns"],
    },
    "databases": {
        "PostgreSQL": [
            "postgresql", "postgres", "psql", "pg"
        ],
        "MySQL": ["mysql"],
        "MongoDB": ["mongodb", "mongo"],
        "Redis": ["redis"],
        "Elasticsearch": [
            "elasticsearch", "elastic search", "es"
        ],
        "SQLite": ["sqlite", "sqlite3"],
        "Cassandra": ["cassandra"],
        "DynamoDB": ["dynamodb", "dynamo"],
        "Oracle DB": ["oracle", "oracle db"],
        "SQL Server": [
            "sql server", "mssql", "microsoft sql server"
        ],
        "Neo4j": ["neo4j"],
        "CouchDB": ["couchdb"],
        "Firebase": ["firebase", "firestore"],
    },
    "tools": {
        "Docker": ["docker", "dockerfile"],
        "Kubernetes": ["kubernetes", "k8s"],
        "Git": ["git"],
        "GitHub": ["github"],
        "GitLab": ["gitlab"],
        "Jenkins": ["jenkins"],
        "Terraform": ["terraform", "tf"],
        "Ansible": ["ansible"],
        "Nginx": ["nginx"],
        "Apache": ["apache"],
        "Webpack": ["webpack"],
        "Babel": ["babel"],
        "Vite": ["vite"],
        "Postman": ["postman"],
        "Jira": ["jira"],
        "Confluence": ["confluence"],
        "Figma": ["figma"],
        "VS Code": ["vscode", "vs code", "visual studio code"],
    },
    "platforms": {
        "AWS": [
            "aws", "amazon web services", "ec2", "s3",
            "lambda", "sagemaker"
        ],
        "Google Cloud": [
            "gcp", "google cloud", "google cloud platform",
            "bigquery"
        ],
        "Microsoft Azure": ["azure", "microsoft azure"],
        "Heroku": ["heroku"],
        "Vercel": ["vercel"],
        "Netlify": ["netlify"],
        "DigitalOcean": ["digitalocean", "digital ocean"],
        "Linux": ["linux", "ubuntu", "centos", "debian"],
        "Windows": ["windows"],
        "macOS": ["macos", "mac os"],
    },
    "methodologies": {
        "Agile": ["agile"],
        "Scrum": ["scrum"],
        "Kanban": ["kanban"],
        "CI/CD": ["ci/cd", "cicd", "ci cd"],
        "TDD": ["tdd", "test driven development"],
        "DevOps": ["devops", "dev ops"],
        "Microservices": ["microservices", "micro services"],
        "REST API": ["rest", "rest api", "restful"],
        "GraphQL": ["graphql"],
        "gRPC": ["grpc"],
    },
}


class SkillNormalizer:
    """
    Normalizes and categorizes extracted skills against 
    a comprehensive taxonomy.
    """

    def __init__(self, taxonomy_path: Optional[str] = None):
        self.taxonomy = self._load_taxonomy(taxonomy_path)
        self.lookup_table = self._build_lookup_table()
        self._rust = get_rust_accelerator()
        logger.info(
            f"SkillNormalizer initialized with "
            f"{len(self.lookup_table)} skill variants"
        )

    def _load_taxonomy(
        self, path: Optional[str]
    ) -> Dict:
        """Load skill taxonomy from file or use embedded default."""
        if path:
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(
                    f"Could not load taxonomy from {path}: {e}. "
                    "Using default."
                )
        return DEFAULT_SKILL_TAXONOMY

    def _build_lookup_table(self) -> Dict[str, Tuple[str, str]]:
        """
        Build a flat lookup table mapping every alias to 
        (canonical_name, category).
        """
        table = {}
        for category, skills in self.taxonomy.items():
            for canonical_name, aliases in skills.items():
                # Add the canonical name itself
                table[canonical_name.lower()] = (
                    canonical_name, category
                )
                for alias in aliases:
                    table[alias.lower()] = (
                        canonical_name, category
                    )
        return table

    def normalize(
        self, raw_skills: List[str]
    ) -> List[Dict]:
        """
        Normalize a list of raw skill strings.
        
        Returns list of dicts:
            - name: canonical skill name
            - category: skill category
            - original: original raw text
            - confidence: match confidence
        """
        normalized = []
        seen = set()

        for raw_skill in raw_skills:
            result = self._match_skill(raw_skill)
            if result and result["name"].lower() not in seen:
                seen.add(result["name"].lower())
                normalized.append(result)

        return normalized

    def _match_skill(self, raw: str) -> Optional[Dict]:
        """Match a raw skill string to the taxonomy."""
        raw_clean = self._normalize_skill_text(raw)

        if not raw_clean or len(raw_clean) < 1:
            return None

        # 1. Exact match
        if raw_clean in self.lookup_table:
            canonical, category = self.lookup_table[raw_clean]
            return {
                "name": canonical,
                "category": category,
                "original": raw,
                "confidence": 1.0,
            }

        # 2. Substring match (e.g., "Python 3.9" → "Python")
        for alias, (canonical, category) in self.lookup_table.items():
            # Avoid very short aliases causing false positives
            if len(alias) < 3:
                continue

            alias_pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(alias_pattern, raw_clean) or (
                len(raw_clean) >= 4 and raw_clean in alias
            ):
                return {
                    "name": canonical,
                    "category": category,
                    "original": raw,
                    "confidence": 0.85,
                }

        # 3. Fuzzy match
        best_match = None
        best_ratio = 0.0

        for alias, (canonical, category) in self.lookup_table.items():
            ratio = SequenceMatcher(
                None, raw_clean, alias
            ).ratio()
            if ratio > best_ratio and ratio >= settings.SKILL_MATCH_THRESHOLD:
                best_ratio = ratio
                best_match = {
                    "name": canonical,
                    "category": category,
                    "original": raw,
                    "confidence": ratio,
                }

        if best_match:
            return best_match

        # 4. No match — return as uncategorized skill
        return {
            "name": raw.strip(),
            "category": "other",
            "original": raw,
            "confidence": 0.4,
        }

    def _normalize_skill_text(self, raw: str) -> str:
        if self._rust and hasattr(self._rust, "normalize_skill_text"):
            return self._rust.normalize_skill_text(raw)

        raw_clean = raw.strip().lower()
        return re.sub(r"[^\w\s.#+/\-]", "", raw_clean).strip()

    def categorize_skills(
        self, skills: List[Dict]
    ) -> Dict[str, List[str]]:
        """
        Group normalized skills by category.
        
        Returns: Dict mapping category → list of skill names
        """
        categories = {}
        for skill in skills:
            cat = skill["category"]
            if cat not in categories:
                categories[cat] = []
            if skill["name"] not in categories[cat]:
                categories[cat].append(skill["name"])
        return categories
