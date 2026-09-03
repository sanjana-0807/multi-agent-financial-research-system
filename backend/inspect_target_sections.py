import os

print("\n========== TARGET SECTIONS ==========")

search_root = "documents"

keywords = [
    "target",
    "revenue",
    "net sales",
    "operating income",
    "net income",
    "cash flow",
    "earnings per share",
]

if not os.path.exists(search_root):
    print("Documents directory not found.")
else:

    for root, dirs, files in os.walk(search_root):

        for file in files:

            path = os.path.join(root, file)

            try:
                with open(
                    path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as f:
                    text = f.read()

                if "target" in text.lower():

                    print("\nFILE:", path)

                    for keyword in keywords:

                        if keyword in text.lower():
                            print("FOUND:", keyword)

            except Exception:
                pass