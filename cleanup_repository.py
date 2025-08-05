#!/usr/bin/env python3
"""
Script to clean up the repository by removing unused files
"""

import os
import shutil
from pathlib import Path

def cleanup_repository():
    """Remove unused files and keep only essential ones"""
    
    print("🧹 Cleaning up repository...")
    print("=" * 50)
    
    # Essential files that should be kept
    essential_files = {
        # Core application files
        'main_test.py',
        'ai_engine.py', 
        'config.py',
        'supabase_manager.py',
        'requirements.txt',
        
        # Templates (only the ones actually used)
        'templates/index.html',
        'templates/results.html',
        
        # Documentation
        'README.md',
        
        # Git files
        '.gitignore',
        '.gitattributes',
        
        # Environment and config
        '.env',  # if exists
    }
    
    # Files to remove (unused)
    files_to_remove = [
        # Test and debugging files
        'test_interview_questions.py',
        'check_schema.py', 
        'cleanup_test_data.py',
        'cleanup_repository.py',  # This script will remove itself
        
        # Unused template files
        'templates/result1.html',
        'templates/base1.html',
        
        # Sample resume file in root
        'Sai Nithin Goud K.pdf',
    ]
    
    # Directories to clean (remove contents but keep directory)
    dirs_to_clean = [
        'uploads',
        'backups', 
        'exports',
        'logs',
        '__pycache__'
    ]
    
    # Remove unused files
    print("🗑️  Removing unused files...")
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"   ✅ Removed: {file_path}")
            except Exception as e:
                print(f"   ❌ Failed to remove {file_path}: {e}")
        else:
            print(f"   ⏭️  Skipped (not found): {file_path}")
    
    # Clean directories (remove contents but keep directory)
    print("\n🧹 Cleaning directories...")
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            try:
                # Remove all contents but keep the directory
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                print(f"   ✅ Cleaned: {dir_path}/")
            except Exception as e:
                print(f"   ❌ Failed to clean {dir_path}: {e}")
        else:
            print(f"   ⏭️  Skipped (not found): {dir_path}")
    
    # Create .gitkeep files to preserve empty directories
    print("\n📁 Preserving directory structure...")
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            gitkeep_path = os.path.join(dir_path, '.gitkeep')
            if not os.path.exists(gitkeep_path):
                try:
                    with open(gitkeep_path, 'w') as f:
                        f.write("# This file ensures the directory is preserved in git\n")
                    print(f"   ✅ Created: {gitkeep_path}")
                except Exception as e:
                    print(f"   ❌ Failed to create {gitkeep_path}: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Repository Cleanup Summary")
    print("=" * 50)
    print("✅ Essential files preserved:")
    for file_path in essential_files:
        if os.path.exists(file_path):
            print(f"   - {file_path}")
    
    print(f"\n🗑️  Removed {len(files_to_remove)} unused files")
    print(f"🧹 Cleaned {len(dirs_to_clean)} directories")
    print("\n🎉 Repository cleanup completed!")
    print("\n📝 Next steps:")
    print("   1. Review the changes")
    print("   2. Commit the cleanup to git")
    print("   3. Test the application to ensure everything works")

if __name__ == "__main__":
    cleanup_repository() 