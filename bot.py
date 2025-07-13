import discord
from discord.ext import commands
import json
import re
import shlex
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

def get_sheet_by_name(session, ctx, character_name):
    """Get a character sheet by name for the user or GM."""
    # Try to get the user's own sheet first
    user = get_or_create_user(session, ctx.author.id, ctx.author.name)
    sheet = session.query(CharacterSheet).filter_by(user_id=user.id, character_name=character_name).first()
    if sheet:
        return sheet
    # If not found, allow GM to access any sheet by name
    if is_gm(ctx.author):
        sheet = session.query(CharacterSheet).filter_by(character_name=character_name).first()
        return sheet
    return None

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
                character = parser.parse_json_content(sheet_data)
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

@bot.command(name='viewsheet', help='View a character sheet by name')
async def view_sheet(ctx, *, character_name: str):
    """View a character sheet"""
    session = Session()
    try:
        sheet = get_sheet_by_name(session, ctx, character_name)
        if not sheet:
            await ctx.send(f"Character sheet '{character_name}' not found or you do not have permission to view it.")
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
async def share_sheet(ctx, character_name: str, user: discord.Member):
    """Share a character sheet with another user"""
    session = Session()
    try:
        sheet = get_sheet_by_name(session, ctx, character_name)
        if not sheet:
            await ctx.send(f"Character sheet '{character_name}' not found or you do not have permission to share it.")
            return

        # Get or create the target user
        target_user = get_or_create_user(session, user.id, user.name)

        # Check if already shared
        existing_share = session.query(SharedSheet).filter_by(
            sheet_id=sheet.id,
            shared_with_discord_id=str(user.id)
        ).first()

        if existing_share:
            await ctx.send(f"Character sheet is already shared with {user.mention}.")
            return

        # Create share record
        share = SharedSheet(
            sheet_id=sheet.id,
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
async def roll_dice(ctx, *, args):
    """Roll dice for a character's skill or attribute"""
    session = Session()
    try:
        # Use shlex to split arguments, supporting quoted names and multi-word skills
        try:
            parts = shlex.split(args)
            if len(parts) < 2:
                raise ValueError
            character_name = parts[0]
            skill = ' '.join(parts[1:])
        except ValueError:
            await ctx.send("Invalid argument. Use !help roll for usage.")
            return

        user = session.query(User).filter_by(discord_id=str(ctx.author.id)).first()
        if not user:
            await ctx.send("User not found in database.")
            return

        sheet = session.query(CharacterSheet).filter_by(user_id=user.id, character_name=character_name).first()
        if not sheet:
            await ctx.send(f"Character '{character_name}' not found.")
            return
        
        data = sheet.data
        skill_key = find_skill_key(data['skills'], skill)
        if skill_key:
            dice_code = data['skills'][skill_key]
            roll_type = f"{skill_key.replace('_', ' ').title()} skill"
        elif skill.lower().replace(' ', '_') in data['attributes']:
            dice_code = data['attributes'][skill.lower().replace(' ', '_')]
            roll_type = f"{skill.title()} attribute"
        else:
            # Check if it's an untrained skill
            attributes = {k.lower(): v for k, v in data['attributes'].items()}
            governing_attr = parser.get_skill_attribute(skill)
            if governing_attr and governing_attr.lower() in attributes:
                dice_code = parser.calculate_untrained_skill_from_data(data, skill)
                roll_type = f"{skill.title()} (untrained)"
            else:
                await ctx.send(f"Skill or attribute '{skill}' not found for {data['name']}.")
                return
        
        # Roll the dice
        result = dice_roller.roll(dice_code)

        # Assume result['wild_die'] contains the wild die value (add this to your dice roller if needed)
        wild_die = result.get('wild_die_result')
        total = result['total']

        # Default color and result formatting
        embed_color = 0x0099ff  # fallback blue
        result_str = f"**{total}**"  # Bold, default color

        if wild_die == 1:
            embed_color = 0xff0000  # Red
        elif 1 <= total <= 5:
            embed_color = 0xff69b4  # Pink
        elif 6 <= total <= 10:
            embed_color = 0x3399ff  # Blue
        elif 11 <= total <= 15:
            embed_color = 0x33cc33  # Green
        elif 16 <= total <= 20:
            embed_color = 0xffff00  # Yellow
        elif 21 <= total <= 30:
            embed_color = 0xffffff  # White
        elif total > 30:
            embed_color = 0x800080  # Purple

        # If wild die is 6, make the result numbers green text (using Discord markdown)
        if wild_die and wild_die > 5:
            result_str = f"```diff\n+{total}\n```"  # Green text in Discord
        else:
            result_str = f"**{total}**"  # Bold, default color

        embed = discord.Embed(
            title=f"🎲 Dice Roll for {data['name']}",
            color=embed_color
        )
        embed.add_field(name="Roll Type", value=roll_type, inline=True)
        embed.add_field(name="Dice Code", value=dice_code, inline=True)
        embed.add_field(name="Result", value=result_str, inline=True)
        embed.add_field(name="Breakdown", value=result['breakdown'], inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
    finally:
        session.close()

@bot.command(name='deletesheet', help='Delete one of your character sheets')
async def delete_sheet(ctx, *, character_name: str):
    """Delete a character sheet"""
    session = Session()
    try:
        sheet = get_sheet_by_name(session, ctx, character_name)
        if not sheet:
            await ctx.send(f"Character sheet '{character_name}' not found or you do not have permission to delete it.")
            return

        # Delete associated shares
        session.query(SharedSheet).filter_by(sheet_id=sheet.id).delete()
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
    `!listskills` - List all available skills by attribute
    `!rolldice <dice code>` - Roll any WEG dice code (e.g., 4D+1)
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

@bot.command(name='listskills', help='List all available skills organized by attribute')
async def list_skills(ctx):
    """List all skills organized by governing attribute"""
    try:
        embed = discord.Embed(
            title="🌟 WEG Star Wars Skills by Attribute",
            description="All available skills organized by their governing attributes",
            color=0x0099ff
        )
        
        # Get skill categories from parser
        for attribute, skills in parser.skill_categories.items():
            # Format skill names (replace underscores with spaces, title case)
            formatted_skills = [skill.replace('_', ' ').title() for skill in skills]
            
            # Split into chunks if too many skills (Discord embed field limit is 1024 chars)
            skill_text = ", ".join(formatted_skills)
            
            if len(skill_text) > 1024:
                # Split into multiple fields if too long
                chunks = []
                current_chunk = []
                current_length = 0
                
                for skill in formatted_skills:
                    skill_with_comma = skill + ", "
                    if current_length + len(skill_with_comma) > 1020:  # Leave some buffer
                        chunks.append(", ".join(current_chunk))
                        current_chunk = [skill]
                        current_length = len(skill_with_comma)
                    else:
                        current_chunk.append(skill)
                        current_length += len(skill_with_comma)
                
                if current_chunk:
                    chunks.append(", ".join(current_chunk))
                
                # Add multiple fields for this attribute
                for i, chunk in enumerate(chunks):
                    field_name = f"{attribute.capitalize()}" if i == 0 else f"{attribute.capitalize()} (cont.)"
                    embed.add_field(name=field_name, value=chunk, inline=False)
            else:
                # Single field for this attribute
                embed.add_field(
                    name=f"{attribute.capitalize()}",
                    value=skill_text,
                    inline=False
                )
        
        # Add footer with usage info
        embed.set_footer(text="Use these skill names with !roll <sheet_id> <skill_name>")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command(name='updatesheet', help='Update an existing character sheet by name')
async def updatesheet(ctx, *, character_name: str):
    """Update a character sheet by uploading a new file or pasting new data"""
    session = Session()
    try:
        sheet = get_sheet_by_name(session, ctx, character_name)
        if not sheet:
            await ctx.send(f"Sheet '{character_name}' not found or you do not have permission to update it.")
            return

        await ctx.send("Please upload the new character sheet file or paste the new data as your next message.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        msg = await bot.wait_for('message', check=check, timeout=120)
        if msg.attachments:
            attachment = msg.attachments[0]
            content = await attachment.read()
            sheet_data = content.decode('utf-8')
            filename = attachment.filename
        else:
            sheet_data = msg.content
            filename = "input.txt"

        # Parse the new sheet data
        if sheet_data.strip().startswith('{'):
            character = parser.parse_json_content(sheet_data)
        else:
            character = parser.parse_text_sheet(sheet_data)

        # Update the sheet in the database
        sheet.character_name = character.name
        sheet.template = character.template
        sheet.data = character.__dict__
        session.commit()
        await ctx.send(f"Character sheet '{sheet.character_name}' updated successfully!")
    except Exception as e:
        await ctx.send(f"Error updating character sheet: {str(e)}")
    finally:
        session.close()

@bot.command(name='rolldice', help='Roll any WEG dice code (e.g., !rolldice 4D+1)')
async def roll_dice_code(ctx, dice_code: str):
    """Roll any WEG dice code without a character sheet"""
    try:
        result = dice_roller.roll(dice_code)
        wild_die = result.get('wild_die_result')
        total = result['total']

        # Color and result formatting logic (exclusive if-elif chain)
        embed_color = 0x0099ff  # fallback blue
        result_str = f"**{total}**"  # Bold, default color

        if wild_die == 1:
            embed_color = 0xff0000  # Red
        elif 1 <= total <= 5:
            embed_color = 0xff69b4  # Pink
        elif 6 <= total <= 10:
            embed_color = 0x3399ff  # Blue
        elif 11 <= total <= 15:
            embed_color = 0x33cc33  # Green
        elif 16 <= total <= 20:
            embed_color = 0xffff00  # Yellow
        elif 21 <= total <= 30:
            embed_color = 0xffffff  # White
        elif total > 30:
            embed_color = 0x800080  # Purple

        # If wild die is 6+, make the result numbers green text (using Discord markdown)
        if wild_die and wild_die > 5:
            result_str = f"```diff\n+{total}\n```"

        embed = discord.Embed(
            title=f"🎲 Dice Roll: {dice_code}",
            color=embed_color
        )
        embed.add_field(name="Result", value=result_str, inline=True)
        embed.add_field(name="Breakdown", value=result['breakdown'], inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error rolling dice: {str(e)}")

def find_skill_key(skills_dict, skill):
    """Find the correct skill key in the dict, regardless of underscores, spaces, or case."""
    skill_variants = [
        skill,
        skill.lower(),
        skill.lower().replace(' ', '_'),
        skill.lower().replace('_', ' '),
        skill.replace(' ', '_'),
        skill.replace('_', ' ')
    ]
    for key in skills_dict:
        for variant in skill_variants:
            if key.lower() == variant.lower():
                return key
    return None

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