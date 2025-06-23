"""
Database initialization script for the custom search engine.

This script provides utilities for initializing the custom search engine database,
managing seed data, and performing database maintenance tasks.
"""

import asyncio
import logging
import sqlite3
from typing import List, Dict, Any

from .custom_search_engine import CustomSearchEngine

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Handles database initialization and setup for the custom search engine."""
    
    def __init__(self, db_path: str = "web_scout_search.db"):
        self.db_path = db_path
    
    def initialize_database(self):
        """Initialize the database with all required tables and indexes."""
        logger.info("Initializing custom search engine database")
        
        # Create a temporary CustomSearchEngine instance to initialize the database
        engine = CustomSearchEngine(self.db_path)
        logger.info(f"Database initialized at: {self.db_path}")
    
    def add_seed_urls(self, urls: List[str], priority: int = 5) -> int:
        """Add seed URLs to the crawl queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        added_count = 0
        
        try:
            for url in urls:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                
                cursor.execute("""
                    INSERT OR IGNORE INTO crawl_queue (url, domain, priority)
                    VALUES (?, ?, ?)
                """, (url, domain, priority))
                
                if cursor.rowcount > 0:
                    added_count += 1
            
            conn.commit()
            logger.info(f"Added {added_count} new seed URLs to crawl queue")
            
        except Exception as e:
            logger.error(f"Failed to add seed URLs: {e}")
            conn.rollback()
            raise
        
        finally:
            conn.close()
        
        return added_count
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get current database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Table row counts
            tables = ['pages', 'links', 'images', 'crawl_queue']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Queue status breakdown
            cursor.execute("SELECT status, COUNT(*) FROM crawl_queue GROUP BY status")
            stats['queue_status'] = dict(cursor.fetchall())
            
            # Content type breakdown
            cursor.execute("SELECT content_type, COUNT(*) FROM pages GROUP BY content_type")
            stats['content_types'] = dict(cursor.fetchall())
            
            # Domain statistics
            cursor.execute("SELECT COUNT(DISTINCT domain) FROM pages")
            stats['unique_domains'] = cursor.fetchone()[0]
            
            # Database file size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            stats['db_size_bytes'] = page_count * page_size
            
            return stats
        
        finally:
            conn.close()
    
    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Clean up old crawled data to manage database size."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Remove old pages with low quality scores
            cursor.execute("""
                DELETE FROM pages 
                WHERE crawl_timestamp < datetime('now', '-{} days')
                AND quality_score < 0.3
                AND page_rank < 0.1
            """.format(days_old))
            
            deleted_pages = cursor.rowcount
            
            # Clean up orphaned records
            cursor.execute("DELETE FROM links WHERE from_page_id NOT IN (SELECT id FROM pages)")
            cursor.execute("DELETE FROM images WHERE page_id NOT IN (SELECT id FROM pages)")
            
            # Clean up completed/failed crawl queue entries
            cursor.execute("""
                DELETE FROM crawl_queue 
                WHERE status IN ('completed', 'failed') 
                AND last_attempt < datetime('now', '-7 days')
            """)
            
            # Rebuild FTS index
            cursor.execute("INSERT INTO pages_fts(pages_fts) VALUES('rebuild')")
            
            # Vacuum to reclaim space
            cursor.execute("VACUUM")
            
            conn.commit()
            logger.info(f"Cleaned up {deleted_pages} old pages and optimized database")
            
            return deleted_pages
        
        finally:
            conn.close()
    
    def export_crawl_queue(self, status: str = "pending", limit: int = 1000) -> List[Dict[str, Any]]:
        """Export crawl queue entries for analysis or backup."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT url, domain, priority, scheduled_time, retry_count, status, error_message
                FROM crawl_queue
                WHERE status = ?
                ORDER BY priority DESC, scheduled_time ASC
                LIMIT ?
            """, (status, limit))
            
            columns = ['url', 'domain', 'priority', 'scheduled_time', 'retry_count', 'status', 'error_message']
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
        
        finally:
            conn.close()
    
    def reset_failed_crawls(self) -> int:
        """Reset failed crawl attempts back to pending status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE crawl_queue 
                SET status = 'pending', retry_count = 0, error_message = NULL,
                    scheduled_time = datetime('now', '+' || (retry_count * 10) || ' minutes')
                WHERE status = 'failed' AND retry_count < 5
            """)
            
            reset_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Reset {reset_count} failed crawl attempts to pending")
            return reset_count
        
        finally:
            conn.close()


async def main():
    """Main function for running database initialization tasks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Web-Scout Custom Search Engine Database Manager")
    parser.add_argument("--db-path", default="web_scout_search.db", help="Database file path")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--cleanup", type=int, metavar="DAYS", help="Clean up data older than N days")
    parser.add_argument("--reset-failed", action="store_true", help="Reset failed crawl attempts")
    parser.add_argument("--add-urls", nargs="+", help="Add URLs to crawl queue")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    db_init = DatabaseInitializer(args.db_path)
    
    if args.init:
        db_init.initialize_database()
        print("Database initialized successfully")
    
    if args.stats:
        stats = db_init.get_database_stats()
        print("\nDatabase Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    if args.cleanup:
        deleted = db_init.cleanup_old_data(args.cleanup)
        print(f"Cleaned up {deleted} old records")
    
    if args.reset_failed:
        reset_count = db_init.reset_failed_crawls()
        print(f"Reset {reset_count} failed crawl attempts")
    
    if args.add_urls:
        added = db_init.add_seed_urls(args.add_urls)
        print(f"Added {added} URLs to crawl queue")


if __name__ == "__main__":
    asyncio.run(main())