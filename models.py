from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """Discord user model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(20), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    character_sheets = relationship("CharacterSheet", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(discord_id='{self.discord_id}', username='{self.username}')>"

class CharacterSheet(Base):
    """Character sheet model for WEG Star Wars characters"""
    __tablename__ = 'character_sheets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    character_name = Column(String(100), nullable=False)
    template = Column(String(50), nullable=True)  # Smuggler, Jedi, etc.
    
    # Store the complete character data as JSON
    data = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="character_sheets")
    shared_with = relationship("SharedSheet", back_populates="sheet", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CharacterSheet(id={self.id}, name='{self.character_name}', template='{self.template}')>"
    
    @property
    def attributes(self):
        """Get character attributes from JSON data"""
        return self.data.get('attributes', {})
    
    @property
    def skills(self):
        """Get character skills from JSON data"""
        return self.data.get('skills', {})
    
    @property
    def force_points(self):
        """Get character's force points"""
        return self.data.get('force_points', 1)
    
    @property
    def character_points(self):
        """Get character's character points"""
        return self.data.get('character_points', 5)
    
    @property
    def dark_side_points(self):
        """Get character's dark side points"""
        return self.data.get('dark_side_points', 0)
    
    @property
    def force_sensitive(self):
        """Check if character is force sensitive"""
        return self.data.get('force_sensitive', False)
    
    @property
    def equipment(self):
        """Get character's equipment list"""
        return self.data.get('equipment', [])
    
    @property
    def credits(self):
        """Get character's credits"""
        return self.data.get('credits', 1000)

class SharedSheet(Base):
    """Model for tracking character sheet sharing permissions"""
    __tablename__ = 'shared_sheets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sheet_id = Column(Integer, ForeignKey('character_sheets.id'), nullable=False)
    shared_with_discord_id = Column(String(20), nullable=False)
    
    # Optional: Add sharing permissions
    can_view = Column(Boolean, default=True)
    can_roll = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)  # Future feature
    
    # Metadata
    shared_at = Column(DateTime, default=datetime.utcnow)
    shared_by_discord_id = Column(String(20), nullable=True)  # Who shared it
    
    # Relationships
    sheet = relationship("CharacterSheet", back_populates="shared_with")
    
    def __repr__(self):
        return f"<SharedSheet(sheet_id={self.sheet_id}, shared_with='{self.shared_with_discord_id}')>"

class GameSession(Base):
    """Optional: Model for tracking game sessions and rolls"""
    __tablename__ = 'game_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(String(20), nullable=False)  # Discord server ID
    channel_id = Column(String(20), nullable=False)  # Discord channel ID
    session_name = Column(String(100), nullable=True)
    gm_discord_id = Column(String(20), nullable=False)
    
    # Session state
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Relationships
    rolls = relationship("DiceRoll", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<GameSession(id={self.id}, name='{self.session_name}', guild_id='{self.guild_id}')>"

class DiceRoll(Base):
    """Model for logging dice rolls (optional feature for game history)"""
    __tablename__ = 'dice_rolls'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('game_sessions.id'), nullable=True)
    character_sheet_id = Column(Integer, ForeignKey('character_sheets.id'), nullable=True)
    
    # Roll details
    discord_user_id = Column(String(20), nullable=False)
    guild_id = Column(String(20), nullable=False)
    channel_id = Column(String(20), nullable=False)
    
    # What was rolled
    skill_or_attribute = Column(String(50), nullable=False)
    dice_code = Column(String(20), nullable=False)  # e.g., "4D+2"
    
    # Results
    total_result = Column(Integer, nullable=False)
    individual_dice = Column(JSON, nullable=True)  # Store individual die results
    breakdown = Column(Text, nullable=True)  # Human-readable breakdown
    
    # Metadata
    rolled_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("GameSession", back_populates="rolls")
    character_sheet = relationship("CharacterSheet")
    
    def __repr__(self):
        return f"<DiceRoll(id={self.id}, dice_code='{self.dice_code}', result={self.total_result})>"

class Campaign(Base):
    """Optional: Model for organizing characters into campaigns"""
    __tablename__ = 'campaigns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    guild_id = Column(String(20), nullable=False)  # Discord server ID
    gm_discord_id = Column(String(20), nullable=False)
    
    # Campaign settings
    is_active = Column(Boolean, default=True)
    allow_public_sheets = Column(Boolean, default=False)  # Allow players to see each other's sheets
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    participants = relationship("CampaignParticipant", back_populates="campaign", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', guild_id='{self.guild_id}')>"

class CampaignParticipant(Base):
    """Junction table for campaign participants and their characters"""
    __tablename__ = 'campaign_participants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False)
    character_sheet_id = Column(Integer, ForeignKey('character_sheets.id'), nullable=False)
    discord_user_id = Column(String(20), nullable=False)
    
    # Participant role
    role = Column(String(20), default='player')  # 'player', 'gm', 'observer'
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="participants")
    character_sheet = relationship("CharacterSheet")
    
    def __repr__(self):
        return f"<CampaignParticipant(campaign_id={self.campaign_id}, character_id={self.character_sheet_id})>"

# Database utility functions
def create_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)

def drop_tables(engine):
    """Drop all tables from the database (use with caution!)"""
    Base.metadata.drop_all(engine)

# Example usage and helper functions
class DatabaseManager:
    """Helper class for common database operations"""
    
    def __init__(self, session):
        self.session = session
    
    def get_user_by_discord_id(self, discord_id):
        """Get user by Discord ID"""
        return self.session.query(User).filter_by(discord_id=str(discord_id)).first()
    
    def get_or_create_user(self, discord_id, username):
        """Get existing user or create new one"""
        user = self.get_user_by_discord_id(discord_id)
        if not user:
            user = User(discord_id=str(discord_id), username=username)
            self.session.add(user)
            self.session.commit()
        return user
    
    def get_user_sheets(self, discord_id):
        """Get all character sheets for a user"""
        user = self.get_user_by_discord_id(discord_id)
        if user:
            return user.character_sheets
        return []
    
    def get_sheet_by_id(self, sheet_id):
        """Get character sheet by ID"""
        return self.session.query(CharacterSheet).filter_by(id=sheet_id, is_active=True).first()
    
    def can_user_access_sheet(self, discord_id, sheet_id):
        """Check if user can access a character sheet"""
        sheet = self.get_sheet_by_id(sheet_id)
        if not sheet:
            return False, None
        
        # Owner can always access
        if sheet.user.discord_id == str(discord_id):
            return True, sheet
        
        # Check if shared
        shared = self.session.query(SharedSheet).filter_by(
            sheet_id=sheet_id,
            shared_with_discord_id=str(discord_id)
        ).first()
        
        return bool(shared), sheet
    
    def share_sheet(self, sheet_id, owner_discord_id, target_discord_id):
        """Share a character sheet with another user"""
        sheet = self.get_sheet_by_id(sheet_id)
        if not sheet or sheet.user.discord_id != str(owner_discord_id):
            return False, "You can only share your own character sheets."
        
        # Check if already shared
        existing = self.session.query(SharedSheet).filter_by(
            sheet_id=sheet_id,
            shared_with_discord_id=str(target_discord_id)
        ).first()
        
        if existing:
            return False, "Sheet is already shared with this user."
        
        # Create share record
        share = SharedSheet(
            sheet_id=sheet_id,
            shared_with_discord_id=str(target_discord_id),
            shared_by_discord_id=str(owner_discord_id)
        )
        self.session.add(share)
        self.session.commit()
        
        return True, "Sheet shared successfully."
    
    def log_dice_roll(self, discord_user_id, guild_id, channel_id, character_sheet_id, 
                     skill_or_attribute, dice_code, total_result, individual_dice, breakdown):
        """Log a dice roll to the database"""
        roll = DiceRoll(
            character_sheet_id=character_sheet_id,
            discord_user_id=str(discord_user_id),
            guild_id=str(guild_id),
            channel_id=str(channel_id),
            skill_or_attribute=skill_or_attribute,
            dice_code=dice_code,
            total_result=total_result,
            individual_dice=individual_dice,
            breakdown=breakdown
        )
        self.session.add(roll)
        self.session.commit()
        return roll
    
    def get_sheet_by_name(self, discord_id, character_name):
        """Get character sheet by name for a specific user"""
        user = self.get_user_by_discord_id(discord_id)
        if user:
            return (
                self.session.query(CharacterSheet)
                .filter_by(user_id=user.id, character_name=character_name, is_active=True)
                .first()
            )
        return None