import subprocess
import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger("DEPENDENCIES")

def install_packages():
    packages = [
        "discord.py",
        "python-dotenv",
        "aiohttp",
        "pytz",
        "animec",
        "beautifulsoup4",
        "asyncdagpi",
        "google-search-python",
        "jishaku",
        "pillow",
        "wavelink",
        "spotipy",
        "psutil",
        "requests",
        "motor",
        "dnspython"
    ]
    
    logger.info("Starting installation of required packages...")
    
    for package in packages:
        try:
            logger.info(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            logger.info(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            logger.error(f"Failed to install {package}")
    
    logger.info("Installation completed!")

if __name__ == "__main__":
    install_packages()
    print("\nAll dependencies have been installed. You can now run the bot with 'python main.py'")
