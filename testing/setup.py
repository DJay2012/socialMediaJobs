"""
Setup script for Social Media Jobs
Helps configure the environment and install dependencies
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_env_file():
    """Create .env file from template"""
    env_file = Path('.env')
    template_file = Path('environment_template.txt')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if not template_file.exists():
        print("❌ Environment template not found")
        return
    
    try:
        shutil.copy(template_file, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your actual API keys and database credentials")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

def install_dependencies():
    """Install required Python packages"""
    try:
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['tokens', 'logs', 'backups']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def check_env_variables():
    """Check if required environment variables are set"""
    required_vars = [
        'YOUTUBE_API_KEY',
        'TWITTER_BEARER_TOKEN', 
        'APIFY_API_TOKEN',
        'MONGO_URI'
    ]
    
    missing_vars = []
    
    # Try to load from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment variables")
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or system environment")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_database_connection():
    """Test database connection"""
    try:
        from config import config
        client = config.get_mongo_client()
        client.admin.command('ping')
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Social Media Jobs...")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed - could not install dependencies")
        return
    
    # Check environment variables
    if not check_env_variables():
        print("⚠️  Setup incomplete - please configure environment variables")
        return
    
    # Test database connection
    if not test_database_connection():
        print("⚠️  Setup incomplete - please check database configuration")
        return
    
    print("=" * 50)
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your actual API keys")
    print("2. Test the improved scrapers:")
    print("   python youtube_scraper_improved.py")
    print("   python twitter_scraper_improved.py")
    print("3. Set up cron jobs or use the shell scripts for automation")

if __name__ == "__main__":
    main()
