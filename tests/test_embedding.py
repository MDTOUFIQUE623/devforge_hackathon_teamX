"""
Test file for Embedder module.
Run this script to verify that sentence embeddings are generated correctly.
"""

import sys
from pathlib import Path

# Add project root to Python path so we can import from src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.embedding.embedder import Embedder

def main():
    # Initialize embedder
    embedder = Embedder()

    # Sample text blocks
    sample_texts = [
        "Alice is a software engineer at DevForge.",
        "Bob is the CTO of DevForge and oversees all tech decisions.",
        "The company, DevForge, is located in Bangalore."
    ]

    # Generate embeddings
    embeddings = embedder.encode_texts(sample_texts)

    # Print the shape and first 5 values of each embedding
    for idx, emb in enumerate(embeddings):
        print(f"Text {idx+1}: {sample_texts[idx]}")
        print(f"Embedding length: {len(emb)}")
        print(f"First 5 values: {emb[:5]}")
        print("-" * 50)

    # Test single text embedding
    single_emb = embedder.encode_text("Alice works on AI projects.")
    print("Single text embedding length:", len(single_emb))
    print("First 5 values:", single_emb[:5])


if __name__ == "__main__":
    main()
