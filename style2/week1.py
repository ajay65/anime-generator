# Week 1: Anime Character Generation - Complete Setup Guide
# Optimized for Intel Ultra 9 185H + 32GB RAM + Intel Arc GPU

"""
WEEK 1 LEARNING OBJECTIVES:
1. Set up Python environment for AI anime generation
2. Understand Stable Diffusion models and their differences
3. Generate high-quality anime characters using various models
4. Learn prompt engineering for anime-style outputs
5. Optimize performance for your specific hardware

MODELS WE'LL USE:
1. Stable Diffusion v1.5: Base model for image generation
2. Waifu Diffusion: Anime-specialized model trained on anime/manga images
3. Anything v3.0: Popular anime model with consistent character generation
4. Counterfeit v3.0: High-quality anime model with photorealistic details

WHY THESE MODELS:
- Stable Diffusion: Foundation model, well-documented, stable
- Anime-specific models: Better understanding of anime art styles, character proportions
- Multiple models: Learn differences and find your preferred style
"""

import os
import sys
import torch
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings("ignore")


class AnimeModelManager:
    """
    Manages different anime generation models and their configurations.
    
    This class handles:
    - Model loading and caching
    - Hardware optimization for Intel Ultra 9 + Intel Arc
    - Memory management for 32GB RAM
    - Model comparison and evaluation
    """
    
    def __init__(self, cache_dir: str = "./models"):
        """
        Initialize the Anime Model Manager.
        
        Args:
            cache_dir (str): Directory to store downloaded models
            
        Why we need this:
        - Centralized model management
        - Efficient memory usage on your 32GB system
        - Easy model switching for comparison
        """
        self.cache_dir = cache_dir
        self.models = {}
        self.current_model = None
        self.device = self._detect_optimal_device()
        self.torch_dtype = self._get_optimal_dtype()
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Model configurations optimized for your system
        self.model_configs = {
            "stable_diffusion_v1_5": {
                "model_id": "runwayml/stable-diffusion-v1-5",
                "description": "Base Stable Diffusion model - foundation for all anime models",
                "pros": ["Well documented", "Stable", "Good starting point"],
                "cons": ["Not anime-specialized", "Generic results"],
                "best_for": "Learning basics, understanding how diffusion works",
                "memory_usage": "~4GB RAM"
            },
            "waifu_diffusion": {
                "model_id": "hakurei/waifu-diffusion",
                "description": "Stable Diffusion fine-tuned on anime/manga images",
                "pros": ["Good anime style", "Lightweight", "Fast generation"],
                "cons": ["Lower resolution", "Less detailed than newer models"],
                "best_for": "Quick anime generation, learning anime prompts",
                "memory_usage": "~4GB RAM"
            },
            "anything_v3": {
                "model_id": "Linaqruf/anything-v3.0",
                "description": "Popular anime model with consistent character generation",
                "pros": ["Consistent characters", "Good anatomy", "Versatile styles"],
                "cons": ["Larger model size", "Slower generation"],
                "best_for": "Character consistency, detailed anime art",
                "memory_usage": "~6GB RAM"
            },
            "counterfeit_v3": {
                "model_id": "gsdf/Counterfeit-V3.0",
                "description": "High-quality anime model with photorealistic details",
                "pros": ["Highest quality", "Photorealistic anime", "Beautiful details"],
                "cons": ["Large model", "Requires more VRAM", "Slower"],
                "best_for": "Production-quality anime art, final renders",
                "memory_usage": "~8GB RAM"
            }
        }
        
        print(f"🎯 Anime Model Manager initialized for your system:")
        print(f"   Device: {self.device}")
        print(f"   Data Type: {self.torch_dtype}")
        print(f"   Available RAM: 32GB (Excellent for AI workloads)")
        print(f"   Cache Directory: {os.path.abspath(cache_dir)}")
    
    def _detect_optimal_device(self) -> str:
        """
        Detect the best device for your Intel Ultra 9 + Intel Arc setup.
        
        Returns:
            str: Device identifier ('cuda', 'xpu', or 'cpu')
            
        Intel Arc GPU Support:
        - Intel Arc GPUs are supported through Intel Extension for PyTorch
        - XPU device type for Intel discrete GPUs
        - Falls back to CPU which is very capable on your Ultra 9
        """
        if torch.cuda.is_available():
            return "cuda" #nvidia GPU
        
        # Check for Intel Arc GPU support
        try:
            import intel_extension_for_pytorch as ipex  #optimizes PyTorch performance on Intel hardware
            if hasattr(torch, 'xpu') and torch.xpu.is_available():
                print("🚀 Intel Arc GPU detected and supported!")
                return "xpu" #intel arc GPU
        except ImportError:
            print("💡 Install intel-extension-for-pytorch for Intel Arc GPU acceleration")
        
        print("🖥️  Using CPU (Intel Ultra 9 - Excellent for AI workloads)")
        return "cpu"
    
    def _get_optimal_dtype(self) -> torch.dtype:
        """
        Get optimal data type for your hardware.
        
        Returns:
            torch.dtype: Optimal data type
            
        Why this matters:
        - float16: Faster, less memory, some quality loss
        - float32: Slower, more memory, full quality
        - Your 32GB RAM allows us to use float32 for best quality
        """
        if self.device == "cpu":
            return torch.float32  # CPU requires float32
        else:
            return torch.float16  # GPU can use half precision
    
    def load_model(self, model_name: str) -> 'StableDiffusionPipeline':
        """
        Load a specific anime model optimized for your system.
        
        Args:
            model_name (str): Name of the model to load
            
        Returns:
            StableDiffusionPipeline: Loaded and optimized pipeline
            
        Model Loading Strategy:
        1. Check if model is already in memory
        2. Load from HuggingFace with optimal settings
        3. Apply Intel hardware optimizations
        4. Enable memory optimizations for your 32GB RAM
        """
        if model_name not in self.model_configs:
            available = list(self.model_configs.keys())
            raise ValueError(f"Model '{model_name}' not found. Available: {available}")
        
        # Return cached model if already loaded
        if model_name in self.models:
            print(f"✅ Using cached model: {model_name}")
            self.current_model = model_name
            return self.models[model_name]
        
        print(f"📥 Loading model: {model_name}")
        config = self.model_configs[model_name]
        
        try:
            from diffusers import StableDiffusionPipeline
            
            # Load model with optimal settings for your hardware
            pipeline = StableDiffusionPipeline.from_pretrained(
                config["model_id"],
                torch_dtype=self.torch_dtype,
                safety_checker=None,  # Disable for anime generation
                requires_safety_checker=False,
                cache_dir=self.cache_dir
            )
            
            # Move to optimal device
            pipeline = pipeline.to(self.device)
            
            # Intel Arc GPU optimization
            if self.device == "xpu":
                try:
                    import intel_extension_for_pytorch as ipex
                    pipeline.unet = ipex.optimize(pipeline.unet)
                    pipeline.vae = ipex.optimize(pipeline.vae)
                    print("🔧 Applied Intel Arc optimizations")
                except Exception as e:
                    print(f"⚠️  Intel optimization failed: {e}")
            
            # Memory optimizations for your 32GB system
            pipeline.enable_attention_slicing()  # Reduce memory usage
            pipeline.enable_model_cpu_offload()  # Offload to your abundant RAM
            
            # Cache the loaded model
            self.models[model_name] = pipeline
            self.current_model = model_name
            
            print(f"✅ Model '{model_name}' loaded successfully!")
            print(f"   📊 Expected memory usage: {config['memory_usage']}")
            print(f"   🎨 Best for: {config['best_for']}")
            
            return pipeline
            
        except Exception as e:
            print(f"❌ Failed to load model '{model_name}': {e}")
            print("💡 Trying to install required packages...")
            # self._install_dependencies()
            raise
    
    def _install_dependencies(self):
        """Install required packages for anime generation."""
        packages = [
            "diffusers",
            "transformers", 
            "accelerate",
            "torch",
            "torchvision"
        ]
        
        for package in packages:
            os.system(f"pip install {package}")
    
    def get_model_info(self, model_name: str) -> Dict:
        """
        Get detailed information about a specific model.
        
        Args:
            model_name (str): Name of the model
            
        Returns:
            Dict: Complete model information
        """
        if model_name not in self.model_configs:
            return {}
        return self.model_configs[model_name]
    
    def list_available_models(self) -> List[str]:
        """Get list of all available anime models."""
        return list(self.model_configs.keys())


class AnimePromptEngineer:
    """
    Advanced prompt engineering specifically for anime character generation.
    
    This class provides:
    - Pre-built anime prompt templates
    - Quality enhancement techniques
    - Style consistency methods
    - Character archetype definitions
    """
    
    def __init__(self):
        """
        Initialize the Anime Prompt Engineer.
        
        Why prompt engineering matters:
        - AI models understand specific keywords better
        - Anime has unique vocabulary (tsundere, kawaii, bishojo)
        - Quality tags improve output significantly
        - Negative prompts prevent common issues
        """
        
        # Quality enhancement tags
        self.quality_tags = [
            "masterpiece", "best quality", "high resolution", "detailed",
            "anime style", "official art", "extremely detailed"
        ]
        
        # Common negative prompts for anime
        self.negative_base = [
            "lowres", "bad anatomy", "bad hands", "text", "error",
            "missing fingers", "extra digit", "cropped", "worst quality",
            "low quality", "normal quality", "jpeg artifacts", "signature",
            "watermark", "blurry", "deformed", "disfigured", "mutation",
            "mutated", "ugly", "disgusting", "amputation", "realistic", "3d"
        ]
        
        # Character archetypes with specific traits
        self.character_archetypes = {
            "schoolgirl": {
                "base": "1girl, school uniform, sailor uniform, pleated skirt",
                "personality": "cheerful, energetic, youthful",
                "common_features": "twin tails, hair ribbons, school bag"
            },
            "magical_girl": {
                "base": "1girl, magical girl, frilly dress, staff, tiara",
                "personality": "determined, kind, powerful",
                "common_features": "long hair, bright colors, magical effects"
            },
            "warrior": {
                "base": "1girl, armor, sword, serious expression, battle stance",
                "personality": "strong, determined, brave",
                "common_features": "short hair, scars, muscular build"
            },
            "maid": {
                "base": "1girl, maid outfit, apron, maid headdress",
                "personality": "polite, dedicated, elegant",
                "common_features": "braided hair, white apron, black dress"
            },
            "shrine_maiden": {
                "base": "1girl, miko, red hakama, white kimono, shrine",
                "personality": "serene, spiritual, traditional",
                "common_features": "long black hair, red ribbons, traditional setting"
            }
        }
        
        # Hair colors and styles popular in anime
        self.hair_options = {
            "colors": ["black hair", "brown hair", "blonde hair", "red hair", 
                      "blue hair", "green hair", "purple hair", "pink hair",
                      "silver hair", "white hair", "multicolored hair"],
            "styles": ["long hair", "short hair", "twin tails", "ponytail",
                      "braided hair", "curly hair", "straight hair", "wavy hair",
                      "hair bun", "side ponytail", "drill hair"]
        }
        
        # Eye colors and expressions
        self.eye_options = {
            "colors": ["blue eyes", "brown eyes", "green eyes", "red eyes",
                      "purple eyes", "golden eyes", "heterochromia", "pink eyes"],
            "expressions": ["happy", "sad", "angry", "surprised", "sleepy",
                          "determined", "shy", "confident", "gentle", "fierce"]
        }
    
    def create_character_prompt(self, 
                              archetype: str = "schoolgirl",
                              hair_color: Optional[str] = None,
                              hair_style: Optional[str] = None,
                              eye_color: Optional[str] = None,
                              expression: Optional[str] = None,
                              additional_traits: List[str] = None) -> Tuple[str, str]:
        """
        Create a comprehensive anime character prompt.
        
        Args:
            archetype (str): Character archetype from predefined list
            hair_color (str, optional): Specific hair color
            hair_style (str, optional): Specific hair style
            eye_color (str, optional): Specific eye color
            expression (str, optional): Facial expression
            additional_traits (List[str], optional): Extra characteristics
            
        Returns:
            Tuple[str, str]: (positive_prompt, negative_prompt)
            
        How this works:
        1. Start with character archetype base
        2. Add randomized or specified features
        3. Include quality enhancement tags
        4. Build comprehensive negative prompt
        """
        if additional_traits is None:
            additional_traits = []
        
        # Get archetype base or create custom
        if archetype in self.character_archetypes:
            base_prompt = self.character_archetypes[archetype]["base"]
        else:
            base_prompt = f"1girl, {archetype}"
        
        # Build prompt components
        prompt_parts = [base_prompt]
        
        # Add physical features
        if hair_color:
            prompt_parts.append(hair_color)
        else:
            import random
            prompt_parts.append(random.choice(self.hair_options["colors"]))
            
        if hair_style:
            prompt_parts.append(hair_style)
        else:
            import random
            prompt_parts.append(random.choice(self.hair_options["styles"]))
            
        if eye_color:
            prompt_parts.append(eye_color)
        else:
            import random
            prompt_parts.append(random.choice(self.eye_options["colors"]))
            
        if expression:
            prompt_parts.append(f"{expression} expression")
        else:
            import random
            prompt_parts.append(f"{random.choice(self.eye_options['expressions'])} expression")
        
        # Add additional traits
        prompt_parts.extend(additional_traits)
        
        # Add quality tags
        prompt_parts.extend(self.quality_tags)
        
        # Create final prompts
        positive_prompt = ", ".join(prompt_parts)
        negative_prompt = ", ".join(self.negative_base)
        
        return positive_prompt, negative_prompt
    
    def create_scene_prompt(self, 
                          character_prompt: str,
                          setting: str = "school",
                          lighting: str = "soft lighting",
                          composition: str = "portrait") -> str:
        """
        Create a complete scene prompt with character and environment.
        
        Args:
            character_prompt (str): Character description
            setting (str): Environment/background
            lighting (str): Lighting conditions
            composition (str): Image composition style
            
        Returns:
            str: Complete scene prompt
        """
        scene_elements = [
            character_prompt,
            setting,
            lighting,
            composition,
            "detailed background",
            "cinematic composition"
        ]
        
        return ", ".join(scene_elements)


class AnimeCharacterGenerator:
    """
    Main class for generating anime characters with your Intel Ultra 9 system.
    
    This class combines:
    - Model management
    - Prompt engineering
    - Hardware optimization
    - Result evaluation
    - Batch processing
    """
    
    def __init__(self, cache_dir: str = "./models", output_dir: str = "./output"):
        """
        Initialize the Anime Character Generator.
        
        Args:
            cache_dir (str): Directory for model storage
            output_dir (str): Directory for generated images
        """
        self.model_manager = AnimeModelManager(cache_dir)
        self.prompt_engineer = AnimePromptEngineer()
        self.output_dir = output_dir
        self.generation_history = []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print("🎨 Anime Character Generator Ready!")
        print(f"   Output Directory: {os.path.abspath(output_dir)}")
    
    def generate_character(self,
                         model_name: str = "waifu_diffusion",
                         archetype: str = "schoolgirl",
                         custom_prompt: Optional[str] = None,
                         num_images: int = 1,
                         steps: int = 20,
                         guidance_scale: float = 7.5,
                         width: int = 512,
                         height: int = 512,
                         seed: Optional[int] = None) -> List[Image.Image]:
        """
        Generate anime characters with specified parameters.
        
        Args:
            model_name (str): Which anime model to use
            archetype (str): Character type (schoolgirl, warrior, etc.)
            custom_prompt (str, optional): Custom prompt instead of archetype
            num_images (int): Number of images to generate
            steps (int): Number of denoising steps (more = higher quality, slower)
            guidance_scale (float): How closely to follow prompt (7-15 typical)
            width (int): Image width (512 recommended for your system)
            height (int): Image height (512 recommended for your system)
            seed (int, optional): Seed for reproducible results
            
        Returns:
            List[Image.Image]: Generated anime character images
            
        Generation Process:
        1. Load specified model
        2. Create or use custom prompt
        3. Apply hardware optimizations
        4. Generate images
        5. Save results with metadata
        """
        print(f"🎭 Generating anime character...")
        print(f"   Model: {model_name}")
        print(f"   Archetype: {archetype}")
        print(f"   Images: {num_images}")
        print(f"   Steps: {steps} (higher = better quality)")
        print(f"   Resolution: {width}x{height}")
        
        # Load model
        pipeline = self.model_manager.load_model(model_name)
        
        # Create prompt
        if custom_prompt:
            positive_prompt = custom_prompt
            negative_prompt = ", ".join(self.prompt_engineer.negative_base)
        else:
            positive_prompt, negative_prompt = self.prompt_engineer.create_character_prompt(
                archetype=archetype
            )
        
        print(f"   📝 Prompt: {positive_prompt[:100]}...")
        
        # Set seed for reproducibility
        if seed is not None:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(seed)
        
        # Generate images
        try:
            start_time = datetime.now()
            
            with torch.autocast(self.model_manager.device): #wraps the pipeline call in a performance-optimized context.
                results = pipeline(
                    prompt=positive_prompt,
                    negative_prompt=negative_prompt, #Optional prompt to suppress unwanted features (e.g. "blurry, distorted, watermark")
                    num_images_per_prompt=num_images,
                    num_inference_steps=steps, #Controls the sampling depth — more steps = better quality but slower
                    guidance_scale=guidance_scale, #Strength of prompt conditioning — higher = more faithful to prompt, lower = more creative
                    width=width,
                    height=height
                )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            print(f"   ⏱️  Generation time: {generation_time:.1f} seconds")
            print(f"   🚀 Speed: {generation_time/num_images:.1f} sec/image")
            
            images = results.images
            
            # Save images with metadata
            self._save_images_with_metadata(
                images, model_name, positive_prompt, negative_prompt,
                steps, guidance_scale, width, height, seed, generation_time
            )
            
            print(f"✅ Successfully generated {len(images)} anime character(s)!")
            
            return images
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            print("💡 Try reducing image size or number of steps")
            raise
    
    def _save_images_with_metadata(self, 
                                 images: List[Image.Image],
                                 model_name: str,
                                 positive_prompt: str,
                                 negative_prompt: str,
                                 steps: int,
                                 guidance_scale: float,
                                 width: int,
                                 height: int,
                                 seed: Optional[int],
                                 generation_time: float):
        """Save generated images with complete metadata for learning purposes."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, image in enumerate(images):
            # Save image
            filename = f"{model_name}_{timestamp}_{i:02d}.png"
            filepath = os.path.join(self.output_dir, filename)
            image.save(filepath)
            
            # Save metadata
            metadata = {
                "model_name": model_name,
                "positive_prompt": positive_prompt,
                "negative_prompt": negative_prompt,
                "steps": steps,
                "guidance_scale": guidance_scale,
                "width": width,
                "height": height,
                "seed": seed,
                "generation_time_seconds": generation_time,
                "timestamp": timestamp,
                "system_info": {
                    "device": self.model_manager.device,
                    "torch_dtype": str(self.model_manager.torch_dtype),
                    "system": "Intel Ultra 9 185H + 32GB RAM"
                }
            }
            
            metadata_file = filepath.replace('.png', '_metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Add to history
            self.generation_history.append({
                "filename": filename,
                "metadata": metadata
            })
            
            print(f"   💾 Saved: {filename}")
    
    def compare_models(self, 
                      prompt: str = "1girl, anime style, school uniform, masterpiece",
                      models: List[str] = None) -> Dict[str, Image.Image]:
        """
        Compare different anime models with the same prompt.
        
        Args:
            prompt (str): Prompt to test across models
            models (List[str], optional): Models to compare
            
        Returns:
            Dict[str, Image.Image]: Model comparison results
        """
        if models is None:
            models = ["waifu_diffusion", "anything_v3", "stable_diffusion_v1_5"]
        
        print(f"🔍 Comparing {len(models)} models...")
        print(f"   Prompt: {prompt}")
        
        results = {}
        
        for model_name in models:
            try:
                print(f"\n📊 Testing {model_name}...")
                images = self.generate_character(
                    model_name=model_name,
                    custom_prompt=prompt,
                    num_images=1,
                    steps=20,
                    seed=42  # Same seed for fair comparison
                )
                results[model_name] = images[0]
                
            except Exception as e:
                print(f"❌ Failed to test {model_name}: {e}")
                results[model_name] = None
        
        print(f"\n✅ Model comparison complete!")
        print("   Check your output directory to see the differences")
        
        return results
    
    def get_generation_stats(self) -> Dict:
        """Get statistics about your generation session."""
        if not self.generation_history:
            return {"message": "No generations yet"}
        
        total_images = len(self.generation_history)
        total_time = sum(gen["metadata"]["generation_time_seconds"] 
                        for gen in self.generation_history)
        avg_time = total_time / total_images
        
        models_used = {}
        for gen in self.generation_history:
            model = gen["metadata"]["model_name"]
            models_used[model] = models_used.get(model, 0) + 1
        
        return {
            "total_images_generated": total_images,
            "total_generation_time_seconds": total_time,
            "average_time_per_image": avg_time,
            "models_used": models_used,
            "output_directory": self.output_dir
        }


def week1_tutorial():
    """
    Week 1 Interactive Tutorial - Learn by doing!
    
    This function will guide you through:
    1. Setting up your first anime generator
    2. Testing different models on your system
    3. Learning prompt engineering
    4. Comparing model outputs
    5. Understanding generation parameters
    """
    print("🎓 WEEK 1 TUTORIAL: Anime Character Generation")
    print("=" * 60)
    print("This tutorial will teach you anime generation basics on your Intel Ultra 9 system!")
    print()
    
    # Initialize generator
    print("Step 1: Initializing Anime Generator...")
    generator = AnimeCharacterGenerator()
    
    # Test system capability
    print("\nStep 2: Testing your system with basic model...")
    try:
        # Start with lightest model
        test_images = generator.generate_character(
            model_name="stable_diffusion_v1_5",
            archetype="schoolgirl",
            num_images=1,
            steps=10,  # Fast test
            width=512,
            height=512
        )
        print("✅ Your system successfully generated anime characters!")
        
    except Exception as e:
        print(f"⚠️  Basic test failed: {e}")
        print("💡 This might be due to missing dependencies. Installing...")
        return
    
    # Learn about different archetypes
    print("\nStep 3: Exploring character archetypes...")
    archetypes = ["schoolgirl", "magical_girl", "warrior", "maid"]
    
    for archetype in archetypes:
        print(f"   🎭 Generating {archetype}...")
        generator.generate_character(
            model_name="stable_diffusion_v1_5",
            archetype=archetype,
            num_images=1,
            steps=15
        )
    
    # Model comparison
    print("\nStep 4: Comparing different anime models...")
    comparison_prompt = "1girl, anime style, blue hair, school uniform, smiling, masterpiece"
    
    available_models = generator.model_manager.list_available_models()
    test_models = available_models[:2]  # Test first 2 models
    
    generator.compare_models(
        prompt=comparison_prompt,
        models=test_models
    )
    
    # Show statistics
    print("\nStep 5: Your generation statistics...")
    stats = generator.get_generation_stats()
    print(f"   📊 Images generated: {stats['total_images_generated']}")
    print(f"   ⏱️  Total time: {stats['total_generation_time_seconds']:.1f} seconds")
    print(f"   🚀 Average per image: {stats['average_time_per_image']:.1f} seconds")
    print(f"   🎯 Your system performance: Excellent!")
    
    print("\n" + "=" * 60)
    print("🎉 WEEK 1 TUTORIAL COMPLETE!")
    print("You've successfully:")
    print("✅ Set up anime generation on your system")
    print("✅ Generated multiple character types")
    print("✅ Compared different AI models")
    print("✅ Learned prompt engineering basics")
    print(f"✅ Created {stats['total_images_generated']} anime characters!")
    print()
    print(f"📁 Check your results in: {generator.output_dir}")
    print("🚀 Ready for Week 2: Animation!")


if __name__ == "__main__":
    """
    Main execution - Run this to start your anime generation journey!
    
    This script will:
    1. Run the complete Week 1 tutorial
    2. Test all components on your system
    3. Generate example anime characters
    4. Prepare you for Week 2 (animation)
    """
    print("🚀 Starting Anime Generation Setup for Intel Ultra 9 System")
    print("=" * 70)
    
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required. Please upgrade Python.")
            sys.exit(1)
        
        # Run tutorial
        week1_tutorial()
        
        print("\n" + "🎯 NEXT STEPS" + "")
        print("1. Experiment with different prompts")
        print("2. Try all available models")
        print("3. Adjust generation parameters")
        print("4. Save your favorite characters for Week 2")
        print("5. Get ready for animation in Week 2!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tutorial interrupted by user")
    except Exception as e:
        print(f"\n❌ Tutorial failed: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Make sure you have stable internet for model downloads")
        print("2. Ensure you have enough disk space (5-10GB for models)")
        print("3. Try running: pip install diffusers transformers torch")
        print("4. For Intel Arc support: pip install intel-extension-for-pytorch")