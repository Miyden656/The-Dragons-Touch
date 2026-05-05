# Terminal Test Commands

Run these from the folder that contains the `./` package.

## 1. Compile check

```bash
python -m compileall -q .
```

PowerShell:

```powershell
python -m compileall -q .
```

## 2. Smoke test

```bash
python tools/smoke_test_round8.py
```

PowerShell:

```powershell
python tools\smoke_test_round8.py
```

## 3. Run one real deck without file picker

PowerShell:

```powershell
$env:MTG_DECK_FILE="decklists\your_deck.txt"
python main.py
Remove-Item Env:\MTG_DECK_FILE
```

Bash:

```bash
MTG_DECK_FILE="decklists/your_deck.txt" python main.py
```

## 4. Force normal output mode

PowerShell:

```powershell
$env:MTG_DECK_FILE="decklists\your_deck.txt"
$env:MTG_OUTPUT_MODE="normal"
python main.py
Remove-Item Env:\MTG_DECK_FILE
Remove-Item Env:\MTG_OUTPUT_MODE
```

## 5. Force debug output mode

PowerShell:

```powershell
$env:MTG_DECK_FILE="decklists\your_deck.txt"
$env:MTG_OUTPUT_MODE="debug"
python main.py
Remove-Item Env:\MTG_DECK_FILE
Remove-Item Env:\MTG_OUTPUT_MODE
```

## 6. Force worksheet prompt mode

PowerShell:

```powershell
$env:MTG_DECK_FILE="decklists\your_deck.txt"
$env:MTG_PROMPT_INTERACTION_MODE="worksheet"
python main.py
Remove-Item Env:\MTG_DECK_FILE
Remove-Item Env:\MTG_PROMPT_INTERACTION_MODE
```
