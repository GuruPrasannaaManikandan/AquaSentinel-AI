import os
import hashlib
import tarfile
import pandas as pd

def compute_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def setup_workspace(analysis_root):
    dirs = [
        "config",
        "notebooks",
        "scripts",
        "src/parsing",
        "src/analysis",
        "src/visualization",
        "src/matching",
        "data/interim",
        "data/processed",
        "reports",
        "figures/cdom",
        "figures/hplc",
        "metadata",
        "tests"
    ]
    for d in dirs:
        path = os.path.join(analysis_root, d)
        os.makedirs(path, exist_ok=True)
        print(f"Created directory: {path}")

def main():
    project_root = r"P:\5th semester\Embedded Systems\Capstone Project"
    dataset_root = os.path.join(project_root, "New Datasets", "requested_files", "WHOI", "SOSIK", "NES-LTER", "AE2426")
    analysis_root = os.path.join(project_root, "New Datasets", "AE2426_Analysis")
    
    # 1. Setup folders
    setup_workspace(analysis_root)
    
    # 2. Audit original files
    print("\nAuditing original files...")
    original_files = []
    
    # Check if directories exist
    archive_dir = os.path.join(dataset_root, "archive")
    documents_tgz = os.path.join(dataset_root, "documents.tgz")
    
    if not os.path.exists(archive_dir):
        print(f"Error: Archive directory does not exist: {archive_dir}")
        return
        
    if not os.path.exists(documents_tgz):
        print(f"Error: Documents archive does not exist: {documents_tgz}")
        return

    # List CDOM and HPLC files
    for root, _, files in os.walk(dataset_root):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, dataset_root)
            size = os.path.getsize(full_path)
            checksum = compute_sha256(full_path)
            ext = os.path.splitext(file)[1]
            original_files.append({
                "Filename": file,
                "RelativePath": rel_path,
                "Size_Bytes": size,
                "SHA256": checksum,
                "Extension": ext
            })
            print(f"Audited: {rel_path} ({size} bytes) - SHA256: {checksum[:8]}...")
            
    df_files = pd.DataFrame(original_files)
    df_files.to_csv(os.path.join(analysis_root, "metadata", "file_inventory.csv"), index=False)
    print(f"\nSaved original file inventory to {os.path.join(analysis_root, 'metadata', 'file_inventory.csv')}")

    # 3. Extract documents.tgz to data/interim/documents/
    extract_dest = os.path.join(analysis_root, "data", "interim", "documents")
    os.makedirs(extract_dest, exist_ok=True)
    print(f"\nExtracting documents.tgz to {extract_dest}...")
    
    with tarfile.open(documents_tgz, "r:gz") as tar:
        tar.extractall(path=extract_dest)
        members = tar.getnames()
        print(f"Successfully extracted {len(members)} items from documents.tgz:")
        for member in members:
            member_path = os.path.join(extract_dest, member)
            if os.path.isfile(member_path):
                print(f" - {member} ({os.path.getsize(member_path)} bytes)")
            else:
                print(f" - [Dir] {member}")

    # Create README.md
    readme_content = """# AE2426 Dataset Scientific and Forensic Analysis Workspace

This directory is an isolated analysis workspace for evaluating the AE2426 CDOM and HPLC datasets.

## Structure
- `config/`: Configurations
- `notebooks/`: Exploratory Jupyter notebooks
- `scripts/`: Python utility execution scripts
- `src/`: Reusable packages for parsing, analysis, visualization, and sample matching
- `data/`: Extracted documentation and clean CSV datasets
- `reports/`: Scientific reports (Reports 01 - 12)
- `figures/`: Scientific visualization plots (CDOM and HPLC)
- `metadata/`: Inventories and variable dictionaries
- `tests/`: Unit tests for data matching, parsing, and integration

*Note: The original dataset in `New Datasets/requested_files` remains untouched.*
"""
    with open(os.path.join(analysis_root, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("Created README.md")

if __name__ == "__main__":
    main()
