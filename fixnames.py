import os
import json

ASSETS_DIR = "FishingGameAssets"
CONFIG_FILES = ["my_fishing_game_config.json", "fishing_game_config.json"]

# 1. Rename image files in FishingGameAssets/
renamed = {}
for fname in os.listdir(ASSETS_DIR):
    if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        new_fname = fname.replace("_", "-")
        if new_fname != fname:
            os.rename(os.path.join(ASSETS_DIR, fname), os.path.join(ASSETS_DIR, new_fname))
            print(f"Renamed: {fname} -> {new_fname}")
        renamed[os.path.splitext(fname)[0]] = os.path.splitext(new_fname)[0]

# 2. Update fish names in config files
for config_file in CONFIG_FILES:
    if not os.path.exists(config_file):
        continue
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    changed = False
    for fish in config.get("fish", []):
        old_name = fish["name"]
        new_name = old_name.replace("_", "-")
        if new_name != old_name:
            print(f"Updating fish name in {config_file}: {old_name} -> {new_name}")
            fish["name"] = new_name
            changed = True
    if changed:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f"Updated {config_file}")

print("Done. You should now update the database and README.md as well.")