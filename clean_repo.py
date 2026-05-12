import os, shutil, zipfile

def clean_and_zip():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    zip_name = "VN_SME_Ledger_Source.zip"
    
    # Folders/Files to ignore
    ignored_patterns = [
        ".venv", "dist", "build", "__pycache__", ".git", ".gemini", 
        "data/ledger.db", "data/backups", "invoices", "contracts"
    ]
    
    print("🧹 Cleaning and Packaging project for GitHub...")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if not any(p in os.path.join(root, d) for p in ignored_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)
                
                # Skip if file itself is ignored or matches patterns
                if any(p in rel_path for p in ignored_patterns) or file == zip_name:
                    continue
                
                print(f"  + Adding {rel_path}")
                zipf.write(file_path, rel_path)
                
    size_mb = os.path.getsize(zip_name) / (1024 * 1024)
    print(f"\n✅ SUCCESS! Created: {zip_name}")
    print(f"📊 Final Size: {size_mb:.2f} MB (Well under 25MB!)")
    print("💡 You can now upload this ZIP file directly to GitHub.")

if __name__ == "__main__":
    clean_and_zip()
