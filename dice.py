import random
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class DiceResult:
    """Result of a dice roll"""
    total: int
    dice_code: str
    individual_dice: List[int]
    bonus: int
    breakdown: str
    wild_die_result: int = None
    wild_die_exploded: bool = False
    complications: List[str] = None
    
    def __post_init__(self):
        if self.complications is None:
            self.complications = []

class WEGDiceRoller:
    """Dice roller for West End Games Star Wars RPG"""
    
    def __init__(self, use_wild_die: bool = True):
        self.use_wild_die = use_wild_die
        self.random = random.Random()
    
    def roll(self, dice_code: str, modifier: int = 0, difficulty: str = None) -> Dict[str, Any]:
        """
        Roll dice using WEG Star Wars dice code
        
        Args:
            dice_code: Dice code like "3D+2", "4D", "2D+1+2"
            modifier: Additional modifier to add
            difficulty: Optional difficulty name for comparison
            
        Returns:
            Dictionary with roll results
        """
        try:
            # Parse the dice code
            num_dice, bonus = self._parse_dice_code(dice_code)
            total_bonus = bonus + modifier
            
            # Roll the dice
            dice_results = []
            wild_die_result = None
            wild_die_exploded = False
            complications = []
            
            if num_dice <= 0:
                # Handle edge case of 0 or negative dice
                total = total_bonus
                breakdown = f"No dice + {total_bonus}" if total_bonus != 0 else "0"
            else:
                # Roll regular dice (all but one if using wild die)
                regular_dice = num_dice - 1 if self.use_wild_die and num_dice > 0 else num_dice
                
                for i in range(regular_dice):
                    roll = self.random.randint(1, 6)
                    dice_results.append(roll)
                
                # Roll wild die if applicable
                if self.use_wild_die and num_dice > 0:
                    wild_die_result, wild_exploded, wild_complications = self._roll_wild_die()
                    dice_results.append(wild_die_result)
                    wild_die_exploded = wild_exploded
                    complications.extend(wild_complications)
                
                # Calculate total
                dice_total = sum(dice_results)
                total = dice_total + total_bonus
                
                # Create breakdown string
                breakdown = self._create_breakdown(dice_results, total_bonus, wild_die_result, wild_die_exploded)
            
            # Check against difficulty if provided
            difficulty_info = self._check_difficulty(total, difficulty) if difficulty else None
            
            return {
                'total': total,
                'dice_code': dice_code,
                'individual_dice': dice_results,
                'bonus': total_bonus,
                'breakdown': breakdown,
                'wild_die_result': wild_die_result,
                'wild_die_exploded': wild_die_exploded,
                'complications': complications,
                'difficulty': difficulty_info,
                'success': difficulty_info['success'] if difficulty_info else None
            }
            
        except Exception as e:
            return {
                'error': f"Error rolling dice: {str(e)}",
                'total': 0,
                'dice_code': dice_code,
                'breakdown': f"Error: {str(e)}"
            }
    
    def _parse_dice_code(self, dice_code: str) -> Tuple[int, int]:
        """Parse a dice code like '3D+2' into number of dice and bonus"""
        if not dice_code:
            return 0, 0
        
        # Clean up the input
        dice_code = dice_code.strip().upper().replace(' ', '')
        
        # Handle various formats
        if re.match(r'^\d+D(\+\d+)?$', dice_code):
            # Standard format: "3D" or "3D+2"
            parts = dice_code.split('+')
            dice_part = parts[0]  # "3D"
            num_dice = int(dice_part.replace('D', ''))
            bonus = int(parts[1]) if len(parts) > 1 else 0
            return num_dice, bonus
            
        elif re.match(r'^\d+D(\+\d+)+$', dice_code):
            # Multiple bonuses: "3D+1+2" -> "3D+3"
            parts = dice_code.split('+')
            dice_part = parts[0]  # "3D"
            num_dice = int(dice_part.replace('D', ''))
            bonus = sum(int(x) for x in parts[1:] if x.isdigit())
            return num_dice, bonus
            
        elif re.match(r'^\d+D-\d+$', dice_code):
            # Negative bonus: "3D-1"
            parts = dice_code.split('-')
            dice_part = parts[0]  # "3D"
            num_dice = int(dice_part.replace('D', ''))
            bonus = -int(parts[1])
            return num_dice, bonus
            
        elif re.match(r'^\d+$', dice_code):
            # Just a number, assume it's dice count
            return int(dice_code), 0
            
        else:
            raise ValueError(f"Invalid dice code format: {dice_code}")
    
    def _roll_wild_die(self) -> Tuple[int, bool, List[str]]:
        """
        Roll the wild die with WEG Star Wars rules
        
        Returns:
            (final_result, exploded, complications)
        """
        total = 0
        exploded = False
        complications = []
        
        while True:
            roll = self.random.randint(1, 6)
            total += roll
            
            if roll == 1:
                # Complication on natural 1
                complications.append("Wild die complication (rolled 1)")
                break
            elif roll == 6:
                # Exploding die on natural 6
                exploded = True
                # Continue rolling
            else:
                # Normal result, stop rolling
                break
        
        return total, exploded, complications
    
    def _create_breakdown(self, dice_results: List[int], bonus: int, wild_die_result: int = None, wild_exploded: bool = False) -> str:
        """Create a human-readable breakdown of the roll"""
        if not dice_results:
            return f"No dice + {bonus}" if bonus != 0 else "0"
        
        # Separate regular dice from wild die
        if wild_die_result is not None and len(dice_results) > 0:
            regular_dice = dice_results[:-1]
            wild_die = dice_results[-1]
        else:
            regular_dice = dice_results
            wild_die = None
        
        breakdown_parts = []
        
        # Regular dice
        if regular_dice:
            regular_str = " + ".join(str(d) for d in regular_dice)
            breakdown_parts.append(f"[{regular_str}]")
        
        # Wild die
        if wild_die is not None:
            wild_str = f"**{wild_die}**" if wild_exploded else str(wild_die)
            breakdown_parts.append(f"Wild: {wild_str}")
        
        # Bonus
        if bonus > 0:
            breakdown_parts.append(f"+{bonus}")
        elif bonus < 0:
            breakdown_parts.append(str(bonus))
        
        # Total
        total = sum(dice_results) + bonus
        breakdown = " ".join(breakdown_parts) + f" = **{total}**"
        
        return breakdown
    
    def _check_difficulty(self, total: int, difficulty: str) -> Dict[str, Any]:
        """Check roll result against WEG Star Wars difficulty numbers"""
        difficulties = {
            'very_easy': 1,
            'easy': 5,
            'moderate': 10,
            'difficult': 15,
            'very_difficult': 20,
            'heroic': 25,
            'legendary': 30
        }
        
        # Normalize difficulty name
        difficulty_key = difficulty.lower().replace(' ', '_')
        
        if difficulty_key in difficulties:
            target = difficulties[difficulty_key]
            success = total >= target
            margin = total - target
            
            return {
                'name': difficulty.title(),
                'target': target,
                'success': success,
                'margin': margin
            }
        else:
            # Try to parse as a number
            try:
                target = int(difficulty)
                success = total >= target
                margin = total - target
                
                return {
                    'name': f"Target {target}",
                    'target': target,
                    'success': success,
                    'margin': margin
                }
            except ValueError:
                return {
                    'name': difficulty,
                    'target': None,
                    'success': None,
                    'margin': None,
                    'error': f"Unknown difficulty: {difficulty}"
                }
    
    def roll_multiple(self, dice_code: str, count: int, modifier: int = 0) -> List[Dict[str, Any]]:
        """Roll the same dice code multiple times"""
        results = []
        for i in range(count):
            result = self.roll(dice_code, modifier)
            results.append(result)
        return results
    
    def roll_opposed(self, dice_code1: str, dice_code2: str, modifier1: int = 0, modifier2: int = 0) -> Dict[str, Any]:
        """Roll opposed checks between two dice codes"""
        roll1 = self.roll(dice_code1, modifier1)
        roll2 = self.roll(dice_code2, modifier2)
        
        winner = None
        margin = 0
        
        if roll1['total'] > roll2['total']:
            winner = 1
            margin = roll1['total'] - roll2['total']
        elif roll2['total'] > roll1['total']:
            winner = 2
            margin = roll2['total'] - roll1['total']
        else:
            winner = 0  # Tie
            margin = 0
        
        return {
            'roll1': roll1,
            'roll2': roll2,
            'winner': winner,
            'margin': margin,
            'tie': winner == 0
        }
    
    def roll_damage(self, damage_code: str, armor_value: int = 0) -> Dict[str, Any]:
        """Roll damage and apply armor reduction"""
        damage_roll = self.roll(damage_code)
        
        if 'error' in damage_roll:
            return damage_roll
        
        raw_damage = damage_roll['total']
        final_damage = max(0, raw_damage - armor_value)
        damage_reduced = raw_damage - final_damage
        
        return {
            'raw_damage': raw_damage,
            'armor_value': armor_value,
            'final_damage': final_damage,
            'damage_reduced': damage_reduced,
            'damage_roll': damage_roll
        }
    
    def get_difficulty_list(self) -> Dict[str, int]:
        """Get list of standard WEG Star Wars difficulties"""
        return {
            'Very Easy': 1,
            'Easy': 5,
            'Moderate': 10,
            'Difficult': 15,
            'Very Difficult': 20,
            'Heroic': 25,
            'Legendary': 30
        }
    
    def set_seed(self, seed: int):
        """Set random seed for reproducible results (useful for testing)"""
        self.random.seed(seed)
    
    def roll_force_power(self, dice_code: str, difficulty: str, dark_side_temptation: bool = False) -> Dict[str, Any]:
        """Special roll for Force powers with dark side temptation rules"""
        base_roll = self.roll(dice_code, difficulty=difficulty)
        
        if 'error' in base_roll:
            return base_roll
        
        result = base_roll.copy()
        result['force_power'] = True
        result['dark_side_temptation'] = dark_side_temptation
        
        # Check for dark side temptation (if wild die shows 1 and roll fails)
        if (dark_side_temptation and 
            base_roll.get('wild_die_result') == 1 and 
            base_roll.get('difficulty', {}).get('success') == False):
            result['complications'].append("Dark Side temptation - gain a Dark Side Point for easier success")
        
        return result

# Utility functions for common WEG Star Wars rolls
class WEGRollHelper:
    """Helper class for common WEG Star Wars roll types"""
    
    def __init__(self, dice_roller: WEGDiceRoller):
        self.roller = dice_roller
    
    def skill_roll(self, skill_dice: str, difficulty: str = "moderate", modifier: int = 0) -> Dict[str, Any]:
        """Standard skill roll"""
        return self.roller.roll(skill_dice, modifier, difficulty)
    
    def attribute_roll(self, attribute_dice: str, difficulty: str = "moderate", modifier: int = 0) -> Dict[str, Any]:
        """Standard attribute roll"""
        return self.roller.roll(attribute_dice, modifier, difficulty)
    
    def blaster_attack(self, blaster_skill: str, range_modifier: int = 0, cover_modifier: int = 0) -> Dict[str, Any]:
        """Blaster attack roll with range and cover modifiers"""
        total_modifier = range_modifier + cover_modifier
        return self.roller.roll(blaster_skill, total_modifier, "moderate")
    
    def lightsaber_attack(self, lightsaber_skill: str, opponent_dodge: str = None) -> Dict[str, Any]:
        """Lightsaber attack, optionally opposed by dodge"""
        if opponent_dodge:
            return self.roller.roll_opposed(lightsaber_skill, opponent_dodge)
        else:
            return self.roller.roll(lightsaber_skill, difficulty="moderate")
    
    def starship_piloting(self, piloting_skill: str, maneuver_difficulty: str = "moderate") -> Dict[str, Any]:
        """Starship piloting maneuver"""
        return self.roller.roll(piloting_skill, difficulty=maneuver_difficulty)
    
    def force_power_roll(self, control_dice: str, sense_dice: str, alter_dice: str, 
                        power_difficulty: str = "moderate") -> Dict[str, Any]:
        """Force power roll using Control, Sense, and Alter"""
        # For simplicity, use the highest of the three attributes
        # In a full implementation, you'd handle each aspect separately
        dice_codes = [control_dice, sense_dice, alter_dice]
        # Use the first non-empty dice code (simplified)
        for dice_code in dice_codes:
            if dice_code and dice_code != "0D":
                return self.roller.roll_force_power(dice_code, power_difficulty, dark_side_temptation=True)
        
        return self.roller.roll("1D", difficulty=power_difficulty)

# Example usage and testing
if __name__ == "__main__":
    # Test the dice roller
    roller = WEGDiceRoller()
    helper = WEGRollHelper(roller)
    
    print("=== WEG Star Wars Dice Roller Test ===")
    
    # Test basic rolls
    print("\n1. Basic Rolls:")
    print("3D+2:", roller.roll("3D+2"))
    print("4D:", roller.roll("4D"))
    print("2D+1:", roller.roll("2D+1"))
    
    # Test difficulty checks
    print("\n2. Difficulty Checks:")
    print("3D+2 vs Moderate:", roller.roll("3D+2", difficulty="moderate"))
    print("4D vs Difficult:", roller.roll("4D", difficulty="difficult"))
    
    # Test opposed rolls
    print("\n3. Opposed Roll:")
    opposed = roller.roll_opposed("4D+1", "3D+2")
    print(f"4D+1 vs 3D+2: Winner = {opposed['winner']}, Margin = {opposed['margin']}")
    
    # Test damage
    print("\n4. Damage Roll:")
    damage = roller.roll_damage("5D", armor_value=2)
    print(f"5D damage vs 2 armor: {damage['final_damage']} damage")
    
    # Test helper functions
    print("\n5. Helper Functions:")
    skill_result = helper.skill_roll("4D+2", "difficult")
    print(f"Skill roll: {skill_result['total']} vs Difficult")
    
    print("\n6. Difficulties:")
    for name, value in roller.get_difficulty_list().items():
        print(f"{name}: {value}")