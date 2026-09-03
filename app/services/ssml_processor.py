"""
SSML-like text processor for technical term pronunciation.
Ensures TTS engines pronounce acronyms, framework names,
and technical terms correctly.
"""

import re
from typing import Dict
from loguru import logger


class SSMLProcessor:
    """
    Pre-processes text for better TTS pronunciation.
    
    Handles:
      - Technical acronyms (API → "A P I")
      - Framework names (nginx → "engine X")
      - Version numbers (Python 3.11 → "Python three point eleven")
      - Code-like terms (torch.compile → "Torch compile")
      - Punctuation cleanup for natural pauses
    """

    # Acronyms to spell out letter by letter
    SPELL_OUT: Dict[str, str] = {
        "API": "A P I",
        "SQL": "S Q L",
        "AWS": "A W S",
        "GCP": "G C P",
        "HTML": "H T M L",
        "CSS": "C S S",
        "REST": "REST",
        "CRUD": "CRUD",
        "CI/CD": "C I C D",
        "DNS": "D N S",
        "HTTP": "H T T P",
        "HTTPS": "H T T P S",
        "TCP": "T C P",
        "UDP": "U D P",
        "SSH": "S S H",
        "SSL": "S S L",
        "TLS": "T L S",
        "JWT": "J W T",
        "OOP": "O O P",
        "MVC": "M V C",
        "SDK": "S D K",
        "IDE": "I D E",
        "CLI": "C L I",
        "GUI": "G U I",
        "ORM": "O R M",
        "CDN": "C D N",
        "NLP": "N L P",
        "CNN": "C N N",
        "RNN": "R N N",
        "LSTM": "L S T M",
        "GAN": "G A N",
        "LLM": "L L M",
        "RAG": "R A G",
        "GPU": "G P U",
        "CPU": "C P U",
        "RAM": "RAM",
        "ETL": "E T L",
        "ELT": "E L T",
        "SaaS": "SaaS",
        "PaaS": "PaaS",
        "IaaS": "I A A S",
        "NoSQL": "No S Q L",
        "DevOps": "Dev Ops",
        "MLOps": "M L Ops",
        "YAML": "YAML",
        "JSON": "Jason",
        "XML": "X M L",
        "CSV": "C S V",
        "K8s": "Kubernetes",
        "k8s": "Kubernetes",
    }

    # Technical terms with non-obvious pronunciations
    PRONUNCIATIONS: Dict[str, str] = {
        "nginx": "engine X",
        "kubectl": "kube control",
        "sudo": "sue doo",
        "linux": "Linux",
        "ubuntu": "oo-boon-too",
        "kubernetes": "Kubernetes",
        "postgresql": "Postgres Q L",
        "mysql": "My S Q L",
        "graphql": "Graph Q L",
        "pytorch": "Pie Torch",
        "scikit-learn": "sy-kit learn",
        "sklearn": "sy-kit learn",
        "fastapi": "Fast A P I",
        "numpy": "num pie",
        "scipy": "sigh pie",
        "matplotlib": "mat plot lib",
        "jupyter": "Jupiter",
        "django": "Jango",
        "vue.js": "View J S",
        "next.js": "Next J S",
        "node.js": "Node J S",
        "react.js": "React J S",
        "express.js": "Express J S",
        "nest.js": "Nest J S",
        "nuxt.js": "Nuxt J S",
        "svelte": "Svelt",
        "webpack": "Web Pack",
        "tailwindcss": "Tailwind C S S",
        "tailwind": "Tailwind",
        "supabase": "Super Base",
        "vercel": "Ver sell",
        "heroku": "Heh roku",
        "oauth": "O Auth",
        "grpc": "G R P C",
        "rabbitmq": "Rabbit M Q",
        "celery": "Celery",
        "redis": "Red iss",
        "xgboost": "X G Boost",
        "lightgbm": "Light G B M",
        "catboost": "Cat Boost",
        "langchain": "Lang Chain",
        "huggingface": "Hugging Face",
        "openai": "Open A I",
        "llama": "Llama",
        "mistral": "Mistral",
        "torch.compile": "Torch compile",
        "torchscript": "Torch script",
    }

    def __init__(self):
        # Build regex patterns sorted by length (longest first)
        acronym_keys = sorted(
            self.SPELL_OUT.keys(), key=len, reverse=True
        )
        escaped_acronyms = [re.escape(k) for k in acronym_keys]
        self._acronym_pattern = re.compile(
            r'\b(' + '|'.join(escaped_acronyms) + r')\b'
        )

        pron_keys = sorted(
            self.PRONUNCIATIONS.keys(), key=len, reverse=True
        )
        escaped_prons = [re.escape(k) for k in pron_keys]
        self._pron_pattern = re.compile(
            r'\b(' + '|'.join(escaped_prons) + r')\b',
            re.IGNORECASE
        )

    def process(
        self,
        text: str,
        expand_acronyms: bool = True,
        fix_pronunciations: bool = True,
        add_pauses: bool = True,
        clean_for_speech: bool = True,
    ) -> str:
        """
        Process text for optimal TTS pronunciation.

        Args:
            text: Raw text to process
            expand_acronyms: Spell out technical acronyms
            fix_pronunciations: Apply pronunciation corrections
            add_pauses: Insert natural pauses at boundaries
            clean_for_speech: Remove non-speakable characters

        Returns:
            Processed text optimized for TTS
        """
        if not text:
            return text

        result = text

        if expand_acronyms:
            result = self._expand_acronyms(result)

        if fix_pronunciations:
            result = self._fix_pronunciations(result)

        if add_pauses:
            result = self._add_natural_pauses(result)

        if clean_for_speech:
            result = self._clean_for_speech(result)

        return result.strip()

    def _expand_acronyms(self, text: str) -> str:
        """Replace acronyms with spelled-out versions."""
        def replace_match(match):
            word = match.group(1)
            return self.SPELL_OUT.get(word, word)

        return self._acronym_pattern.sub(replace_match, text)

    def _fix_pronunciations(self, text: str) -> str:
        """Apply pronunciation corrections for tech terms."""
        def replace_match(match):
            word = match.group(1)
            return self.PRONUNCIATIONS.get(word.lower(), word)

        return self._pron_pattern.sub(replace_match, text)

    def _add_natural_pauses(self, text: str) -> str:
        """Insert pauses for more natural speech flow."""
        # Pause after question marks
        text = re.sub(r'\?\s+', '? ... ', text)

        # Pause before transition phrases
        pause_before = [
            "For example", "Specifically", "In particular",
            "Additionally", "Furthermore", "However",
            "Could you", "Can you", "How would you",
            "What was", "What were", "What is",
            "Tell me", "Describe", "Explain",
            "Walk me through", "Let's discuss",
        ]
        for phrase in pause_before:
            text = text.replace(
                f". {phrase}", f". ... {phrase}"
            )

        return text

    def _clean_for_speech(self, text: str) -> str:
        """Remove characters that shouldn't be spoken."""
        # Remove URLs
        text = re.sub(
            r'https?://\S+', '', text
        )
        # Remove email addresses
        text = re.sub(
            r'\S+@\S+\.\S+', '', text
        )
        # Remove markdown formatting
        text = re.sub(r'[*_`#]', '', text)
        # Remove bullet points
        text = re.sub(r'^[\•\-\*\>\▪]\s*', '', text, flags=re.MULTILINE)
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Collapse multiple pauses
        text = re.sub(r'(\.\.\.\s*){2,}', '... ', text)

        return text
