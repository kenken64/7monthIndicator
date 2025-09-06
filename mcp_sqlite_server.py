#!/usr/bin/env python3
"""
MCP server for SQLite databases used by the trading bot.
Provides read-only access to trading_bot.db and trading_data.db via HTTP API.
"""

import json
import sqlite3
import sys
from typing import Dict, List, Any, Optional
import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import threading
import signal
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_server.log')
    ]
)

class SQLiteMCPServer:
    def __init__(self, db_paths: List[str]):
        self.db_paths = db_paths
        self.connections = {}
        self.logger = logging.getLogger(__name__)
        
    def connect_to_db(self, db_path: str) -> sqlite3.Connection:
        """Connect to SQLite database with connection reuse."""
        if db_path not in self.connections:
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found: {db_path}")
            self.connections[db_path] = sqlite3.connect(db_path, check_same_thread=False)
            self.connections[db_path].row_factory = sqlite3.Row
            self.logger.info(f"Connected to database: {db_path}")
        return self.connections[db_path]
    
    def list_tables(self, db_path: str) -> List[str]:
        """Get list of tables in database."""
        conn = self.connect_to_db(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]
    
    def describe_table(self, db_path: str, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        conn = self.connect_to_db(db_path)
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_table_count(self, db_path: str, table_name: str) -> int:
        """Get row count for a table."""
        conn = self.connect_to_db(db_path)
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    
    def execute_query(self, db_path: str, query: str, limit: int = 100) -> Dict[str, Any]:
        """Execute a SELECT query safely."""
        conn = self.connect_to_db(db_path)
        
        # Clean and validate query
        query = query.strip()
        if not query.upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        # Add limit if not present and limit is specified
        if limit > 0 and 'LIMIT' not in query.upper():
            query = f"{query.rstrip(';')} LIMIT {limit}"
        
        try:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            return {
                "query": query,
                "columns": [description[0] for description in cursor.description] if cursor.description else [],
                "rows": [dict(row) for row in rows],
                "count": len(rows),
                "executed_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            raise
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get comprehensive database information."""
        info = {}
        for db_path in self.db_paths:
            if os.path.exists(db_path):
                try:
                    tables = self.list_tables(db_path)
                    table_info = {}
                    for table in tables:
                        table_info[table] = {
                            "schema": self.describe_table(db_path, table),
                            "row_count": self.get_table_count(db_path, table)
                        }
                    
                    info[db_path] = {
                        "status": "connected",
                        "tables": tables,
                        "table_info": table_info,
                        "file_size": os.path.getsize(db_path),
                        "last_modified": os.path.getmtime(db_path)
                    }
                except Exception as e:
                    info[db_path] = {"status": "error", "error": str(e)}
            else:
                info[db_path] = {"status": "not_found", "error": "Database file not found"}
        return info
    
    def close_connections(self):
        """Close all database connections."""
        for db_path, conn in self.connections.items():
            conn.close()
            self.logger.info(f"Closed connection to: {db_path}")
        self.connections.clear()

class MCPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, mcp_server=None, **kwargs):
        self.mcp_server = mcp_server
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logging.getLogger(__name__).info(f"{self.client_address[0]} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if path == '/':
                self._handle_root()
            elif path == '/info':
                self._handle_info()
            elif path == '/tables':
                self._handle_tables(query_params)
            elif path == '/query':
                self._handle_query_get(query_params)
            else:
                self._send_error(404, "Endpoint not found")
                
        except Exception as e:
            logging.getLogger(__name__).error(f"GET request error: {e}")
            self._send_error(500, str(e))
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            if path == '/query':
                self._handle_query_post(post_data)
            else:
                self._send_error(404, "Endpoint not found")
                
        except Exception as e:
            logging.getLogger(__name__).error(f"POST request error: {e}")
            self._send_error(500, str(e))
    
    def _handle_root(self):
        """Handle root endpoint."""
        response = {
            "service": "MCP SQLite Server",
            "status": "running",
            "databases": self.mcp_server.db_paths,
            "endpoints": {
                "GET /": "This help message",
                "GET /info": "Database information",
                "GET /tables?db=<db_path>": "List tables in database",
                "GET /query?db=<db_path>&q=<query>&limit=<limit>": "Execute query",
                "POST /query": "Execute query (JSON body: {db, query, limit})"
            }
        }
        self._send_json_response(response)
    
    def _handle_info(self):
        """Handle database info endpoint."""
        info = self.mcp_server.get_database_info()
        self._send_json_response(info)
    
    def _handle_tables(self, query_params):
        """Handle tables list endpoint."""
        db_path = query_params.get('db', [None])[0]
        if not db_path:
            self._send_error(400, "Missing 'db' parameter")
            return
        
        try:
            tables = self.mcp_server.list_tables(db_path)
            response = {
                "database": db_path,
                "tables": tables
            }
            self._send_json_response(response)
        except Exception as e:
            self._send_error(400, str(e))
    
    def _handle_query_get(self, query_params):
        """Handle query execution via GET."""
        db_path = query_params.get('db', [None])[0]
        query = query_params.get('q', [None])[0]
        limit = int(query_params.get('limit', [100])[0])
        
        if not db_path or not query:
            self._send_error(400, "Missing 'db' or 'q' parameters")
            return
        
        try:
            result = self.mcp_server.execute_query(db_path, query, limit)
            self._send_json_response(result)
        except Exception as e:
            self._send_error(400, str(e))
    
    def _handle_query_post(self, post_data):
        """Handle query execution via POST."""
        try:
            data = json.loads(post_data.decode('utf-8'))
            db_path = data.get('db')
            query = data.get('query')
            limit = data.get('limit', 100)
            
            if not db_path or not query:
                self._send_error(400, "Missing 'db' or 'query' in JSON body")
                return
            
            result = self.mcp_server.execute_query(db_path, query, limit)
            self._send_json_response(result)
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON in request body")
        except Exception as e:
            self._send_error(400, str(e))
    
    def _send_json_response(self, data):
        """Send JSON response."""
        json_data = json.dumps(data, indent=2, default=str)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(json_data))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def _send_error(self, code, message):
        """Send error response."""
        error_data = {"error": message, "code": code}
        json_data = json.dumps(error_data, indent=2)
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(json_data))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))

class MCPServer:
    def __init__(self, db_paths: List[str], host='localhost', port=8080):
        self.mcp_server = SQLiteMCPServer(db_paths)
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """Start the MCP server."""
        handler = lambda *args, **kwargs: MCPRequestHandler(*args, mcp_server=self.mcp_server, **kwargs)
        self.server = HTTPServer((self.host, self.port), handler)
        
        self.logger.info(f"Starting MCP server on {self.host}:{self.port}")
        self.logger.info(f"Available databases: {self.mcp_server.db_paths}")
        
        # Handle graceful shutdown
        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal, stopping server...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start server in thread for graceful shutdown
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        self.logger.info("MCP server started successfully")
        self.logger.info(f"Access at: http://{self.host}:{self.port}")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the MCP server."""
        if self.server:
            self.logger.info("Stopping MCP server...")
            self.server.shutdown()
            self.server.server_close()
        
        if self.mcp_server:
            self.mcp_server.close_connections()
        
        self.logger.info("MCP server stopped")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mcp_sqlite_server.py <db_path1> [db_path2] ... [--port PORT] [--host HOST]")
        sys.exit(1)
    
    # Parse arguments
    db_paths = []
    host = 'localhost'
    port = 8080
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        elif arg == '--host' and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
            i += 2
        elif not arg.startswith('--'):
            db_paths.append(arg)
            i += 1
        else:
            i += 1
    
    if not db_paths:
        print("Error: No database paths specified")
        sys.exit(1)
    
    # Start server
    server = MCPServer(db_paths, host, port)
    server.start()

if __name__ == "__main__":
    main()