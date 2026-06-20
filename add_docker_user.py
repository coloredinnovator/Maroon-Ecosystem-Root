import os
import glob

root_dir = r"C:\Users\maroon\.gemini\antigravity-ide\scratch\Maroon-Ecosystem-Root"
dockerfiles = glob.glob(os.path.join(root_dir, "*", "Dockerfile"))

for df_path in dockerfiles:
    with open(df_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Check if USER is already defined
    if any(line.strip().startswith("USER ") for line in lines):
        print(f"Already has USER: {df_path}")
        continue
    
    # Find where to insert (before CMD or ENTRYPOINT or at end)
    insert_idx = len(lines)
    for i, line in enumerate(lines):
        if line.strip().startswith("CMD ") or line.strip().startswith("ENTRYPOINT "):
            insert_idx = i
            break
            
    # Insert USER nobody
    lines.insert(insert_idx, "USER nobody\n")
    
    with open(df_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Added USER nobody to {df_path}")
