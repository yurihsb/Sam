import json

encodings = ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "latin-1", "cp1252"]

for enc in encodings:
    try:
        with open("backup.json", "r", encoding=enc) as f:
            data = json.load(f)
        with open("backup_recuperado.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"SUCESSO! Codificacao identificada: {enc}")
        break
    except Exception as e:
        continue

