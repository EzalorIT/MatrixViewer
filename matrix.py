import pandas as pd
import os

# === Step 1: Load CSV ===
csv_path = "../output/combined_output.csv"  # Replace with your actual path
df = pd.read_csv(csv_path)

# === Step 2: Validate Columns ===
if not {"Username", "Name"}.issubset(df.columns):
    raise ValueError("Input must have at least 'Username' and 'Name' columns")

# === Step 3: Create Yes/No Pivot ===
pivot = pd.crosstab(df["Username"], df["Name"])
matrix = pivot.applymap(lambda x: "Yes" if x > 0 else "No")

# === Step 4: Save Full Matrix ===
output_path = "user_app_presence_matrix.csv"
matrix.to_csv(output_path)
print(f"✅ Full matrix saved to: {output_path}")

# === Optional Step 5: Chunk for Viewing (e.g., 50 columns per chunk) ===
CHUNK_SIZE = 50
chunk_dir = "matrix_chunks"
os.makedirs(chunk_dir, exist_ok=True)

total_cols = len(matrix.columns)
for i in range(0, total_cols, CHUNK_SIZE):
    chunk = matrix.iloc[:, i:i+CHUNK_SIZE]
    chunk_path = os.path.join(chunk_dir, f"matrix_chunk_{i//CHUNK_SIZE + 1}.csv")
    chunk.to_csv(chunk_path)
    print(f"🔹 Chunk saved: {chunk_path}")
