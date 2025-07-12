import os
from typing import Optional

# =============================================================================
# Discord Bot Configuration
# =============================================================================

# Discord Bot Token - Get this from Discord Developer Portal
# https://discord.com/developers/applications
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'your_bot_token_here')

# Bot command prefix
COMMAND_PREFIX = os.getenv('BOT_PREFIX', '!')

# Bot description
BOT_DESCRIPTION = "West End Games Star Wars TTRPG Discord Bot"

# =============================================================================
# Database Configuration
# =============================================================================

# Database URL - SQLite by default, can be changed to PostgreSQL/MySQL for production
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///starwars_bot.db')

# Alternative database configurations (uncomment as needed):
# PostgreSQL: 'postgresql://username:password@localhost/starwars_bot'
# MySQL: 'mysql://username:password@localhost/starwars_bot'

# Database connection pool settings (for production databases)
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))

# =============================================================================
# Bot Behavior Configuration
# =============================================================================

# Maximum number of character sheets per user
MAX_SHEETS_PER_USER = int(os.getenv('MAX_SHEETS_PER_USER', '10'))

# Maximum file size for character sheet uploads (in bytes)
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '1048576'))  # 1MB default

# Allowed file extensions for character sheet uploads
ALLOWED_FILE_EXTENSIONS = ['.json', '.csv', '.txt', '.text']

# Default dice roller settings
USE_WILD_DIE = os.getenv('USE_WILD_DIE', 'true').lower() == 'true'
SHOW_INDIVIDUAL_DICE = os.getenv('SHOW_INDIVIDUAL_DICE', 'true').lower() == 'true'

# =============================================================================
# Role and Permission Configuration
# =============================================================================

# Role names that grant GM/DM privileges
GM_ROLE_NAMES = [
    'GM', 'DM', 'Game Master', 'Dungeon Master', 
    'Gamemaster', 'Game-Master', 'StarWars-GM'
]

# Role names that can use admin commands (if implemented)
ADMIN_ROLE_NAMES = ['Admin', 'Administrator', 'Bot Admin', 'Server Admin']

# Whether GMs can view all character sheets by default
GM_CAN_VIEW_ALL_SHEETS = os.getenv('GM_CAN_VIEW_ALL_SHEETS', 'true').lower() == 'true'

# Whether GMs can delete any character sheet
GM_CAN_DELETE_ANY_SHEET = os.getenv('GM_CAN_DELETE_ANY_SHEET', 'false').lower() == 'true'

# =============================================================================
# Logging Configuration
# =============================================================================

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# Log file path (None to disable file logging)
LOG_FILE = os.getenv('LOG_FILE', 'starwars_bot.log')

# Whether to log dice rolls to database
LOG_DICE_ROLLS = os.getenv('LOG_DICE_ROLLS', 'true').lower() == 'true'

# Whether to log command usage
LOG_COMMANDS = os.getenv('LOG_COMMANDS', 'true').lower() == 'true'

# =============================================================================
# Feature Flags
# =============================================================================

# Enable/disable specific features
ENABLE_CAMPAIGNS = os.getenv('ENABLE_CAMPAIGNS', 'false').lower() == 'true'
ENABLE_GAME_SESSIONS = os.getenv('ENABLE_GAME_SESSIONS', 'false').lower() == 'true'
ENABLE_ROLL_HISTORY = os.getenv('ENABLE_ROLL_HISTORY', 'true').lower() == 'true'
ENABLE_CHARACTER_BACKUP = os.getenv('ENABLE_CHARACTER_BACKUP', 'true').lower() == 'true'

# =============================================================================
# WEG Star Wars Specific Configuration
# =============================================================================

# Default starting values for new characters
DEFAULT_FORCE_POINTS = int(os.getenv('DEFAULT_FORCE_POINTS', '1'))
DEFAULT_CHARACTER_POINTS = int(os.getenv('DEFAULT_CHARACTER_POINTS', '5'))
DEFAULT_CREDITS = int(os.getenv('DEFAULT_CREDITS', '1000'))

# Force power difficulty modifiers
FORCE_POWER_DIFFICULTY_MODIFIER = int(os.getenv('FORCE_POWER_DIFFICULTY_MODIFIER', '0'))

# Whether to automatically apply dark side points for failed Force rolls with wild die 1
AUTO_DARK_SIDE_TEMPTATION = os.getenv('AUTO_DARK_SIDE_TEMPTATION', 'false').lower() == 'true'

# =============================================================================
# Discord Embed Configuration
# =============================================================================

# Default embed colors (hex values)
EMBED_COLOR_SUCCESS = int(os.getenv('EMBED_COLOR_SUCCESS', '0x00ff00'), 16)  # Green
EMBED_COLOR_ERROR = int(os.getenv('EMBED_COLOR_ERROR', '0xff0000'), 16)      # Red
EMBED_COLOR_INFO = int(os.getenv('EMBED_COLOR_INFO', '0x0099ff'), 16)        # Blue
EMBED_COLOR_WARNING = int(os.getenv('EMBED_COLOR_WARNING', '0xffaa00'), 16)  # Orange
EMBED_COLOR_DICE = int(os.getenv('EMBED_COLOR_DICE', '0xff6600'), 16)        # Orange-Red

# Whether to use embeds for responses (fallback to plain text if False)
USE_EMBEDS = os.getenv('USE_EMBEDS', 'true').lower() == 'true'

# =============================================================================
# Rate Limiting and Spam Protection
# =============================================================================

# Cooldown between dice rolls (in seconds)
DICE_ROLL_COOLDOWN = int(os.getenv('DICE_ROLL_COOLDOWN', '2'))

# Cooldown between character sheet operations (in seconds)
SHEET_OPERATION_COOLDOWN = int(os.getenv('SHEET_OPERATION_COOLDOWN', '5'))

# Maximum number of dice that can be rolled at once
MAX_DICE_PER_ROLL = int(os.getenv('MAX_DICE_PER_ROLL', '20'))

# =============================================================================
# Development and Debug Configuration
# =============================================================================

# Enable debug mode (more verbose logging, etc.)
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

# Test guild ID for slash command testing (None for global commands)
TEST_GUILD_ID: Optional[int] = None
if os.getenv('TEST_GUILD_ID'):
    TEST_GUILD_ID = int(os.getenv('TEST_GUILD_ID'))

# Whether to sync slash commands on startup
SYNC_COMMANDS_ON_STARTUP = os.getenv('SYNC_COMMANDS_ON_STARTUP', 'false').lower() == 'true'

# =============================================================================
# Backup and Export Configuration
# =============================================================================

# Directory for character sheet backups
BACKUP_DIRECTORY = os.getenv('BACKUP_DIRECTORY', './backups')

# Whether to create automatic backups
AUTO_BACKUP_ENABLED = os.getenv('AUTO_BACKUP_ENABLED', 'true').lower() == 'true'

# Backup frequency (in hours)
BACKUP_FREQUENCY_HOURS = int(os.getenv('BACKUP_FREQUENCY_HOURS', '24'))

# Maximum number of backup files to keep
MAX_BACKUP_FILES = int(os.getenv('MAX_BACKUP_FILES', '7'))

# =============================================================================
# External API Configuration (for future features)
# =============================================================================

# SWRPGNetwork API (if you want to integrate with external character tools)
SWRPG_API_KEY = os.getenv('SWRPG_API_KEY', '')
SWRPG_API_URL = os.getenv('SWRPG_API_URL', 'https://api.swrpgnetwork.com')

# =============================================================================
# Validation and Setup
# =============================================================================

def validate_config():
    """Validate configuration settings and provide helpful error messages"""
    errors = []
    warnings = []
    
    # Check required settings
    if BOT_TOKEN == 'your_bot_token_here' or not BOT_TOKEN:
        errors.append("DISCORD_BOT_TOKEN is not set. Get your token from https://discord.com/developers/applications")
    
    # Check database URL
    if not DATABASE_URL:
        errors.append("DATABASE_URL is not set")
    
    # Check file size limits
    if MAX_FILE_SIZE > 8 * 1024 * 1024:  # 8MB Discord limit
        warnings.append(f"MAX_FILE_SIZE ({MAX_FILE_SIZE}) exceeds Discord's 8MB limit")
    
    # Check dice limits
    if MAX_DICE_PER_ROLL > 50:
        warnings.append(f"MAX_DICE_PER_ROLL ({MAX_DICE_PER_ROLL}) is very high and may cause performance issues")
    
    # Check role configuration
    if not GM_ROLE_NAMES:
        warnings.append("No GM role names configured - GM features will not work")
    
    return errors, warnings

def get_database_config():
    """Get database configuration for SQLAlchemy"""
    config = {
        'url': DATABASE_URL,
        'echo': DEBUG_MODE,  # Log SQL queries in debug mode
    }
    
    # Add connection pool settings for non-SQLite databases
    if not DATABASE_URL.startswith('sqlite'):
        config.update({
            'pool_size': DB_POOL_SIZE,
            'max_overflow': DB_MAX_OVERFLOW,
            'pool_timeout': DB_POOL_TIMEOUT,
            'pool_pre_ping': True,  # Verify connections before use
        })
    
    return config

def get_logging_config():
    """Get logging configuration"""
    import logging
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
    
    config = {
        'level': numeric_level,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': []
    }
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    config['handlers'].append(console_handler)
    
    # File handler (if enabled)
    if LOG_FILE:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(numeric_level)
        config['handlers'].append(file_handler)
    
    return config

# =============================================================================
# Environment File Template
# =============================================================================

ENV_TEMPLATE = """
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
BOT_PREFIX=!

# Database Configuration
DATABASE_URL=sqlite:///starwars_bot.db

# Bot Behavior
MAX_SHEETS_PER_USER=10
MAX_FILE_SIZE=1048576
USE_WILD_DIE=true

# Permissions
GM_CAN_VIEW_ALL_SHEETS=true
GM_CAN_DELETE_ANY_SHEET=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=starwars_bot.log
LOG_DICE_ROLLS=true

# Features
ENABLE_CAMPAIGNS=false
ENABLE_ROLL_HISTORY=true

# Debug
DEBUG_MODE=false
"""

def create_env_file():
    """Create a .env template file"""
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(ENV_TEMPLATE.strip())
        print("Created .env template file. Please edit it with your configuration.")
    else:
        print(".env file already exists.")

# =============================================================================
# Runtime Configuration Check
# =============================================================================

if __name__ == "__main__":
    print("=== Star Wars Bot Configuration ===")
    print(f"Bot Token: {'Set' if BOT_TOKEN != 'your_bot_token_here' else 'NOT SET'}")
    print(f"Database URL: {DATABASE_URL}")
    print(f"Command Prefix: {COMMAND_PREFIX}")
    print(f"Debug Mode: {DEBUG_MODE}")
    print(f"Use Wild Die: {USE_WILD_DIE}")
    print(f"GM Roles: {', '.join(GM_ROLE_NAMES)}")
    
    # Validate configuration
    errors, warnings = validate_config()
    
    if errors:
        print("\n❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("\n⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("\n✅ Configuration looks good!")
    
    # Offer to create .env file
    if not os.path.exists('.env'):
        response = input("\nCreate .env template file? (y/n): ")
        if response.lower() == 'y':
            create_env_file()