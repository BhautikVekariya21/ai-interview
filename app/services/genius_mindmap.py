import json
import re
from loguru import logger
from typing import Dict, Any

from app.schemas.mindmap_schemas import GeniusMindMapResponse, GeniusMindMapNode, GeniusMindMapEdge
from app.services.llm_service import get_llm

class GeniusMindmapGenerator:
    """Service to generate mind maps from a textual prompt using LLM."""

    def __init__(self):
        self.llm = get_llm()
    
    def generate(self, topic: str) -> GeniusMindMapResponse:
        system_prompt = (
            "You are a Genius Mind Map Generator. Your job is to take a given topic or problem "
            "and break it down into a highly detailed, professional, and visually structured mind map. "
            "You MUST output valid JSON ONLY."
        )

        user_prompt = f"""
Generate a comprehensive mind map for the topic: "{topic}"

The response MUST be valid JSON data structured exactly like this:
{{
  "nodes": [
    {{"id": "node-1", "title": "Main Concept", "note": "Detailed explanation here.", "x": 0, "y": 200}},
    ...
  ],
  "edges": [
    {{"source": "node-1", "target": "node-2"}}
  ]
}}

Guidelines for positions (x, y):
- The central node should be at (0, 200).
- Level 1 children should be at x = 250 to 300, spread vertically for their y-coordinates (e.g. 0, 150, 300, 450).
- Level 2 children should be at x = 550 to 600, spread vertically so they don't overlap.
- Ensure the tree expands generally from left to right.
DO NOT wrap the response in markdown blocks (like ```json), output raw JSON only.
"""
        response_text = self.llm.generate(prompt=user_prompt, system_prompt=system_prompt, temperature=0.7, max_tokens=2500)
        
        if not response_text:
            logger.error("LLM failed to generate a mindmap response.")
            raise ValueError("Failed to generate mind map from AI.")

        # Clean up any potential markdown formatting
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        try:
            data = json.loads(cleaned_text.strip())
        except json.JSONDecodeError:
            # Try to extract a JSON block using regex if parsing failed
            match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception as e:
                    logger.error(f"Failed to parse extracted JSON: {e}")
                    raise ValueError("AI returned malformed JSON.")
            else:
                logger.error(f"No JSON found in LLM response: {cleaned_text[:200]}")
                raise ValueError("AI returned invalid data format.")
        
        nodes = []
        for n in data.get("nodes", []):
            nodes.append(GeniusMindMapNode(
                id=str(n.get("id", "")),
                title=str(n.get("title", "Untitled")),
                note=str(n.get("note", "")),
                x=int(n.get("x", 0)),
                y=int(n.get("y", 0))
            ))
            
        edges = []
        for e in data.get("edges", []):
            edges.append(GeniusMindMapEdge(
                source=str(e.get("source", "")),
                target=str(e.get("target", ""))
            ))
            
        return GeniusMindMapResponse(
            success=True,
            nodes=nodes,
            edges=edges
        )

def get_genius_mindmap_generator() -> GeniusMindmapGenerator:
    return GeniusMindmapGenerator()
