import sqlite3
from datetime import datetime
import json
from typing import Dict, Any, List, Optional
from ..config import DB_PATH
from .base import BaseTool, ToolType

class TodoTool(BaseTool):
    def __init__(self):
        super().__init__("todo", ToolType.PLANNING)
        self.db_path = DB_PATH
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure the todos table exists"""
        print("Ensuring table exists")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    priority INTEGER,
                    due_date TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    tags TEXT,
                    metadata TEXT
                )
            """)
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute todo operations"""
        action = params.get("action")
        
        actions = {
            "add": self._add_todo,
            "update": self._update_todo,
            "complete": self._complete_todo,
            "list": self._list_todos,
            "get": self._get_todo,
            "delete": self._delete_todo
        }
        
        if action not in actions:
            return {"status": "error", "message": f"Unknown action: {action}"}
            
        try:
            return actions[action](params)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _add_todo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new todo"""
        required = ["title"]
        if not all(params.get(field) for field in required):
            return {"status": "error", "message": f"Missing required fields: {required}"}
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO todos (
                    title, description, status, priority, due_date,
                    created_at, tags, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                params["title"],
                params.get("description"),
                params.get("status", "pending"),
                params.get("priority", 3),
                params.get("due_date"),
                datetime.now().isoformat(),
                json.dumps(params.get("tags", [])),
                json.dumps(params.get("metadata", {}))
            ))
            
            todo_id = cursor.lastrowid
            return {
                "status": "success",
                "message": "Todo created successfully",
                "todo_id": todo_id
            }

    def _update_todo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing todo"""
        todo_id = params.get("id")
        if not todo_id:
            return {"status": "error", "message": "Missing todo id"}
            
        update_fields = []
        values = []
        
        field_mapping = {
            "title": "title",
            "description": "description",
            "status": "status",
            "priority": "priority",
            "due_date": "due_date",
            "tags": ("tags", json.dumps),
            "metadata": ("metadata", json.dumps)
        }
        
        for param_key, db_info in field_mapping.items():
            if param_key in params:
                db_field = db_info if isinstance(db_info, str) else db_info[0]
                transform = (lambda x: x) if isinstance(db_info, str) else db_info[1]
                update_fields.append(f"{db_field} = ?")
                values.append(transform(params[param_key]))
        
        if not update_fields:
            return {"status": "error", "message": "No fields to update"}
            
        values.append(todo_id)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE todos SET {', '.join(update_fields)} WHERE id = ?",
                values
            )
            return {"status": "success", "message": "Todo updated successfully"}

    def _complete_todo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a todo as completed"""
        todo_id = params.get("id")
        if not todo_id:
            return {"status": "error", "message": "Missing todo id"}
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE todos 
                SET status = 'completed', completed_at = ? 
                WHERE id = ?
            """, (datetime.now().isoformat(), todo_id))
            return {"status": "success", "message": "Todo marked as completed"}

    def _list_todos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List todos with optional filters"""
        query = "SELECT * FROM todos"
        conditions = []
        values = []
        
        if status := params.get("status"):
            conditions.append("status = ?")
            values.append(status)
            
        if priority := params.get("priority"):
            conditions.append("priority = ?")
            values.append(priority)
            
        if tags := params.get("tags"):
            for tag in tags:
                conditions.append("tags LIKE ?")
                values.append(f"%{tag}%")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY priority ASC, created_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, values)
            todos = [{**dict(row)} for row in cursor.fetchall()]
            
            # Parse JSON fields
            for todo in todos:
                if todo["tags"]:
                    todo["tags"] = json.loads(todo["tags"])
                if todo["metadata"]:
                    todo["metadata"] = json.loads(todo["metadata"])
            
            return {"status": "success", "todos": todos}

    def _get_todo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific todo by id"""
        todo_id = params.get("id")
        if not todo_id:
            return {"status": "error", "message": "Missing todo id"}
            
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
            if todo := cursor.fetchone():
                todo_dict = dict(todo)
                if todo_dict["tags"]:
                    todo_dict["tags"] = json.loads(todo_dict["tags"])
                if todo_dict["metadata"]:
                    todo_dict["metadata"] = json.loads(todo_dict["metadata"])
                return {"status": "success", "todo": todo_dict}
            return {"status": "error", "message": "Todo not found"}

    def _delete_todo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a todo"""
        todo_id = params.get("id")
        if not todo_id:
            return {"status": "error", "message": "Missing todo id"}
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
            return {"status": "success", "message": "Todo deleted successfully"}

    def get_description(self) -> str:
        return """
        Todo Management Tool
        Actions:
        - add: Create a new todo
          Parameters: {
            "action": "add",
            "title": "required",
            "description": "optional",
            "status": "pending/in_progress/completed/cancelled",
            "priority": 1-5 (1 highest),
            "due_date": "YYYY-MM-DD",
            "tags": ["tag1", "tag2"],
            "metadata": {"key": "value"}
          }
        - update: Update an existing todo
          Parameters: {
            "action": "update",
            "id": "todo_id",
            "title": "new title",
            ... (same fields as add)
          }
        - complete: Mark a todo as completed
          Parameters: {
            "action": "complete",
            "id": "todo_id"
          }
        - list: List todos with optional filters
          Parameters: {
            "action": "list",
            "status": "optional filter",
            "priority": "optional filter",
            "tags": ["optional", "tag", "filters"]
          }
        - get: Get a specific todo
          Parameters: {
            "action": "get",
            "id": "todo_id"
          }
        - delete: Delete a todo
          Parameters: {
            "action": "delete",
            "id": "todo_id"
          }
        """