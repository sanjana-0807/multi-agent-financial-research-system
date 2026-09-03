import os

print("\n========== WALMART DOCUMENT INSPECTION ==========")

search_root = "documents"

if not os.path.exists(search_root):
    print("Documents directory not found.")
else:

    for root, dirs, files in os.walk(search_root):

        for file in files:

            if "walmart" in file.lower():

                path = os.path.join(root, file)

                print("\nFOUND:", path)

                try:
                    print(
                        "Size:",
                        os.path.getsize(path),
                        "bytes"
                    )
                except Exception as e:
                    print("ERROR:", e)