import os
import re
import pkg_resources

def extract_imports(file_path):
    """Extract imported library names from a Python file."""
    imports = set()
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Match simple import statements, this does not cover all cases
            match = re.match(r'^(?:import|from)\s+(\S+)', line)
            if match:
                imports.add(match.group(1).split('.')[0])  # Take top-level package name
    return imports

def get_installed_packages():
    """Get a dict of installed packages and their versions."""
    return {pkg.key: pkg.version for pkg in pkg_resources.working_set}

def generate_requirements(directory):
    all_imports = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                all_imports |= extract_imports(os.path.join(root, file))

    installed_packages = get_installed_packages()
    with open('requirements.txt', 'w', encoding='utf-8') as req_file:
        for import_name in all_imports:
            if import_name in installed_packages:
                req_file.write(f"{import_name}=={installed_packages[import_name]}\n")

generate_requirements('/Users/ismadoukkali/Desktop/altadex-amazongpt')
