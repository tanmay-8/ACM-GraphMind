"""
LLM Extractor - Converts user text to structured graph format.

Input: Raw user text
Output: Structured JSON with nodes and relationships

Example Output:
{
    "nodes": [
        {
            "type": "Asset",
            "properties": {
                "name": "HDFC Mutual Fund",
                "value": 50000,
                "asset_type": "mutual_fund"
            }
        }
    ],
    "relationships": [
        {
            "type": "OWNS",
            "from_node": "User",
            "to_node": "Asset",
            "properties": {
                "acquired_date": "2026-02-21"
            }
        }
    ]
}
"""

from typing import Dict, List, Any
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class LLMExtractor:
    """
    LLM-based entity and relationship extractor.
    """
    
    def __init__(self):
        """Initialize the LLM extractor."""
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
    
    def extract(self, text: str, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract structured entities and relationships from text.
        
        Args:
            text: User input text
            user_id: User identifier for context
            
        Returns:
            Dictionary with 'nodes' and 'relationships' lists
        """
        if not self.model:
            return self._fallback_extraction(text, user_id)
        
        try:
            prompt = self._build_extraction_prompt(text)
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            extracted_data = json.loads(response_text)
            
            # Add IDs to nodes if not present
            for node in extracted_data.get("nodes", []):
                if "id" not in node.get("properties", {}):
                    if "properties" not in node:
                        node["properties"] = {}
                    node["properties"]["id"] = f"{node['type'].lower()}_{uuid.uuid4().hex[:8]}"
            
            # Validate and return
            if self.validate_schema(extracted_data):
                return extracted_data
            else:
                return self._fallback_extraction(text, user_id)
                
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            return self._fallback_extraction(text, user_id)
    
    def _build_extraction_prompt(self, text: str) -> str:
        """Build the extraction prompt for LLM."""
        return f"""You are a financial data extraction system. Extract structured entities and relationships from user messages.

Entity Types:
- Asset: Financial assets (stocks, mutual funds, bonds, real estate, gold, etc.)
- Goal: Financial goals (retirement, education, house purchase, emergency fund, etc.)
- Transaction: Financial transactions (investments, withdrawals, deposits, etc.)
- RiskProfile: User's risk tolerance (low, moderate, high, aggressive)

Relationship Types:
- OWNS: User owns an asset
- HAS_GOAL: User has a financial goal
- MADE_TRANSACTION: User made a transaction
- CONTRIBUTES_TO: Asset contributes to a goal
- HAS_RISK: Asset has a risk level

Extract from this message: "{text}"

Return ONLY valid JSON in this exact format:
{{
  "nodes": [
    {{
      "type": "Asset",
      "properties": {{
        "name": "Asset name",
        "current_value": 50000,
        "asset_type": "mutual_fund"
      }}
    }}
  ],
  "relationships": [
    {{
      "type": "OWNS",
      "from_type": "User",
      "to_type": "Asset",
      "from_name": "user",
      "to_name": "Asset name",
      "properties": {{}}
    }}
  ]
}}

Rules:
1. Extract all financial entities mentioned
2. Infer reasonable property values
3. Include only relevant relationships
4. Use proper types from the list above
5. Return valid JSON only, no additional text

JSON:"""
    
    def _fallback_extraction(self, text: str, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Fallback simple keyword-based extraction."""
        nodes = []
        relationships = []
        
        text_lower = text.lower()
        
        # Simple pattern matching for investments
        if any(word in text_lower for word in ["invested", "bought", "purchased"]):
            # Try to extract asset name and amount
            words = text.split()
            for i, word in enumerate(words):
                if word.lower() in ["in", "into"] and i + 1 < len(words):
                    asset_name = " ".join(words[i+1:i+4])  # Next 3 words as asset name
                    
                    # Try to find amount
                    for w in words:
                        if w.replace(",", "").replace(".", "").isdigit():
                            amount = float(w.replace(",", ""))
                            
                            asset_id = f"asset_{uuid.uuid4().hex[:8]}"
                            nodes.append({
                                "type": "Asset",
                                "properties": {
                                    "id": asset_id,
                                    "name": asset_name.strip(),
                                    "current_value": amount,
                                    "asset_type": "investment"
                                }
                            })
                            
                            relationships.append({
                                "type": "OWNS",
                                "from_type": "User",
                                "to_type": "Asset",
                                "from_name": "user",
                                "to_name": asset_name.strip(),
                                "properties": {
                                    "acquired_date": datetime.now().strftime("%Y-%m-%d")
                                }
                            })
                            break
                    break
        
        return {
            "nodes": nodes,
            "relationships": relationships
        }
    
    def validate_schema(self, extracted_data: Dict[str, Any]) -> bool:
        """
        Validate that extracted data matches expected schema.
        
        Args:
            extracted_data: Extracted nodes and relationships
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(extracted_data, dict):
            return False
        
        if "nodes" not in extracted_data or "relationships" not in extracted_data:
            return False
        
        # Validate nodes
        for node in extracted_data.get("nodes", []):
            if "type" not in node or "properties" not in node:
                return False
        
        # Validate relationships
        for rel in extracted_data.get("relationships", []):
            if "type" not in rel:
                return False
        
        return True
