# Smart-SW-Roller

**Smart-SW-Roller** is a Discord bot designed to facilitate playing the **West End Games (WEG) Star Wars Tabletop RPG** (the classic d6 system). It allows users to upload character sheets, manage them in a database, and roll dice directly against their character's skills and attributes, handling the specific rules of the system (like the "Wild Die").

## 🌟 Features

*   **🎲 WEG d6 Dice Rolling**:
    *   Full support for the classic d6 system.
    *   **Wild Die Mechanic**: Automatically handles exploding 6s and complications on 1s.
    *   **Opposed Rolls**: Support for contested actions.
    *   **Custom Dice Codes**: Roll standard codes (e.g., `!roll 3D+2`) or custom combinations.
*   **📝 Character Sheet Management**:
    *   **Easy Upload**: Upload character sheets via `!addsheet` using **JSON**, **CSV**, or **Plain Text** files.
    *   **Smart Parsing**: Automatically detects file formats and normalizes skill names (e.g., "Lightsabre" -> "lightsaber").
    *   **Database Storage**: Securely stores characters in a SQLite database.
    *   **Privacy**: Users can only see their own sheets unless explicitly shared.
*   **🤝 Sharing & Permissions**:
    *   Share sheets with other players using `!sharesheet`.
    *   GMs have administrative access to view all sheets.

## 🚀 Installation

### Prerequisites

*   Python 3.8+
*   A Discord Bot Token (from the [Discord Developer Portal](https://discord.com/developers/applications))

### Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Big-Bald-Mike/Smart-SW-Roller.git
    cd Smart-SW-Roller
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the bot**:
    *   Create a `.env` file in the root directory (or rename a template if provided).
    *   Add your Discord Bot Token and other settings (see [Configuration](#configuration) below).

4.  **Run the bot**:
    ```bash
    python bot.py
    ```

## ⚙️ Configuration

Create a `.env` file in the root directory with the following settings:

```env
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
BOT_PREFIX=!

# Database Configuration
# Default is SQLite, but you can use PostgreSQL/MySQL
DATABASE_URL=sqlite:///starwars_bot.db

# Bot Behavior
MAX_SHEETS_PER_USER=10
MAX_FILE_SIZE=1048576  # 1MB
USE_WILD_DIE=true      # Set to false to disable Wild Die mechanics

# Permissions
GM_ROLE_NAMES=GM,DM,Game Master,Dungeon Master
GM_CAN_VIEW_ALL_SHEETS=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=starwars_bot.log
```

## 🎮 Usage

### Character Management

*   `!addsheet` - Upload a character sheet. Attach a `.json`, `.csv`, or `.txt` file, or paste the data directly.
*   `!listsheets` - List all your character sheets.
*   `!viewsheet <name>` - View a character sheet by name.
*   `!updatesheet <name>` - Update an existing character sheet.
*   `!deletesheet <name>` - Delete a character sheet.
*   `!sharesheet <name> @user` - Share a character sheet with another user.

### Dice Rolling

*   `!roll <character_name> <skill/attribute>` - Roll a skill or attribute for a specific character.
    *   Example: `!roll Han Blaster` (Rolls Han Solo's Blaster skill)
    *   Example: `!roll Luke Dex` (Rolls Luke's Dexterity attribute)
*   `!rolldice <dice_code>` - Roll a generic dice code without a character sheet.
    *   Example: `!rolldice 3D+2`
*   `!listskills` - List all available skills organized by attribute.

## 📂 File Structure

*   `bot.py`: Main entry point. Handles Discord commands and events.
*   `dice.py`: Core dice rolling logic (WEG d6 system implementation).
*   `models.py`: Database schema definitions (User, CharacterSheet, SharedSheet).
*   `parser.py`: Logic for parsing character sheets from various file formats.
*   `config.py`: Configuration management using environment variables.

## 📄 License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.
