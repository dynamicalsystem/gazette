import os
from pathlib import Path
from dynamicalsystem.pytests.environment import variables as environment_variables


def test_environment_variables_and_directory(environment_variables):
    """Test that environment variables are set and directory exists."""
    # Log the environment variables
    folder = os.environ.get('DYNAMICALSYSTEM_FOLDER', 'NOT SET')
    environment = os.environ.get('DYNAMICALSYSTEM_ENVIRONMENT', 'NOT SET')
    
    print(f"\nEnvironment Variables:")
    print(f"  DYNAMICALSYSTEM_FOLDER: {folder}")
    print(f"  DYNAMICALSYSTEM_ENVIRONMENT: {environment}")
    
    # Check if the directory exists
    if folder != 'NOT SET':
        folder_path = Path(folder)
        exists = folder_path.exists()
        is_dir = folder_path.is_dir() if exists else False
        
        print(f"\nDirectory Check:")
        print(f"  Path: {folder_path}")
        print(f"  Exists: {exists}")
        print(f"  Is Directory: {is_dir}")
        
        # Check subdirectories
        if exists and is_dir:
            dynamicalsystem_dir = folder_path / "dynamicalsystem"
            config_dir = dynamicalsystem_dir / "config"
            
            print(f"\nSubdirectory Check:")
            print(f"  {dynamicalsystem_dir}: exists={dynamicalsystem_dir.exists()}, is_dir={dynamicalsystem_dir.is_dir()}")
            print(f"  {config_dir}: exists={config_dir.exists()}, is_dir={config_dir.is_dir()}")
            
            # List config files if directory exists
            if config_dir.exists() and config_dir.is_dir():
                config_files = list(config_dir.iterdir())
                print(f"\nConfig files in {config_dir}:")
                if config_files:
                    for file in sorted(config_files):
                        print(f"    {file.name}")
                else:
                    print("    (directory is empty)")
                    
                # Check for expected config files
                print(f"\nChecking for expected config files:")
                expected_files = ['pytest.env', 'halogen.pytest.env', 'gazette.pytest.env']
                for filename in expected_files:
                    file_path = config_dir / filename
                    print(f"    {filename}: {'exists' if file_path.exists() else 'NOT FOUND'}")
        
        # Assert the directory exists
        assert exists, f"Directory {folder_path} does not exist"
        assert is_dir, f"Path {folder_path} exists but is not a directory"
    else:
        assert False, "DYNAMICALSYSTEM_FOLDER environment variable is not set"
    
    # Also verify the environment variable is set correctly
    assert environment == 'pytest', f"DYNAMICALSYSTEM_ENVIRONMENT should be 'pytest' but is '{environment}'"