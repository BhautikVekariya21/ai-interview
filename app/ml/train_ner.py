"""
NER model training script.
Includes synthetic training data generation for resume entities.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
from loguru import logger

from app.core.config import settings
from app.ml.experiment_tracking import MLflowTracker
from app.models.ner_model import TAG_TO_IDX, ResumeNERModel


class ResumeNERTrainer:
    """Handles synthetic data generation and PyTorch training for the NER model."""

    def __init__(self, tracker: MLflowTracker | None = None):
        self.model = ResumeNERModel()
        self.tracker = tracker or MLflowTracker()
        self.first_names = ["John", "Jane", "Alex", "Sarah", "Michael", "Emily", "David", "Lisa", "James", "Maria", "Robert", "Amanda", "Priya", "Raj", "Wei", "Yuki", "Ahmed", "Fatima", "Carlos", "Sofia", "Anika", "Deepak", "Chen", "Sato"]
        self.last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Kumar", "Patel", "Wang", "Kim", "Tanaka", "Hassan", "Rodriguez", "Martinez", "Sharma", "Gupta", "Lee", "Chen", "Wilson", "Anderson"]
        self.companies = ["Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix", "Tesla", "IBM", "Oracle", "Salesforce", "Adobe", "Uber", "Airbnb", "Stripe", "Spotify", "Infosys", "TCS", "Wipro", "Accenture", "Deloitte", "Goldman Sachs", "JPMorgan", "McKinsey", "BCG"]
        self.roles = ["Software Engineer", "Senior Developer", "Machine Learning Engineer", "Data Scientist", "Full Stack Developer", "Backend Engineer", "Frontend Developer", "DevOps Engineer", "Product Manager", "Technical Lead", "Research Scientist", "Cloud Architect", "Mobile Developer", "QA Engineer", "Systems Engineer", "Database Administrator"]
        self.institutions = ["MIT", "Stanford University", "Harvard University", "Carnegie Mellon University", "UC Berkeley", "Georgia Tech", "University of Michigan", "IIT Delhi", "IIT Bombay", "NIT Trichy", "University of Toronto", "ETH Zurich", "University of Oxford", "Caltech", "University of Illinois", "Columbia University"]
        self.degrees = ["Bachelor of Science", "Master of Science", "Bachelor of Technology", "Master of Technology", "Bachelor of Engineering", "Master of Engineering", "Ph.D.", "MBA", "Bachelor of Arts", "Master of Arts", "B.S.", "M.S.", "B.Tech", "M.Tech", "B.E.", "M.E."]
        self.fields = ["Computer Science", "Software Engineering", "Electrical Engineering", "Data Science", "Information Technology", "Artificial Intelligence", "Machine Learning", "Mechanical Engineering", "Mathematics", "Physics", "Statistics", "Computer Engineering", "Cybersecurity"]
        self.skills = ["Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Ruby", "Swift", "React", "Angular", "Vue.js", "Node.js", "Django", "Flask", "FastAPI", "Spring Boot", "PyTorch", "PyTorch Lightning", "Hugging Face", "scikit-learn", "XGBoost", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Git", "Linux", "REST API", "GraphQL", "CI/CD", "Apache Kafka", "RabbitMQ", "Terraform", "Jenkins"]
        self.projects = ["E-commerce Platform", "Chat Application", "Recommendation Engine", "Fraud Detection System", "Image Classification Model", "NLP Pipeline", "Real-time Analytics Dashboard", "Task Manager App", "Social Media Platform", "Content Management System", "Autonomous Drone Controller", "Stock Predictor", "Health Monitoring System", "IoT Gateway"]
        self.certifications = ["AWS Certified Solutions Architect", "Google Cloud Professional", "Certified Kubernetes Administrator", "AWS Certified Machine Learning - Specialty", "Azure Data Scientist Associate", "Certified ScrumMaster", "PMP Certification", "CISSP"]

    def generate_synthetic_training_data(self, num_samples: int = 5000) -> Tuple[List[List[str]], List[List[str]]]:
        logger.info(f"Generating {num_samples} synthetic training samples...")
        all_tokens: List[List[str]] = []
        all_tags: List[List[str]] = []
        generators = [self._gen_personal_info, self._gen_education, self._gen_experience, self._gen_skill_line, self._gen_project, self._gen_certification, self._gen_achievement, self._gen_mixed_line]
        for _ in range(num_samples):
            tokens, tags = random.choice(generators)()
            all_tokens.append(tokens)
            all_tags.append(tags)
        logger.info(f"Generated {len(all_tokens)} training samples")
        return all_tokens, all_tags

    def _gen_personal_info(self) -> Tuple[List[str], List[str]]:
        return random.choice([self._gen_name_line, self._gen_email_line, self._gen_phone_line, self._gen_location_line])()

    def _gen_name_line(self) -> Tuple[List[str], List[str]]:
        tokens = [random.choice(self.first_names), random.choice(self.last_names)]
        tags = ["B-NAME", "I-NAME"]
        if random.random() < 0.3:
            tokens = [random.choice(["Mr.", "Ms.", "Dr.", "Prof."])] + tokens
            tags = ["O"] + tags
        return tokens, tags

    def _gen_email_line(self) -> Tuple[List[str], List[str]]:
        first = random.choice(self.first_names).lower()
        last = random.choice(self.last_names).lower()
        domain = random.choice(["gmail.com", "outlook.com", "yahoo.com", "university.edu", "company.com"])
        email = f"{first}.{last}@{domain}"
        prefix_tokens, prefix_tags = random.choice([(["Email", ":"], ["O", "O"]), (["Contact", ":"], ["O", "O"]), (["E-mail", ":"], ["O", "O"]), ([], [])])
        return prefix_tokens + [email], prefix_tags + ["B-EMAIL"]

    def _gen_phone_line(self) -> Tuple[List[str], List[str]]:
        phone = random.choice([f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}", f"({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}", f"+91-{random.randint(70000,99999)}{random.randint(10000,99999)}"])
        prefix_tokens, prefix_tags = random.choice([(["Phone", ":"], ["O", "O"]), (["Tel", ":"], ["O", "O"]), (["Mobile", ":"], ["O", "O"]), ([], [])])
        return prefix_tokens + [phone], prefix_tags + ["B-PHONE"]

    def _gen_location_line(self) -> Tuple[List[str], List[str]]:
        city = random.choice([("San", "Francisco", ",", "CA"), ("New", "York", ",", "NY"), ("Bangalore", ",", "India"), ("London", ",", "UK"), ("Toronto", ",", "Canada"), ("Berlin", ",", "Germany")])
        return list(city), ["B-LOCATION"] + ["I-LOCATION"] * (len(city) - 1)

    def _gen_education(self) -> Tuple[List[str], List[str]]:
        degree_tokens = random.choice(self.degrees).split()
        field_tokens = random.choice(self.fields).split()
        inst_tokens = random.choice(self.institutions).split()
        tokens = degree_tokens + ["in"] + field_tokens + [random.choice([",", "-", "from", "|"])] + inst_tokens
        tags = ["B-DEGREE"] + ["I-DEGREE"] * (len(degree_tokens) - 1) + ["O"] + ["B-FIELD"] + ["I-FIELD"] * (len(field_tokens) - 1) + ["O"] + ["B-INSTITUTION"] + ["I-INSTITUTION"] * (len(inst_tokens) - 1)
        if random.random() < 0.5:
            tokens.extend(["GPA", ":", f"{random.uniform(2.5, 4.0):.2f}"])
            tags.extend(["O", "O", "B-GPA"])
        if random.random() < 0.6:
            tokens.extend(["-", str(random.randint(2015, 2024))])
            tags.extend(["O", "B-DATE"])
        return tokens, tags

    def _gen_experience(self) -> Tuple[List[str], List[str]]:
        role_tokens = random.choice(self.roles).split()
        company_tokens = random.choice(self.companies).split()
        tokens = role_tokens + [random.choice(["at", "|", ",", "-"])] + company_tokens
        tags = ["B-ROLE"] + ["I-ROLE"] * (len(role_tokens) - 1) + ["O"] + ["B-COMPANY"] + ["I-COMPANY"] * (len(company_tokens) - 1)
        if random.random() < 0.7:
            start_year = random.randint(2018, 2023)
            end_year = random.choice([str(start_year + random.randint(1, 3)), "Present"])
            tokens.extend([str(start_year), "-", end_year])
            tags.extend(["B-DATE", "O", "B-DATE"])
        return tokens, tags

    def _gen_skill_line(self) -> Tuple[List[str], List[str]]:
        selected = random.sample(self.skills, min(random.randint(3, 8), len(self.skills)))
        tokens: List[str] = []
        tags: List[str] = []
        if random.random() < 0.4:
            prefix_tokens = random.choice(["Skills:", "Technical Skills:", "Technologies:", "Proficiencies:"]).split()
            tokens.extend(prefix_tokens)
            tags.extend(["O"] * len(prefix_tokens))
        for idx, skill in enumerate(selected):
            skill_tokens = skill.split()
            tokens.extend(skill_tokens)
            tags.extend(["B-SKILL"] + ["I-SKILL"] * (len(skill_tokens) - 1))
            if idx < len(selected) - 1:
                tokens.append(random.choice([",", "|", ";"]))
                tags.append("O")
        return tokens, tags

    def _gen_project(self) -> Tuple[List[str], List[str]]:
        proj_tokens = random.choice(self.projects).split()
        tokens = list(proj_tokens)
        tags = ["B-PROJECT"] + ["I-PROJECT"] * (len(proj_tokens) - 1)
        if random.random() < 0.7:
            tokens.append("using")
            tags.append("O")
            techs = random.sample(self.skills, random.randint(2, 4))
            for idx, tech in enumerate(techs):
                tech_tokens = tech.split()
                tokens.extend(tech_tokens)
                tags.extend(["B-SKILL"] + ["I-SKILL"] * (len(tech_tokens) - 1))
                if idx < len(techs) - 1:
                    tokens.append(",")
                    tags.append("O")
        return tokens, tags

    def _gen_certification(self) -> Tuple[List[str], List[str]]:
        cert_tokens = random.choice(self.certifications).split()
        tokens = list(cert_tokens)
        tags = ["B-CERT"] + ["I-CERT"] * (len(cert_tokens) - 1)
        if random.random() < 0.5:
            tokens.extend(["-", str(random.randint(2020, 2024))])
            tags.extend(["O", "B-DATE"])
        return tokens, tags

    def _gen_achievement(self) -> Tuple[List[str], List[str]]:
        ach_tokens = random.choice(["Dean's List", "Summa Cum Laude", "Best Paper Award", "Hackathon Winner", "Employee of the Year", "Outstanding Performance Award", "First Place", "Gold Medal"]).split()
        return ach_tokens, ["B-ACHIEVEMENT"] + ["I-ACHIEVEMENT"] * (len(ach_tokens) - 1)

    def _gen_mixed_line(self) -> Tuple[List[str], List[str]]:
        role_tokens = random.choice(self.roles).split()
        company_tokens = random.choice(self.companies).split()
        skill1_tokens = random.choice(self.skills).split()
        skill2_tokens = random.choice(self.skills).split()
        tokens = ["Worked", "as"] + role_tokens + ["at"] + company_tokens + ["using"] + skill1_tokens + ["and"] + skill2_tokens
        tags = ["O", "O"] + ["B-ROLE"] + ["I-ROLE"] * (len(role_tokens) - 1) + ["O"] + ["B-COMPANY"] + ["I-COMPANY"] * (len(company_tokens) - 1) + ["O"] + ["B-SKILL"] + ["I-SKILL"] * (len(skill1_tokens) - 1) + ["O"] + ["B-SKILL"] + ["I-SKILL"] * (len(skill2_tokens) - 1)
        return tokens, tags

    def prepare_training_data(self, token_sequences: List[List[str]], tag_sequences: List[List[str]]) -> Tuple[np.ndarray, np.ndarray]:
        self.model.build_vocabulary(token_sequences)
        x_rows = []
        y_rows = []
        for tokens, tags in zip(token_sequences, tag_sequences):
            x_rows.append(self.model.tokens_to_ids(tokens))
            tag_ids = [TAG_TO_IDX.get(tag, TAG_TO_IDX["O"]) for tag in tags[: settings.MAX_SEQUENCE_LENGTH]]
            tag_ids.extend([TAG_TO_IDX["PAD"]] * (settings.MAX_SEQUENCE_LENGTH - len(tag_ids)))
            y_rows.append(tag_ids)
        return np.array(x_rows, dtype=np.int32), np.array(y_rows, dtype=np.int32)

    def train(
        self,
        num_samples: int = 5000,
        epochs: int = None,
        batch_size: int = None,
        validation_split: float = 0.15,
        model_path: str | None = None,
        metrics_path: str | None = None,
        seed: int = 42,
        run_name: str | None = None,
    ) -> Dict[str, Any]:
        epochs = epochs or settings.EPOCHS
        batch_size = batch_size or settings.BATCH_SIZE
        model_path = model_path or settings.NER_MODEL_PATH
        metrics_path = metrics_path or settings.NER_TRAINING_METRICS_PATH
        started_at = datetime.now(UTC)

        self._set_seed(seed)
        logger.info("=" * 60)
        logger.info("STARTING PYTORCH NER MODEL TRAINING")
        logger.info("=" * 60)

        training_params = {
            "num_samples": num_samples,
            "epochs": epochs,
            "batch_size": batch_size,
            "validation_split": validation_split,
            "embedding_dim": self.model.embedding_dim,
            "lstm_units": self.model.lstm_units,
            "dropout_rate": self.model.dropout_rate,
            "learning_rate": settings.LEARNING_RATE,
            "max_sequence_length": self.model.max_seq_length,
            "seed": seed,
            "device": str(self.model.device),
        }

        with self.tracker.start_run(run_name=run_name):
            self.tracker.log_params(training_params)

            token_seqs, tag_seqs = self.generate_synthetic_training_data(num_samples)
            x_data, y_data = self.prepare_training_data(token_seqs, tag_seqs)
            logger.info(f"Training data shape: X={x_data.shape}, y={y_data.shape}")

            self.model.vocab_size = len(self.model.word_to_idx) + 100
            self.model.build_model()
            self.model.compile_model()

            x_tensor = torch.as_tensor(x_data, dtype=torch.long, device=self.model.device)
            y_tensor = torch.as_tensor(y_data, dtype=torch.long, device=self.model.device)
            indices = torch.randperm(x_tensor.size(0), device=self.model.device)
            split_idx = max(1, int(x_tensor.size(0) * (1 - validation_split)))
            train_idx = indices[:split_idx]
            val_idx = indices[split_idx:] if split_idx < len(indices) else indices[:1]

            history = {"loss": [], "val_loss": []}
            best_val_loss = float("inf")
            best_epoch = 0
            trained_epochs = 0
            patience_left = 7
            checkpoint_path = os.path.join(model_path, "checkpoint.pt")
            os.makedirs(model_path, exist_ok=True)

            for epoch in range(epochs):
                self.model.model.train()
                epoch_losses: List[float] = []
                shuffled = train_idx[torch.randperm(train_idx.size(0), device=self.model.device)]
                for start in range(0, shuffled.size(0), batch_size):
                    batch_ids = shuffled[start: start + batch_size]
                    batch_x = x_tensor[batch_ids]
                    batch_y = y_tensor[batch_ids]
                    self.model.optimizer.zero_grad()
                    emissions = self.model.model(batch_x)
                    loss = self.model._crf_loss(batch_y, emissions)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(list(self.model.model.parameters()) + list(self.model.crf_layer.parameters()), max_norm=5.0)
                    self.model.optimizer.step()
                    epoch_losses.append(float(loss.detach().cpu().item()))

                train_loss = sum(epoch_losses) / max(1, len(epoch_losses))
                val_loss = self._evaluate_loss(x_tensor[val_idx], y_tensor[val_idx])
                history["loss"].append(train_loss)
                history["val_loss"].append(val_loss)
                trained_epochs = epoch + 1
                logger.info(f"Epoch {trained_epochs}/{epochs} | loss={train_loss:.4f} | val_loss={val_loss:.4f}")
                self.tracker.log_metrics({"train_loss": train_loss, "val_loss": val_loss}, step=epoch)

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_epoch = trained_epochs
                    patience_left = 7
                    torch.save({"model_state_dict": self.model.model.state_dict(), "crf_state_dict": self.model.crf_layer.state_dict()}, checkpoint_path)
                else:
                    patience_left -= 1
                    if patience_left <= 0:
                        logger.info("Early stopping triggered")
                        break

            if os.path.exists(checkpoint_path):
                checkpoint = torch.load(checkpoint_path, map_location=self.model.device, weights_only=False)
                self.model.model.load_state_dict(checkpoint["model_state_dict"])
                self.model.crf_layer.load_state_dict(checkpoint["crf_state_dict"])

            self.model.save(model_path)

            summary = self._build_training_summary(
                history=history,
                training_params=training_params,
                model_path=model_path,
                metrics_path=metrics_path,
                best_epoch=best_epoch,
                best_val_loss=best_val_loss,
                trained_epochs=trained_epochs,
                started_at=started_at,
            )
            self._write_metrics(summary, metrics_path)
            self.tracker.log_artifact(metrics_path, artifact_path=settings.MLFLOW_ARTIFACT_PATH)
            self.tracker.log_artifacts(model_path, artifact_path=os.path.join(settings.MLFLOW_ARTIFACT_PATH, "ner_model"))
            self.tracker.log_metrics(
                {
                    "best_val_loss": summary["best_val_loss"],
                    "final_train_loss": summary["final_train_loss"],
                    "final_val_loss": summary["final_val_loss"],
                }
            )

        logger.info("=" * 60)
        logger.info("TRAINING COMPLETE")
        logger.info(f"Final loss: {summary['final_train_loss']:.4f}")
        logger.info("=" * 60)
        return summary

    def _evaluate_loss(self, x_val: torch.Tensor, y_val: torch.Tensor) -> float:
        self.model.model.eval()
        with torch.no_grad():
            emissions = self.model.model(x_val)
            loss = self.model._crf_loss(y_val, emissions)
        return float(loss.cpu().item())

    def _build_training_summary(
        self,
        history: Dict[str, List[float]],
        training_params: Dict[str, Any],
        model_path: str,
        metrics_path: str,
        best_epoch: int,
        best_val_loss: float,
        trained_epochs: int,
        started_at: datetime,
    ) -> Dict[str, Any]:
        finished_at = datetime.now(UTC)
        return {
            "status": "completed",
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
            "trained_epochs": trained_epochs,
            "best_epoch": best_epoch,
            "best_val_loss": round(float(best_val_loss), 6),
            "final_train_loss": round(float(history["loss"][-1]), 6),
            "final_val_loss": round(float(history["val_loss"][-1]), 6),
            "history": history,
            "params": training_params,
            "artifacts": {
                "model_path": model_path,
                "metrics_path": metrics_path,
            },
        }

    def _write_metrics(self, summary: Dict[str, Any], metrics_path: str) -> None:
        metrics_file = Path(metrics_path)
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        metrics_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    def _set_seed(self, seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train the resume NER model with optional MLflow tracking.")
    parser.add_argument("--num-samples", type=int, default=5000, help="Number of synthetic training samples to generate.")
    parser.add_argument("--epochs", type=int, default=settings.EPOCHS, help="Maximum number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=settings.BATCH_SIZE, help="Batch size for training.")
    parser.add_argument("--validation-split", type=float, default=0.15, help="Validation split ratio.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible training.")
    parser.add_argument("--model-path", default=settings.NER_MODEL_PATH, help="Directory where the trained model will be saved.")
    parser.add_argument("--metrics-path", default=settings.NER_TRAINING_METRICS_PATH, help="Path for the JSON metrics report.")
    parser.add_argument("--run-name", default=None, help="Optional MLflow run name.")
    return parser


def main() -> Dict[str, Any]:
    args = build_arg_parser().parse_args()
    tracker = MLflowTracker()
    trainer = ResumeNERTrainer(tracker=tracker)
    return trainer.train(
        num_samples=args.num_samples,
        epochs=args.epochs,
        batch_size=args.batch_size,
        validation_split=args.validation_split,
        model_path=args.model_path,
        metrics_path=args.metrics_path,
        seed=args.seed,
        run_name=args.run_name,
    )


if __name__ == "__main__":
    main()
