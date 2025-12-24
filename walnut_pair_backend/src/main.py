from src.business_layers.walnut_bl import WalnutBL
import sys
import os

def main():
    if len(sys.argv) < 3:
        print("Usage: python -m src.main <front_image> <back_image>")
        return

    front_path, back_path = sys.argv[1], sys.argv[2]
    if not os.path.exists(front_path) or not os.path.exists(back_path):
        print("File not found!")
        return

    bl = WalnutBL()
    front_emb, back_emb = bl.generate_pair_embedding(front_path, back_path)
    print(f"Front embedding length: {len(front_emb)}, Back embedding length: {len(back_emb)}")
    print(f"Cosine similarity between front and back: {bl.similarity(front_emb, back_emb):.4f}")

if __name__ == "__main__":
    main()
