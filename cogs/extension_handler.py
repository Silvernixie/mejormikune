import logging
import importlib
import inspect
import os
import sys
import traceback
from discord.ext import commands

logger = logging.getLogger("Extension_Handler")

async def fix_extension(bot, cog_name):
    """Attempts to fix common issues with extensions."""
    cog_path = f'cogs.{cog_name}'
    logger.info(f"Attempting to fix module: {cog_path}")
    
    try:
        # Import the module to analyze it
        if cog_path in sys.modules:
            # Reload the module if it's already loaded
            module = importlib.reload(sys.modules[cog_path])
        else:
            module = importlib.import_module(cog_path)
        
        # Check if setup function exists and is properly defined
        if not hasattr(module, 'setup'):
            logger.error(f"Module {cog_path} is missing the setup function")
            return False
        
        setup_func = getattr(module, 'setup')
        if not inspect.iscoroutinefunction(setup_func):
            # Fix non-async setup function
            logger.info(f"Converting non-async setup function in {cog_path} to async")
            
            # Create a fixed version of the file
            file_path = module.__file__
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace the setup function definition
            if "def setup(bot):" in content:
                content = content.replace(
                    "def setup(bot):", 
                    "async def setup(bot):"
                )
                
                # Replace direct bot.add_cog with await bot.add_cog
                content = content.replace(
                    "bot.add_cog(", 
                    "await bot.add_cog("
                )
                
                # Write the fixed content back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"Fixed setup function in {cog_path}")
                
                # Reload the module after fixing
                importlib.reload(sys.modules[cog_path])
                return True
            else:
                logger.error(f"Could not find setup function in {cog_path}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error while fixing {cog_path}: {e}")
        return False

async def safe_load_extension(bot, cog_name):
    """Safely load an extension with error handling and auto-fixing."""
    cog_path = f'cogs.{cog_name}'
    
    try:
        await bot.load_extension(cog_path)
        logger.info(f'✅ Module loaded successfully: {cog_path}')
        return True
    except commands.ExtensionAlreadyLoaded:
        await bot.reload_extension(cog_path)
        logger.info(f'🔄 Module reloaded: {cog_path}')
        return True
    except commands.NoEntryPointError:
        logger.error(f'❌ Module {cog_path} has no setup function')
        return False
    except commands.ExtensionFailed as e:
        # Check the specific error
        if "ModuleNotFoundError" in str(e):
            # Missing dependency
            missing_module = str(e).split("No module named '")[-1].split("'")[0]
            logger.error(f'❌ Module {cog_path} requires missing dependency: {missing_module}')
            
            # Suggest pip install
            logger.info(f'💡 Try installing the missing dependency: pip install {missing_module}')
            return False
        elif "CommandRegistrationError" in str(e):
            # Command conflict
            command_name = str(e).split("The command ")[-1].split(" ")[0]
            logger.error(f'❌ Command conflict in {cog_path}: Command "{command_name}" already exists')
            return False
        elif "TypeError: object NoneType can't be used in 'await' expression" in str(e):
            # Missing await
            logger.error(f'❌ Module {cog_path} has sync/async mismatch - attempting to fix')
            if await fix_extension(bot, cog_name):
                # Try loading again after fixing
                return await safe_load_extension(bot, cog_name)
            return False
        else:
            logger.error(f'❌ Error loading module {cog_path}: {e}')
            logger.error(traceback.format_exc())
            return False
    except Exception as e:
        logger.error(f'❌ Unexpected error loading {cog_path}: {e}')
        logger.error(traceback.format_exc())
        return False
