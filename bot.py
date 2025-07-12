import discord
from discord.ext import commands
import json
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, CharacterSheet, SharedSheet
from parser import WEGStarWarsParser
from dice import WEGDiceRoller
from config import BOT_TOKEN, DATABASE_URL

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Database setup
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Initialize parser and dice roller
parser = WEGStarWarsParser()
dice_roller = WEGDiceRoller()

def get_or_create_user(session, discord_id, username):
    """Get or create a user in the database"""
    user = session.query(User).filter_by(discord_id=str(discord_id)).first()
    if not user:
        user = User(discord_id=str(discord_id), username=username)
        session.add(user)
        session.commit()
    return user

def is_gm(user):
    """Check if user has GM/DM role"""
    gm_roles = ['GM', 'DM', 'Game Master', 'Dungeon Master']
    return any(role.name in gm_roles for role in user.roles)

def can_view_sheet(session, requesting_user_id, sheet_id):
    """Check if user can view a character sheet"""
    sheet = session.query(CharacterSheet).filter_by(id=sheet_id).first()
    if not sheet:
        return False, None
    
    # Owner can always view
    if sheet.user.discord_id == str(requesting_user_id):
        return True, sheet
    
    # Check if shared with user
    shared = session.query(SharedSheet).filter_by(
        sheet_id=sheet_id, 
        shared_with_discord_id=str(requesting_user_id)
    ).first()
    if shared:
        return True, sheet
    
    return False, sheet

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')

@bot.command(name='addsheet', help='Upload a character sheet (JSON, CSV, or text)')
async def add_sheet(ctx, *, sheet_data=None):
    """Add a character sheet for the user"""
    session = Session()
    try:
        user = get_or_create_user(session, ctx.author.id, ctx.author.name)
        
        # Check if user attached a file
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if attachment.filename.endswith(('.json', '.csv', '.txt')):
                content = await attachment.read()
                sheet_data = content.decode('utf-8')
            else:
                await ctx.send("Please upload a .json, .csv, or .txt file.")
                return
        
        if not sheet_data:
            await ctx.send("Please provide character sheet data or attach a file.")
            return
        
        # Parse the character sheet
        try:
            if sheet_data.strip().startswith('{'):
                # JSON data
                character = parser._parse_generic_json(json.loads(sheet_data))
            else:
                # Plain text
                character = parser.parse_text_sheet(sheet_data)
        except Exception as e:
            await ctx.send(f"Error parsing character sheet: {str(e)}")
            return
        
        # Check if character with this name already exists for user
        existing = session.query(CharacterSheet).filter_by(
            user_id=user.id, 
            character_name=character.name
        ).first()
        
        if existing:
            await ctx.send(f"You already have a character named '{character.name}'. Use `!updatesheet` to modify it.")
            return
        
        # Save to database
        sheet = CharacterSheet(
            user_id=user.id,
            character_name=character.name,
            template=character.template,
            data=character.__dict__
        )
        session.add(sheet)
        session.commit()
        
        await ctx.send(f"✅ Character sheet for '{character.name}' ({character.template}) has been saved!")
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
    finally:
        session.close()

@bot.command(name='listsheets', help='List your character sheets')
async def list_sheets(ctx):
    """List all character sheets for the user"""
    session = Session()
    try:
        user = get_or_create_user(session, ctx.author.id, ctx.author.name)
        sheets = session.query(CharacterSheet).filter_by(user_id=user.id).all()
        
        if not sheets:
            await ctx.send("You don't have any character sheets yet. Use `!addsheet` to add one.")
            return
        
        embed = discord.Embed(title="Your Character Sheets", color=0x00ff00)
        for sheet in sheets:
            embed.add_field(
                name=f"{sheet.character_name} (ID: {sheet.id})",
                value=f"Template: {sheet.template}",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
    finally:
        session.close()

@bot.command(name='viewsheet', help='View a character sheet by ID')
async def view_sheet(ctx, sheet_id: int):
    """View a character sheet"""
    session = Session()
    try:
        # Check permissions
        can_view, sheet = can_view_sheet(session, ctx.author.id, sheet_id)
        
        # GMs can view any sheet
        if not can_view and is_gm(ctx.author):
            sheet = session.query(CharacterSheet).filter_by(id=sheet_id).first()
            can_view = True
        
        if not can_view or not sheet:
            await ctx.send("You don't have permission to view this character sheet, or it doesn't exist.")
            return
        
        data = sheet.data
        
        # Create embed with character info
        embed = discord.Embed(
            title=f"{data['name']} ({data['template']})",
            color=0x0099ff
        )
        
        # Add attributes
        attr_text = ""
        for attr, value in data['attributes'].items():
            attr_text += f"**{attr.capitalize()}:** {value}\n"
        embed.add_field(name="Attributes", value=attr_text, inline=True)
        
        # Add skills (limit to prevent embed overflow)
        skills_text = ""
        skill_count = 0
        for skill, value in data['skills'].items():
            if skill_count >= 10:  # Limit skills shown
                skills_text += f"... and {len(data['skills']) - 10} more"
                break
            skills_text += f"**{skill.replace('_', ' ').title()}:** {value}\n"
            skill_count += 1
        
        if skills_text:
            embed.add_field(name="Skills", value=skills_text, inline=True)
        
        # Add Force info
        force_text = f"**Force Points:** {data.get('force_points', 1)}\n"
        force_text += f"**Character Points:** {data.get('character_points', 5)}\n"
        force_text += f"**Dark Side Points:** {data.get('dark_side_points', 0)}\n"
        force_text += f"**Force Sensitive:** {'Yes' if data.get('force_sensitive', False) else 'No'}"
        embed.add_field(name="Force & Character Points", value=force_text, inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
    finally:
        session.close()

@bot.command(name='sharesheet', help='Share a character sheet with another user')
async def share_sheet(ctx, sheet_id: int, user: discord.Member):
    """Share a character sheet with another user"""
    session = Session()
    try:
        # Check if user owns the sheet
        sheet = session.query(CharacterSheet).filter_by(id=sheet_id).first()
        if not sheet or sheet.user.discord_id != str(ctx.author.id):
            await ctx.send("You can only share your own character sheets.")
            return
        
        # Get or create the target user
        target_user = get_or_create_user(session, user.id, user.name)
        
        # Check if already shared
        existing_share = session.query(SharedSheet).filter_by(
            sheet_id=sheet_id,
            shared_with_discord_id=str(user.id)
        ).first()
        
        if existing_share:
            await ctx.send(f"Character sheet is already shared with {user.mention}.")
            return
        
        # Create share record
        share = SharedSheet(
            sheet_id=sheet_id,
            shared_with_discord_id=str(user.id)
        )
        session.add(share)
        session.commit()
        
        await ctx.send(f"✅ Character sheet '{sheet.character_name}' has been shared with {user.mention}!")
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
    finally:
        session.close()

@bot.command(name='roll', help='Roll dice for a skill or attribute')
async def roll_dice(ctx, sheet_id: int, skill_or_attribute: str):
    """Roll dice for a character's skill or attribute"""
    session = Session()
    try:
        # Check permissions
        can_view, sheet = can_view_sheet(session, ctx.author.id, sheet_id)
        
        # GMs can roll for any sheet
        if not can_view and is_gm(ctx.author):
            sheet = session.query(CharacterSheet).filter_by(id=sheet_id).first()
            can_view = True
        
        if not can_view or not sheet:
            await ctx.send("You don't have permission to use this character sheet, or it doesn't exist.")
            return
        
        data = sheet.data
        skill_name = skill_or_attribute.lower().replace(' ', '_')
        
        # Check if it's a skill first
        dice_code = None
        roll_type = None
        
        if skill_name in data['skills']:
            dice_code = data['skills'][skill_name]
            roll_type = f"{skill_name.replace('_', ' ').title()} skill"
        elif skill_name in data['attributes']:
            dice_code = data['attributes'][skill_name]
            roll_type = f"{skill_name.capitalize()} attribute"
        else:
            # Check if it's an untrained skill
            governing_attr = parser.get_skill_attribute(skill_name)
            if governing_attr in data['attributes']:
                dice_code = parser.calculate_untrained_skill_from_data(data, skill_name)
                roll_type = f"{skill_name.replace('_', ' ').title()} (untrained)"
            else:
                await ctx.send(f"Skill or attribute '{skill_or_attribute}' not found for {data['name']}.")
                return
        
        # Roll the dice
        result = dice_roller.roll(dice_code)
        
        embed = discord.Embed(
            title=f"🎲 Dice Roll for {data['name']}",
            color=0xff6600
        )
        embed.add_field(name="Roll Type", value=roll_type, inline=True)
        embed.add_field(name="Dice Code", value=dice_code, inline=True)
        embed.add_field(name="Result", value=f"**{result['total']}**", inline=True)
        embed.add_field(name="Breakdown", value=result['breakdown'], inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
    finally:
        session.close()

@bot.command(name='deletesheet', help='Delete one of your character sheets')
async def delete_sheet(ctx, sheet_id: int):
    """Delete a character sheet"""
    session = Session()
    try:
        sheet = session.query(CharacterSheet).filter_by(id=sheet_id).first()
        if not sheet or sheet.user.discord_id != str(ctx.author.id):
            await ctx.send("You can only delete your own character sheets.")
            return
        
        character_name = sheet.character_name
        
        # Delete associated shares
        session.query(SharedSheet).filter_by(sheet_id=sheet_id).delete()
        
        # Delete the sheet
        session.delete(sheet)
        session.commit()
        
        await ctx.send(f"✅ Character sheet '{character_name}' has been deleted.")
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
    finally:
        session.close()

@bot.command(name='help_starwars', help='Show Star Wars bot help')
async def help_starwars(ctx):
    """Show help for Star Wars bot commands"""
    embed = discord.Embed(
        title="🌟 Star Wars RPG Bot Commands",
        description="West End Games Star Wars TTRPG Discord Bot",
        color=0xffff00
    )
    
    commands_text = """
    `!addsheet` - Upload a character sheet (attach file or paste data)
    `!listsheets` - List your character sheets
    `!viewsheet <id>` - View a character sheet by ID
    `!sharesheet <id> @user` - Share a sheet with another user
    `!roll <id> <skill/attribute>` - Roll dice for a skill or attribute
    `!deletesheet <id>` - Delete one of your character sheets
    """
    
    embed.add_field(name="Commands", value=commands_text, inline=False)
    
    embed.add_field(
        name="Dice Codes",
        value="Uses WEG Star Wars dice codes like `3D+2` (roll 3d6 and add 2)",
        inline=False
    )
    
    embed.add_field(
        name="Privacy",
        value="Only you (and GMs) can view your sheets unless you share them",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument. Use `!help {ctx.command}` for usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Invalid argument. Use `!help {ctx.command}` for usage.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")
        print(f"Error in command {ctx.command}: {error}")

if __name__ == '__main__':
    bot.run(BOT_TOKEN)