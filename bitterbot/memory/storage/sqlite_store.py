import sqlite3
from typing import List, Dict, Any
import json
from datetime import datetime

class SQLiteStore:
    """SQLite database wrapper for structured data"""
    
    def __init__(self, db_path: str = "bitterbot.db"):
        self.db_path = db_path
        self.conn = None
        self._init_connection()
        
    def _init_connection(self):
        """Initialize database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    async def execute(self, query: str, params: tuple = None):
        """Execute a query"""
        # TODO: Implement async execution
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self.conn.commit()
        return cursor
        
    async def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """Fetch all results"""
        cursor = await self.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
        
    async def fetch_one(self, query: str, params: tuple = None) -> Dict:
        """Fetch single result"""
        cursor = await self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()