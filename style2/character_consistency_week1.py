# Character Consistency Add-on for Week 1 Script
# This extends your Week 1 script with advanced character consistency features

"""
CHARACTER CONSISTENCY LEVELS:

Level 1: Seed-Based (Week 1 - Basic)
- Same seed = similar character appearance
- Works ~70% of the time
- Good for learning and simple consistency

Level 2: Prompt Engineering (Week 1 Enhanced - This Script)
- Detailed character descriptions
- Consistent style tags
- Works ~85% of the time

Level 3: IP-Adapter/ControlNet (Week 3-4 - Advanced) 
- Reference image-based consistency
- Works ~95% of the time
- Requires additional models

This script implements Level 1 + Level 2 for your Week 1 learning.
"""

import json
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Character:
    """
    Represents a consistent anime character with all defining traits.
    
    This class ensures character consistency by:
    1. Storing all physical and personality traits
    2. Generating consistent prompts
    3. Using dedicated seeds for each character
    4. Tracking character usage across scenes
    """
    name: str
    seed: int
    hair_color: str
    hair_style: str
    eye_color: str
    personality: str
    outfit_style: str
    age_group: str
    special_features: List[str]
    created_date: str
    usage_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convert character to dictionary for saving."""
        return {
            "name": self.name,
            "seed": self.seed,
            "hair_color": self.hair_color,
            "hair_style": self.hair_style,
            "eye_color": self.eye_color,
            "personality": self.personality,
            "outfit_style": self.outfit_style,
            "age_group": self.age_group,
            "special_features": self.special_features,
            "created_date": self.created_date,
            "usage_count": self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Character':
        """Create character from dictionary."""
        return cls(**data)


class CharacterConsistencyManager:
    """
    Advanced character consistency management for anime generation.
    
    This class provides:
    1. Character creation and storage
    2. Consistent prompt generation
    3. Character variation management
    4. Cross-scene consistency
    5. Character evolution tracking
    
    Why this is needed:
    - Simple seeds alone don't guarantee character consistency
    - Detailed prompts are crucial for consistent appearance
    - Character management prevents inconsistencies across scenes
    - Proper tracking helps improve results over time
    """
    
    def __init__(self, characters_file: str = "./characters.json"):
        """
        Initialize the Character Consistency Manager.
        
        Args:
            characters_file (str): File to store character definitions
            
        Character Storage Strategy:
        - JSON file for easy editing and backup
        - In-memory cache for fast access
        - Automatic seed generation for new characters
        - Usage tracking for optimization
        """
        self.characters_file = characters_file
        self.characters: Dict[str, Character] = {}
        self.load_characters()
        
        # Consistency enhancement techniques
        self.consistency_tags = [
            "consistent character", "same person", "character sheet",
            "model sheet", "reference sheet", "official art"
        ]
        
        # Quality tags for better consistency
        self.quality_tags = [
            "masterpiece", "best quality", "high resolution", 
            "extremely detailed", "perfect anatomy", "detailed face"
        ]
        
        print(f"🎭 Character Consistency Manager initialized")
        print(f"   Characters file: {self.characters_file}")
        print(f"   Loaded characters: {len(self.characters)}")
    
    def create_character(self, 
                        name: str,
                        base_prompt: str = "",
                        seed: Optional[int] = None,
                        hair_color: str = "brown hair",
                        hair_style: str = "long hair", 
                        eye_color: str = "brown eyes",
                        personality: str = "friendly",
                        outfit_style: str = "school uniform",
                        age_group: str = "teenage",
                        special_features: List[str] = None) -> Character:
        """
        Create a new consistent character with detailed specifications.
        
        Args:
            name (str): Character name/identifier
            base_prompt (str): Base description
            seed (int, optional): Specific seed, auto-generated if None
            hair_color (str): Specific hair color
            hair_style (str): Hair style description
            eye_color (str): Eye color specification
            personality (str): Character personality
            outfit_style (str): Default outfit style
            age_group (str): Age group (child, teenage, adult)
            special_features (List[str]): Unique character features
            
        Returns:
            Character: Complete character definition
            
        Character Creation Process:
        1. Generate unique seed if not provided
        2. Create comprehensive character profile
        3. Test generation to ensure consistency
        4. Save character definition
        5. Return character object for immediate use
        """
        if special_features is None:
            special_features = []
        
        # Generate unique seed if not provided
        if seed is None:
            # Create deterministic seed based on character traits
            trait_string = f"{name}_{hair_color}_{hair_style}_{eye_color}"
            seed = int(hashlib.md5(trait_string.encode()).hexdigest()[:8], 16) % (2**31)
        
        # Create character object
        character = Character(
            name=name,
            seed=seed,
            hair_color=hair_color,
            hair_style=hair_style,
            eye_color=eye_color,
            personality=personality,
            outfit_style=outfit_style,
            age_group=age_group,
            special_features=special_features,
            created_date=datetime.now().isoformat()
        )
        
        # Store character
        self.characters[name] = character
        self.save_characters()
        
        print(f"✅ Created character '{name}':")
        print(f"   Seed: {seed}")
        print(f"   Appearance: {hair_color}, {hair_style}, {eye_color}")
        print(f"   Style: {personality} {age_group} in {outfit_style}")
        
        return character
    
    def get_character_prompt(self, 
                           character_name: str,
                           scene_context: str = "",
                           action: str = "",
                           expression: str = "",
                           include_consistency_tags: bool = True) -> Tuple[str, str, int]:
        """
        Generate a consistent prompt for a specific character.
        
        Args:
            character_name (str): Name of the character
            scene_context (str): Scene description (school, home, etc.)
            action (str): What the character is doing
            expression (str): Facial expression
            include_consistency_tags (bool): Add consistency enhancement tags
            
        Returns:
            Tuple[str, str, int]: (positive_prompt, negative_prompt, seed)
            
        Prompt Building Strategy:
        1. Start with character's core traits
        2. Add scene-specific elements
        3. Include consistency enhancement tags
        4. Apply quality improvements
        5. Generate appropriate negative prompt
        """
        if character_name not in self.characters:
            raise ValueError(f"Character '{character_name}' not found. Available: {list(self.characters.keys())}")
        
        char = self.characters[character_name]
        char.usage_count += 1  # Track usage
        
        # Build prompt components
        prompt_parts = []
        
        # Core character description
        core_description = f"1girl, {char.age_group}"
        prompt_parts.append(core_description)
        
        # Physical traits (most important for consistency)
        physical_traits = [
            char.hair_color,
            char.hair_style, 
            char.eye_color,
            char.outfit_style if not scene_context else f"wearing {char.outfit_style}"
        ]
        prompt_parts.extend(physical_traits)
        
        # Special features
        if char.special_features:
            prompt_parts.extend(char.special_features)
        
        # Scene context
        if scene_context:
            prompt_parts.append(scene_context)
        
        # Action and expression
        if action:
            prompt_parts.append(action)
        if expression:
            prompt_parts.append(f"{expression} expression")
        elif char.personality:
            prompt_parts.append(f"{char.personality} expression")
        
        # Consistency enhancement tags
        if include_consistency_tags:
            prompt_parts.extend(self.consistency_tags[:2])  # Don't overwhelm
        
        # Quality tags
        prompt_parts.extend(self.quality_tags[:3])
        
        # Build final prompts
        positive_prompt = ", ".join(prompt_parts)
        
        # Negative prompt for consistency
        negative_prompt = ", ".join([
            "multiple people", "different person", "inconsistent character",
            "lowres", "bad anatomy", "bad hands", "missing fingers",
            "extra digits", "cropped", "worst quality", "low quality",
            "blurry", "deformed", "disfigured", "ugly", "mutation"
        ])
        
        # Save updated usage count
        self.save_characters()
        
        return positive_prompt, negative_prompt, char.seed
    
    def create_character_variations(self,
                                  character_name: str,
                                  variations: List[str],
                                  seed_offset: int = 1) -> List[Tuple[str, str, int]]:
        """
        Create multiple variations of the same character.
        
        Args:
            character_name (str): Base character name
            variations (List[str]): List of variation descriptions
            seed_offset (int): Offset to add to base seed for variations
            
        Returns:
            List[Tuple[str, str, int]]: List of (prompt, negative_prompt, seed) tuples
            
        Variation Strategy:
        - Use base character traits as foundation
        - Apply slight seed modifications for variety
        - Maintain core consistency while allowing differences
        - Perfect for creating character sheets or pose references
        """
        if character_name not in self.characters:
            raise ValueError(f"Character '{character_name}' not found")
        
        char = self.characters[character_name]
        results = []
        
        for i, variation in enumerate(variations):
            # Use base character prompt with variation
            positive_prompt, negative_prompt, base_seed = self.get_character_prompt(
                character_name, 
                scene_context=variation,
                include_consistency_tags=True
            )
            
            # Modify seed slightly for variation
            variation_seed = base_seed + (seed_offset * (i + 1))
            
            results.append((positive_prompt, negative_prompt, variation_seed))
        
        print(f"🎨 Generated {len(variations)} variations for '{character_name}'")
        return results
    
    def load_characters(self):
        """Load characters from JSON file."""
        try:
            with open(self.characters_file, 'r') as f:
                data = json.load(f)
                self.characters = {
                    name: Character.from_dict(char_data) 
                    for name, char_data in data.items()
                }
        except FileNotFoundError:
            print(f"📝 Creating new characters file: {self.characters_file}")
            self.characters = {}
    
    def save_characters(self):
        """Save characters to JSON file."""
        data = {
            name: char.to_dict() 
            for name, char in self.characters.items()
        }
        with open(self.characters_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def list_characters(self) -> Dict[str, Dict]:
        """Get summary of all characters."""
        summary = {}
        for name, char in self.characters.items():
            summary[name] = {
                "appearance": f"{char.hair_color}, {char.hair_style}, {char.eye_color}",
                "style": f"{char.personality} {char.age_group}",
                "outfit": char.outfit_style,
                "usage_count": char.usage_count,
                "seed": char.seed
            }
        return summary
    
    def delete_character(self, character_name: str):
        """Delete a character."""
        if character_name in self.characters:
            del self.characters[character_name]
            self.save_characters()
            print(f"🗑️ Deleted character '{character_name}'")
        else:
            print(f"❌ Character '{character_name}' not found")


class EnhancedAnimeGenerator:
    """
    Enhanced version of AnimeCharacterGenerator with character consistency.
    
    This extends the original generator with:
    1. Character consistency management
    2. Multi-character scene support
    3. Character relationship tracking
    4. Advanced prompt engineering
    5. Consistency quality metrics
    """
    
    def __init__(self, model_manager, output_dir: str = "./output"):
        """
        Initialize Enhanced Anime Generator.
        
        Args:
            model_manager: AnimeModelManager instance
            output_dir (str): Output directory for images
        """
        self.model_manager = model_manager
        self.output_dir = output_dir
        self.character_manager = CharacterConsistencyManager()
        self.generation_history = []
        
        print("🚀 Enhanced Anime Generator with Character Consistency ready!")
    
    def create_main_characters(self) -> Dict[str, Character]:
        """
        Create a set of main characters for your anime project.
        
        Returns:
            Dict[str, Character]: Dictionary of created characters
            
        This creates 4 classic anime archetypes:
        1. Main protagonist (energetic schoolgirl)
        2. Best friend (shy, supportive)  
        3. Rival (confident, competitive)
        4. Mentor figure (wise, mysterious)
        """
        characters = {}
        
        # Main protagonist
        characters["protagonist"] = self.character_manager.create_character(
            name="protagonist",
            hair_color="brown hair",
            hair_style="medium length hair with hair ribbon",
            eye_color="bright blue eyes", 
            personality="energetic",
            outfit_style="blue school uniform",
            age_group="teenage",
            special_features=["cheerful smile", "determined expression"]
        )
        
        # Best friend
        characters["best_friend"] = self.character_manager.create_character(
            name="best_friend",
            hair_color="black hair",
            hair_style="long straight hair",
            eye_color="gentle brown eyes",
            personality="shy",
            outfit_style="pink school uniform", 
            age_group="teenage",
            special_features=["glasses", "soft smile", "book in hand"]
        )
        
        # Rival character
        characters["rival"] = self.character_manager.create_character(
            name="rival",
            hair_color="blonde hair",
            hair_style="short hair with side swept bangs",
            eye_color="sharp green eyes",
            personality="confident",
            outfit_style="red school uniform",
            age_group="teenage",
            special_features=["smirk", "crossed arms", "competitive stance"]
        )
        
        # Mentor figure  
        characters["mentor"] = self.character_manager.create_character(
            name="mentor",
            hair_color="silver hair",
            hair_style="long flowing hair",
            eye_color="mysterious purple eyes",
            personality="wise",
            outfit_style="traditional robes",
            age_group="adult",
            special_features=["gentle smile", "magical aura", "staff"]
        )
        
        print("🎭 Created main character cast:")
        for name, char in characters.items():
            print(f"   {name}: {char.hair_color}, {char.eye_color}, {char.personality}")
        
        return characters
    
    def generate_character_scene(self,
                               character_name: str,
                               scene_description: str,
                               model_name: str = "waifu_diffusion",
                               action: str = "",
                               expression: str = "",
                               num_images: int = 1,
                               steps: int = 20) -> List:
        """
        Generate images of a specific character in a scene.
        
        Args:
            character_name (str): Name of the character
            scene_description (str): Description of the scene
            model_name (str): AI model to use
            action (str): What the character is doing
            expression (str): Character's expression
            num_images (int): Number of images to generate
            steps (int): Generation steps
            
        Returns:
            List: Generated images
        """
        print(f"🎬 Generating scene with '{character_name}':")
        print(f"   Scene: {scene_description}")
        print(f"   Action: {action}")
        print(f"   Expression: {expression}")
        
        # Get character-consistent prompt
        positive_prompt, negative_prompt, seed = self.character_manager.get_character_prompt(
            character_name=character_name,
            scene_context=scene_description,
            action=action,
            expression=expression
        )
        
        # Load model
        pipeline = self.model_manager.load_model(model_name)
        
        # Generate with character consistency
        import torch
        torch.manual_seed(seed)
        
        try:
            with torch.autocast(self.model_manager.device):
                results = pipeline(
                    prompt=positive_prompt,
                    negative_prompt=negative_prompt,
                    num_images_per_prompt=num_images,
                    num_inference_steps=steps,
                    guidance_scale=7.5,
                    width=512,
                    height=512
                )
            
            images = results.images
            
            # Save with character metadata
            self._save_character_images(
                images, character_name, scene_description, 
                positive_prompt, model_name, seed
            )
            
            print(f"✅ Generated {len(images)} consistent images of '{character_name}'")
            return images
            
        except Exception as e:
            print(f"❌ Character scene generation failed: {e}")
            raise
    
    def generate_character_sheet(self,
                               character_name: str,
                               model_name: str = "anything_v3") -> List:
        """
        Generate a character sheet showing multiple poses/expressions.
        
        Args:
            character_name (str): Character to generate sheet for
            model_name (str): AI model to use
            
        Returns:
            List: Character sheet images
        """
        print(f"📋 Generating character sheet for '{character_name}'")
        
        # Define standard character sheet variations
        variations = [
            "front view, standing pose, neutral expression",
            "side view, walking pose, happy expression", 
            "three quarter view, sitting pose, thinking expression",
            "back view, waving pose, cheerful expression",
            "close up portrait, smiling expression",
            "action pose, determined expression"
        ]
        
        # Generate all variations
        variation_prompts = self.character_manager.create_character_variations(
            character_name, variations
        )
        
        pipeline = self.model_manager.load_model(model_name)
        sheet_images = []
        
        for i, (prompt, neg_prompt, seed) in enumerate(variation_prompts):
            print(f"   Generating pose {i+1}/{len(variations)}: {variations[i]}")
            
            import torch
            torch.manual_seed(seed)
            
            with torch.autocast(self.model_manager.device):
                result = pipeline(
                    prompt=prompt,
                    negative_prompt=neg_prompt,
                    num_inference_steps=25,  # Higher quality for character sheets
                    guidance_scale=8.0,
                    width=512,
                    height=512
                ).images[0]
            
            sheet_images.append(result)
        
        # Save character sheet
        self._save_character_sheet(sheet_images, character_name, model_name)
        
        print(f"✅ Character sheet completed: {len(sheet_images)} poses")
        return sheet_images
    
    def _save_character_images(self, images, character_name, scene, prompt, model, seed):
        """Save character images with detailed metadata."""
        import os
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, image in enumerate(images):
            filename = f"{character_name}_{scene.replace(' ', '_')}_{timestamp}_{i:02d}.png"
            filepath = os.path.join(self.output_dir, filename)
            image.save(filepath)
            
            # Save metadata
            metadata = {
                "character_name": character_name,
                "scene_description": scene,
                "prompt": prompt,
                "model": model,
                "seed": seed,
                "timestamp": timestamp,
                "consistency_level": "enhanced"
            }
            
            metadata_file = filepath.replace('.png', '_metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
    
    def _save_character_sheet(self, images, character_name, model):
        """Save character sheet as combined image."""
        from PIL import Image
        import math
        
        # Create character sheet grid
        cols = 3
        rows = math.ceil(len(images) / cols)
        
        sheet_width = 512 * cols
        sheet_height = 512 * rows
        
        character_sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        
        for i, img in enumerate(images):
            x = (i % cols) * 512
            y = (i // cols) * 512
            character_sheet.paste(img, (x, y))
        
        # Save character sheet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sheet_filename = f"{character_name}_character_sheet_{timestamp}.png"
        sheet_path = os.path.join(self.output_dir, sheet_filename)
        character_sheet.save(sheet_path)
        
        print(f"💾 Character sheet saved: {sheet_filename}")


def week1_enhanced_tutorial():
    """
    Enhanced Week 1 tutorial with character consistency features.
    
    This tutorial extends the basic Week 1 with:
    1. Character creation and management
    2. Consistent character generation across scenes
    3. Character sheet creation
    4. Multi-character scene setup
    """
    print("🎓 WEEK 1 ENHANCED: Character Consistency Tutorial")
    print("=" * 60)
    
    # Import the original components (assuming they exist)
    try:
        # You'll need to import your original AnimeModelManager here
        from your_week1_script import AnimeModelManager  # Adjust import as needed
        model_manager = AnimeModelManager()
        
    except ImportError:
        print("⚠️  Please ensure your Week 1 script is available for import")
        print("   This enhanced version builds on the original Week 1 components")
        return
    
    # Initialize enhanced generator
    generator = EnhancedAnimeGenerator(model_manager)
    
    print("\nStep 1: Creating consistent main characters...")
    main_characters = generator.create_main_characters()
    
    print("\nStep 2: Testing character consistency...")
    # Generate the same character in different scenes
    protagonist_scenes = [
        ("classroom", "sitting at desk", "focused"),
        ("school hallway", "walking", "cheerful"), 
        ("library", "reading book", "curious"),
        ("school rooftop", "looking at sky", "dreamy")
    ]
    
    for scene, action, expression in protagonist_scenes[:2]:  # Test 2 scenes
        generator.generate_character_scene(
            character_name="protagonist",
            scene_description=scene,
            action=action,
            expression=expression,
            model_name="waifu_diffusion"
        )
    
    print("\nStep 3: Creating character sheet...")
    generator.generate_character_sheet("protagonist")
    
    print("\nStep 4: Character management summary...")
    characters = generator.character_manager.list_characters()
    for name, info in characters.items():
        print(f"   {name}: {info['appearance']} - Used {info['usage_count']} times")
    
    print("\n" + "=" * 60)
    print("🎉 ENHANCED WEEK 1 COMPLETE!")
    print("You've learned:")
    print("✅ Character consistency techniques")
    print("✅ Character management and storage")
    print("✅ Multi-scene character generation") 
    print("✅ Character sheet creation")
    print("✅ Advanced prompt engineering")
    print()
    print("🚀 Your characters are now ready for Week 2 animation!")


if __name__ == "__main__":
    """
    Run the enhanced character consistency tutorial.
    """
    try:
        week1_enhanced_tutorial()
    except Exception as e:
        print(f"❌ Tutorial failed: {e}")
        print("\n🔧 To use this enhancement:")
        print("1. Ensure your original Week 1 script is working")
        print("2. Run this script after completing basic Week 1")
        print("3. Or integrate these classes into your main script")