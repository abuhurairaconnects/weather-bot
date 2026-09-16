"""
Database manager using aiosqlite for persistence.
Stores users, settings, favorites, alert preferences, and search logs.
"""
import aiosqlite
from typing import Optional, Dict, Any, List
from config import DB_PATH, DEFAULT_LANGUAGE, DEFAULT_TEMP_UNIT

async def init_db():
    """Initialize database tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                language TEXT DEFAULT 'bn',
                temp_unit TEXT DEFAULT 'C',
                default_city TEXT,
                default_lat REAL,
                default_lon REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked INTEGER DEFAULT 0
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                city_name TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                user_id INTEGER PRIMARY KEY,
                city_name TEXT,
                lat REAL,
                lon REAL,
                rain_alert INTEGER DEFAULT 0,
                severe_alert INTEGER DEFAULT 1,
                morning_report INTEGER DEFAULT 0,
                evening_report INTEGER DEFAULT 0,
                morning_time TEXT DEFAULT '07:00',
                evening_time TEXT DEFAULT '19:00',
                quiet_start TEXT DEFAULT '23:00',
                quiet_end TEXT DEFAULT '06:00',
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                city_name TEXT,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()

async def get_or_create_user(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve existing user or insert a new user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
        
        # Create new user
        await db.execute(
            """
            INSERT INTO users (user_id, username, first_name, language, temp_unit)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, username or "", first_name or "", DEFAULT_LANGUAGE, DEFAULT_TEMP_UNIT)
        )
        # Create default alerts row
        await db.execute(
            """
            INSERT OR IGNORE INTO alerts (user_id) VALUES (?)
            """,
            (user_id,)
        )
        await db.commit()
        
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {}

async def update_user_setting(user_id: int, key: str, value: Any):
    """Update a specific column in the users table."""
    allowed_keys = {"language", "temp_unit", "default_city", "default_lat", "default_lon", "is_blocked"}
    if key not in allowed_keys:
        raise ValueError(f"Invalid column: {key}")
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
        await db.commit()

async def set_default_location(user_id: int, city_name: str, lat: float, lon: float):
    """Set the user's default/home location."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE users
            SET default_city = ?, default_lat = ?, default_lon = ?
            WHERE user_id = ?
            """,
            (city_name, lat, lon, user_id)
        )
        # Also sync to alerts default location if not already set
        await db.execute(
            """
            UPDATE alerts
            SET city_name = ?, lat = ?, lon = ?
            WHERE user_id = ? AND (lat IS NULL OR lon IS NULL)
            """,
            (city_name, lat, lon, user_id)
        )
        await db.commit()

async def add_favorite(user_id: int, tag: str, city_name: str, lat: float, lon: float) -> int:
    """Add a favorite location (tag can be 'home', 'work', 'university', 'custom')."""
    async with aiosqlite.connect(DB_PATH) as db:
        # If tag is home or work, replace existing one with the same tag
        if tag in ('home', 'work', 'university'):
            await db.execute("DELETE FROM favorites WHERE user_id = ? AND tag = ?", (user_id, tag))
        
        cursor = await db.execute(
            """
            INSERT INTO favorites (user_id, tag, city_name, lat, lon)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, tag, city_name, lat, lon)
        )
        await db.commit()
        return cursor.lastrowid

async def get_favorites(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve all favorite locations for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM favorites WHERE user_id = ? ORDER BY id ASC", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def delete_favorite(user_id: int, fav_id: int):
    """Delete a favorite location by its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM favorites WHERE id = ? AND user_id = ?", (fav_id, user_id))
        await db.commit()

async def get_alert_settings(user_id: int) -> Dict[str, Any]:
    """Get alert and daily report preferences for a user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM alerts WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            # Insert default if not present
            await db.execute("INSERT OR IGNORE INTO alerts (user_id) VALUES (?)", (user_id,))
            await db.commit()
            async with db.execute("SELECT * FROM alerts WHERE user_id = ?", (user_id,)) as cur2:
                r2 = await cur2.fetchone()
                return dict(r2) if r2 else {}

async def update_alert_settings(user_id: int, **kwargs):
    """Update alert settings dynamically."""
    valid_keys = {
        "city_name", "lat", "lon", "rain_alert", "severe_alert",
        "morning_report", "evening_report", "morning_time", "evening_time",
        "quiet_start", "quiet_end"
    }
    updates = []
    values = []
    for k, v in kwargs.items():
        if k in valid_keys:
            updates.append(f"{k} = ?")
            values.append(v)
            
    if not updates:
        return
    
    values.append(user_id)
    sql = f"UPDATE alerts SET {', '.join(updates)} WHERE user_id = ?"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(sql, tuple(values))
        await db.commit()

async def get_all_subscribers_for_alerts() -> List[Dict[str, Any]]:
    """Fetch all users who have active rain, severe, or daily reports enabled."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        sql = """
            SELECT a.*, u.language, u.temp_unit, u.is_blocked
            FROM alerts a
            JOIN users u ON a.user_id = u.user_id
            WHERE u.is_blocked = 0 AND (
                a.rain_alert = 1 OR a.severe_alert = 1 OR a.morning_report = 1 OR a.evening_report = 1
            ) AND a.lat IS NOT NULL AND a.lon IS NOT NULL
        """
        async with db.execute(sql) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def log_search(user_id: int, city_name: str):
    """Record a city search query."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO search_logs (user_id, city_name) VALUES (?, ?)",
            (user_id, city_name)
        )
        await db.commit()

async def get_admin_stats() -> Dict[str, Any]:
    """Retrieve statistics for the admin dashboard."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Total users
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        
        # Blocked users
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1") as cur:
            blocked_users = (await cur.fetchone())[0]
            
        # Active alert subscriptions
        async with db.execute("SELECT COUNT(*) FROM alerts WHERE rain_alert = 1 OR morning_report = 1") as cur:
            active_alerts = (await cur.fetchone())[0]
            
        # Most searched locations (Top 5)
        top_locations = []
        async with db.execute("""
            SELECT city_name, COUNT(*) as count 
            FROM search_logs 
            GROUP BY city_name 
            ORDER BY count DESC 
            LIMIT 5
        """) as cur:
            rows = await cur.fetchall()
            top_locations = [(r[0], r[1]) for r in rows]
            
        return {
            "total_users": total_users,
            "blocked_users": blocked_users,
            "active_alerts": active_alerts,
            "top_locations": top_locations
        }

async def get_all_user_ids() -> List[int]:
    """Get all non-blocked user IDs for announcements/broadcasts."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_blocked = 0") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]
