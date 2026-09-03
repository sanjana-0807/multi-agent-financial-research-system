import os

DOCUMENTS_DIR = "documents"

print("\n========== RAW DOCUMENT INSPECTION ==========")

if not os.path.exists(DOCUMENTS_DIR):
    print("Documents directory not found.")
else:
    for root, dirs, files in os.walk(DOCUMENTS_DIR):

        print("\nDirectory:", root)

        for file in files:
            path = os.path.join(root, file)

            try:
                size = os.path.getsize(path)
                print(f"{file} | {size} bytes")
            except Exception as e:
                print(file, "| ERROR:", e)