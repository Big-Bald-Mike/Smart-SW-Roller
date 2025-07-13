import json
import csv
import re
import io
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union

@dataclass
class StarWarsCharacter:
    """Data class representing a WEG Star Wars character"""
    name: str
    template: str  # Smuggler, Jedi, etc.
    attributes: Dict[str, str]  # Dexterity: "3D+1", etc.
    skills: Dict[str, str]      # Blaster: "4D+2", etc.
    force_points: int
    character_points: int
    dark_side_points: int
    force_sensitive: bool
    equipment: List[str]
    credits: int
    
    def to_dict(self):
        """Convert to dictionary for database storage"""
        return {
            'name': self.name,
            'template': self.template,
            'attributes': self.attributes,
            'skills': self.skills,
            'force_points': self.force_points,
            'character_points': self.character_points,
            'dark_side_points': self.dark_side_points,
            'force_sensitive': self.force_sensitive,
            'equipment': self.equipment,
            'credits': self.credits
        }

class WEGStarWarsParser:
    """Parser for West End Games Star Wars character sheets"""
    
    def __init__(self):
        # WEG Star Wars attributes
        self.attributes = [
            'dexterity', 'knowledge', 'mechanical', 
            'perception', 'strength', 'technical'
        ]
        
        # Attribute aliases for parsing
        self.attribute_aliases = {
            'dex': 'dexterity',
            'know': 'knowledge',
            'mech': 'mechanical',
            'perc': 'perception',
            'str': 'strength',
            'tech': 'technical'
        }
        
        # Common skills organized by governing attribute
        self.skill_categories = {
            'dexterity': [
                'blaster', 'brawling_parry', 'dodge', 'firearms',
                'lightsaber', 'melee_combat', 'melee_parry', 'pick_pocket',
                'running', 'thrown_weapons', 'vehicle_blasters', 'archaic_guns',
                'blaster_artillery', 'bowcaster', 'grenade', 'heavy_weapons'
            ],
            'knowledge': [
                'alien_species', 'bureaucracy', 'cultures', 'intimidation',
                'languages', 'planetary_systems', 'scholar', 'streetwise',
                'survival', 'tactics', 'technology', 'willpower', 'business',
                'law_enforcement', 'value', 'jedi_lore', 'sith_lore'
            ],
            'mechanical': [
                'astrogation', 'beast_riding', 'communications', 'computer_programming',
                'piloting', 'repulsorlift_operation', 'sensors', 'space_transports',
                'starfighter_piloting', 'starship_gunnery', 'starship_shields',
                'swoop_operation', 'walker_operation', 'capital_ship_piloting',
                'capital_ship_gunnery', 'capital_ship_shields'
            ],
            'perception': [
                'bargain', 'command', 'con', 'forgery', 'gambling',
                'hide', 'investigation', 'persuasion', 'search', 'sneak',
                'artist', 'entertain', 'sleight_of_hand'
            ],
            'strength': [
                'brawling', 'climbing', 'jumping', 'lifting', 'stamina', 'swimming'
            ],
            'technical': [
                'armor_repair', 'blaster_repair', 'computer_repair',
                'demolitions', 'droid_programming', 'droid_repair',
                'first_aid', 'lightsaber_repair', 'medicine', 'repulsorlift_repair',
                'security', 'space_transports_repair', 'starfighter_repair',
                'capital_ship_repair', 'walker_repair'
            ]
        }
        
        # Force powers (for future expansion)
        self.force_powers = [
            'accelerate_healing', 'absorb_dissipate_energy', 'concentration',
            'control_pain', 'detoxify_poison', 'enhance_attribute', 'hibernation_trance',
            'reduce_injury', 'remain_conscious', 'resist_stun', 'combat_sense',
            'danger_sense', 'life_detection', 'life_sense', 'magnify_senses',
            'receptive_telepathy', 'sense_force', 'telekinesis', 'lightsaber_combat',
            'projective_telepathy', 'affect_mind', 'control_mind', 'transfer_force'
        ]
    
    def parse_file(self, file_content: str, filename: str) -> StarWarsCharacter:
        """Parse character sheet from file content based on file extension"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.json'):
            return self.parse_json_content(file_content)
        elif filename_lower.endswith('.csv'):
            return self.parse_csv_content(file_content)
        elif filename_lower.endswith(('.txt', '.text')):
            return self.parse_text_sheet(file_content)
        else:
            # Try to auto-detect format
            stripped_content = file_content.strip()
            if stripped_content.startswith('{') and stripped_content.endswith('}'):
                return self.parse_json_content(file_content)
            elif ',' in stripped_content and '\n' in stripped_content:
                return self.parse_csv_content(file_content)
            else:
                return self.parse_text_sheet(file_content)
    
    def parse_json_content(self, content: str) -> StarWarsCharacter:
        """Parse JSON character sheet content"""
        try:
            data = json.loads(content)
            return self._parse_json_data(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    
    def parse_csv_content(self, content: str) -> StarWarsCharacter:
        """Parse CSV character sheet content"""
        try:
            # Handle both comma and semicolon separators
            if ';' in content and content.count(';') > content.count(','):
                delimiter = ';'
            else:
                delimiter = ','
            
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            data = next(reader)  # Get first row
            return self._parse_csv_data(data)
        except Exception as e:
            raise ValueError(f"Error parsing CSV: {str(e)}")
    
    def parse_text_sheet(self, text: str) -> StarWarsCharacter:
        """Parse plain text character sheet using regex patterns"""
        return self._parse_text_data(text)
    
    def _parse_json_data(self, data: Dict[str, Any]) -> StarWarsCharacter:
        """Parse character data from JSON dictionary"""
        # Extract basic info
        name = data.get('name', data.get('character_name', 'Unknown'))
        template = data.get('template', data.get('character_template', 'Unknown'))
        
        # Parse attributes
        attributes = {}
        attr_data = data.get('attributes', data.get('stats', {}))
        
        for attr in self.attributes:
            # Try various key formats
            value = (attr_data.get(attr) or 
                    attr_data.get(attr.capitalize()) or 
                    attr_data.get(attr.upper()) or
                    attr_data.get(self.attribute_aliases.get(attr, attr)))
            
            if value:
                attributes[attr] = self._normalize_dice_code(str(value))
            else:
                attributes[attr] = '2D'  # Default
        
        # Parse skills
        skills = {}
        skills_data = data.get('skills', {})
        
        for skill_name, dice_code in skills_data.items():
            normalized_skill = self._normalize_skill_name(skill_name)
            if dice_code:
                skills[normalized_skill] = self._normalize_dice_code(str(dice_code))
        
        # Parse Force and character info
        force_points = int(data.get('force_points', data.get('forcePoints', 1)))
        character_points = int(data.get('character_points', data.get('characterPoints', 5)))
        dark_side_points = int(data.get('dark_side_points', data.get('darkSidePoints', 0)))
        force_sensitive = bool(data.get('force_sensitive', data.get('forceSensitive', False)))
        
        # Parse equipment
        equipment = data.get('equipment', [])
        if isinstance(equipment, str):
            equipment = [item.strip() for item in equipment.split(',') if item.strip()]
        elif not isinstance(equipment, list):
            equipment = []
        
        credits = int(data.get('credits', data.get('money', 1000)))
        
        return StarWarsCharacter(
            name=name,
            template=template,
            attributes=attributes,
            skills=skills,
            force_points=force_points,
            character_points=character_points,
            dark_side_points=dark_side_points,
            force_sensitive=force_sensitive,
            equipment=equipment,
            credits=credits
        )
    
    def _parse_csv_data(self, data: Dict[str, str]) -> StarWarsCharacter:
        """Parse character data from CSV row dictionary"""
        name = data.get('Name', data.get('Character Name', 'Unknown'))
        template = data.get('Template', data.get('Character Template', 'Unknown'))
        
        # Parse attributes
        attributes = {}
        for attr in self.attributes:
            # Try various column name formats
            value = (data.get(attr.capitalize()) or 
                    data.get(attr.upper()) or 
                    data.get(attr) or
                    data.get(f'{attr.capitalize()} Dice'))
            
            if value and value.strip():
                attributes[attr] = self._normalize_dice_code(value.strip())
            else:
                attributes[attr] = '2D'
        
        # Parse skills
        skills = {}
        for key, value in data.items():
            if value and value.strip():
                normalized_key = self._normalize_skill_name(key)
                if self._is_valid_skill(normalized_key):
                    skills[normalized_key] = self._normalize_dice_code(value.strip())
        
        # Parse other fields
        force_points = self._safe_int(data.get('Force Points', data.get('Force_Points', '1')), 1)
        character_points = self._safe_int(data.get('Character Points', data.get('Character_Points', '5')), 5)
        dark_side_points = self._safe_int(data.get('Dark Side Points', data.get('Dark_Side_Points', '0')), 0)
        
        force_sensitive_str = data.get('Force Sensitive', data.get('Force_Sensitive', '')).lower()
        force_sensitive = force_sensitive_str in ['yes', 'true', '1', 'y']
        
        equipment_str = data.get('Equipment', '')
        equipment = [item.strip() for item in equipment_str.split(',') if item.strip()] if equipment_str else []
        
        credits = self._safe_int(data.get('Credits', '1000'), 1000)
        
        return StarWarsCharacter(
            name=name,
            template=template,
            attributes=attributes,
            skills=skills,
            force_points=force_points,
            character_points=character_points,
            dark_side_points=dark_side_points,
            force_sensitive=force_sensitive,
            equipment=equipment,
            credits=credits
        )
    
    def _parse_text_data(self, text: str) -> StarWarsCharacter:
        """Parse character data from plain text"""
        lines = text.split('\n')
        
        # Extract name
        name_match = re.search(r'(?:name|character)\s*:?\s*(.+)', text, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else 'Unknown'
        
        # Extract template
        template_match = re.search(r'template\s*:?\s*(.+)', text, re.IGNORECASE)
        template = template_match.group(1).strip() if template_match else 'Unknown'
        
        # Parse attributes
        attributes = {}
        for attr in self.attributes:
            pattern = rf'(?:{attr}|{self.attribute_aliases.get(attr, "")})\s*:?\s*([0-9]+D(?:\+[0-9]+)?)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                attributes[attr] = self._normalize_dice_code(match.group(1))
            else:
                attributes[attr] = '2D'
        
        # Parse skills
        skills = {}
        # Look for patterns like "Blaster: 4D+2" or "Piloting 3D+1"
        skill_pattern = r'(\w+(?:\s+\w+)*)\s*:?\s*([0-9]+D(?:\+[0-9]+)?)'
        for match in re.finditer(skill_pattern, text):
            skill_name = self._normalize_skill_name(match.group(1))
            dice_code = match.group(2)
            if self._is_valid_skill(skill_name):
                skills[skill_name] = self._normalize_dice_code(dice_code)
        
        # Parse Force/Character info
        fp_match = re.search(r'force\s+points?\s*:?\s*(\d+)', text, re.IGNORECASE)
        force_points = int(fp_match.group(1)) if fp_match else 1
        
        cp_match = re.search(r'character\s+points?\s*:?\s*(\d+)', text, re.IGNORECASE)
        character_points = int(cp_match.group(1)) if cp_match else 5
        
        dsp_match = re.search(r'dark\s+side\s+points?\s*:?\s*(\d+)', text, re.IGNORECASE)
        dark_side_points = int(dsp_match.group(1)) if dsp_match else 0
        
        force_sensitive = bool(re.search(r'force\s+sensitive', text, re.IGNORECASE))
        
        # Parse equipment
        equipment = []
        equipment_match = re.search(r'equipment\s*:?\s*(.+?)(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
        if equipment_match:
            equipment_text = equipment_match.group(1)
            equipment = [item.strip() for item in re.split(r'[,\n]', equipment_text) if item.strip()]
        
        # Parse credits
        credits_match = re.search(r'credits?\s*:?\s*(\d+)', text, re.IGNORECASE)
        credits = int(credits_match.group(1)) if credits_match else 1000
        
        return StarWarsCharacter(
            name=name,
            template=template,
            attributes=attributes,
            skills=skills,
            force_points=force_points,
            character_points=character_points,
            dark_side_points=dark_side_points,
            force_sensitive=force_sensitive,
            equipment=equipment,
            credits=credits
        )
    
    def _normalize_dice_code(self, dice_code: str) -> str:
        """Normalize dice codes to standard format (e.g., '3D+2')"""
        if not dice_code:
            return '2D'
        
        # Clean up the input
        dice_code = dice_code.strip().upper().replace(' ', '')
        
        # Handle various formats
        if re.match(r'^\d+D(\+\d+)?$', dice_code):
            return dice_code
        elif re.match(r'^\d+D(\+\d+)?\+\d+$', dice_code):
            # Handle double plus like "3D+1+2" -> "3D+3"
            parts = dice_code.split('+')
            base = parts[0]  # "3D"
            total_bonus = sum(int(x) for x in parts[1:] if x.isdigit())
            return f"{base}+{total_bonus}" if total_bonus > 0 else base
        elif re.match(r'^\d+$', dice_code):
            # Just a number, assume it's dice
            return f"{dice_code}D"
        elif re.match(r'^\d+\+\d+$', dice_code):
            # Format like "3+2", assume it means "3D+2"
            parts = dice_code.split('+')
            return f"{parts[0]}D+{parts[1]}"
        else:
            return '2D'  # Default fallback
    
    def _normalize_skill_name(self, skill_name: str) -> str:
        """Normalize skill names to standard format"""
        # Convert to lowercase and replace spaces/hyphens with underscores
        normalized = skill_name.lower().strip()
        normalized = re.sub(r'[\s\-]+', '_', normalized)
        
        # Handle common aliases
        aliases = {
            'lightsabre': 'lightsaber',
            'melee': 'melee_combat',
            'brawl': 'brawling',
            'pilot': 'piloting',
            'astro': 'astrogation',
            'computer': 'computer_programming',
            'repair': 'blaster_repair',  # Default to blaster repair
            'medicine': 'medicine',
            'first_aid': 'first_aid'
        }
        
        return aliases.get(normalized, normalized)
    
    def _is_valid_skill(self, skill_name: str) -> bool:
        """Check if a skill name is valid for WEG Star Wars"""
        all_skills = [skill for skills_list in self.skill_categories.values() for skill in skills_list]
        return skill_name in all_skills or skill_name in self.force_powers
    
    def _safe_int(self, value: str, default: int) -> int:
        """Safely convert string to int with default"""
        try:
            return int(value) if value and value.strip() else default
        except (ValueError, TypeError):
            return default
    
    def get_skill_attribute(self, skill_name: str) -> str:
        """Get the governing attribute for a skill"""
        normalized = self._normalize_skill_name(skill_name)
        for attribute, skills in self.skill_categories.items():
            # Normalize each skill in the list for comparison
            if any(self._normalize_skill_name(s) == normalized for s in skills):
                return attribute
        return None  # Or 'dexterity' as a fallback if you prefer
    
    def calculate_untrained_skill(self, character: StarWarsCharacter, skill_name: str) -> str:
        """Calculate dice code for untrained skill use"""
        governing_attr = self.get_skill_attribute(skill_name)
        attr_dice = character.attributes.get(governing_attr, '2D')
        
        # Untrained skills are at -1D penalty
        return self._apply_dice_penalty(attr_dice, 1)
    
    def calculate_untrained_skill_from_data(self, character_data: Dict, skill_name: str) -> str:
        """Calculate dice code for untrained skill use from character data dict"""
        governing_attr = self.get_skill_attribute(skill_name)
        attr_dice = character_data.get('attributes', {}).get(governing_attr, '2D')

        # No penalty for untrained skills
        return attr_dice
    
    def _apply_dice_penalty(self, dice_code: str, penalty_dice: int) -> str:
        """Apply dice penalty to a dice code"""
        match = re.match(r'(\d+)D(\+(\d+))?', dice_code)
        if not match:
            return '1D'
        
        base_dice = int(match.group(1))
        bonus_pips = int(match.group(3)) if match.group(3) else 0
        
        # Convert to total pips (each die = 3 pips), apply penalty, convert back
        total_pips = (base_dice * 3) + bonus_pips - (penalty_dice * 3)
        
        if total_pips <= 3:
            return '1D'
        
        new_dice = total_pips // 3
        new_bonus = total_pips % 3
        
        if new_bonus > 0:
            return f"{new_dice}D+{new_bonus}"
        else:
            return f"{new_dice}D"
    
    def validate_character(self, character: StarWarsCharacter) -> List[str]:
        """Validate character data and return list of warnings/errors"""
        warnings = []
        
        # Check for missing required fields
        if not character.name or character.name == 'Unknown':
            warnings.append("Character name is missing or set to 'Unknown'")
        
        # Check attributes
        for attr in self.attributes:
            if attr not in character.attributes:
                warnings.append(f"Missing attribute: {attr}")
            else:
                dice_code = character.attributes[attr]
                if not re.match(r'^\d+D(\+\d+)?$', dice_code):
                    warnings.append(f"Invalid dice code for {attr}: {dice_code}")
        
        # Check for unrealistic values
        if character.force_points < 0:
            warnings.append("Force Points cannot be negative")
        if character.character_points < 0:
            warnings.append("Character Points cannot be negative")
        if character.dark_side_points < 0:
            warnings.append("Dark Side Points cannot be negative")
        if character.credits < 0:
            warnings.append("Credits cannot be negative")
        
        return warnings

# Example usage and testing
if __name__ == "__main__":
    parser = WEGStarWarsParser()
    
    # Example JSON data
    example_json = '''
    {
        "name": "Han Solo",
        "template": "Smuggler",
        "attributes": {
            "dexterity": "3D+1",
            "knowledge": "2D+1",
            "mechanical": "4D",
            "perception": "3D",
            "strength": "3D+2",
            "technical": "2D+2"
        },
        "skills": {
            "blaster": "5D",
            "piloting": "6D+2",
            "astrogation": "5D+1",
            "con": "4D+1",
            "bargain": "4D"
        },
        "force_points": 1,
        "character_points": 5,
        "dark_side_points": 0,
        "force_sensitive": false,
        "equipment": ["Heavy Blaster Pistol", "Millennium Falcon"],
        "credits": 2500
    }
    '''
    
    # Test parsing
    character = parser.parse_json_content(example_json)
    print(f"Parsed character: {character.name} ({character.template})")
    print(f"Blaster skill: {character.skills.get('blaster', 'Untrained')}")
    
    # Test validation
    warnings = parser.validate_character(character)
    if warnings:
        print("Warnings:", warnings)
    else:
        print("Character validation passed!")