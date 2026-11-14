# azure-rag-assistant
Azure Rag Assistant demo project


## Getting the sample data

The documents are not stored in this repo. To download them:

```powershell
python scripts/download_data.py
```

This reads `data/sources.json` and saves the files to `data/raw/`
(which is git-ignored). Source URLs and licenses are listed in that file.

If a download fails, fetch the file manually from the URL in
`sources.json` and place it in `data/raw/`.

$RG    = "rg-rag-assistant"
$LOC   = "eastus"          # pick a region and stick with it; see the note in step 2
$SUFFIX = 59630
$STORAGE = "ragstore$SUFFIX"      # lowercase letters/numbers only, globally unique
$SEARCH  = "rag-search-$SUFFIX"   # lowercase letters, numbers, hyphens, globally unique
$AI_Name = "rg-rag-assistant-resource"