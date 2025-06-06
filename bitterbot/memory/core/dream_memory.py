from typing import List, Dict, Any
from datetime import datetime
import json

class DreamMemory:
    """Storage for dream-generated insights and explorations"""
    
    def __init__(self, dream_log_path: str = "bitterbot_dreams.json"):
        self.dream_log_path = dream_log_path
        self.dreams = self._load_dreams()
        
    def _load_dreams(self) -> List[Dict[str, Any]]:
        """Load existing dream logs"""
        try:
            with open(self.dream_log_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
            
    async def store_dream(self, dream_content: Dict[str, Any]):
        """Store a dream session"""
        dream_entry = {
            'timestamp': datetime.now().isoformat(),
            'content': dream_content,
            'insights': [],
            'curiosity_seeds': []
        }
        self.dreams.append(dream_entry)
        # TODO: Implement persistence
        
    async def add_insight(self, dream_id: int, insight: str):
        """Add an insight from a dream"""
        if 0 <= dream_id < len(self.dreams):
            self.dreams[dream_id]['insights'].append({
                'text': insight,
                'timestamp': datetime.now().isoformat()
            })
            
    async def get_recent_dreams(self, k: int = 5) -> List[Dict[str, Any]]:
        """Get k most recent dreams"""
        return self.dreams[-k:] if self.dreams else []
        
    def save(self):
        """Persist dreams to disk"""
        with open(self.dream_log_path, 'w') as f:
            json.dump(self.dreams, f, indent=2)