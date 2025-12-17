#!/usr/bin/env python3
"""
Auto-chunker script for the RAG Chatbot.

This script scans the Docusaurus /docs folder, extracts content from .md files,
chunks the content into 300-500 token pieces, generates embeddings, and stores
them in Qdrant and metadata in Postgres.

Usage:
    python auto-chunker.py [--docs-path PATH] [--backend-url URL]
"""

import os
import re
import sys
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import json


def estimate_tokens(text: str) -> int:
    """Estimate token count (roughly 4 characters per token for English)."""
    return len(text) // 4


def clean_md_content(content: str) -> str:
    """
    Clean MDX content by removing JSX components, imports, and formatting.
    """
    # Remove import statements
    content = re.sub(r'^import\s+.*$', '', content, flags=re.MULTILINE)

    # Remove export statements
    content = re.sub(r'^export\s+.*$', '', content, flags=re.MULTILINE)

    # Remove JSX self-closing tags like <Component />
    content = re.sub(r'<[A-Z][a-zA-Z]*\s*[^>]*/>', '', content)

    # Remove JSX opening/closing tags
    content = re.sub(r'<[A-Z][a-zA-Z]*[^>]*>.*?</[A-Z][a-zA-Z]*>', '', content, flags=re.DOTALL)

    # Remove frontmatter (between --- markers at the start)
    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

    # Remove code blocks but keep their content description
    content = re.sub(r'```[^\n]*\n(.*?)```', r'\1', content, flags=re.DOTALL)

    # Remove inline code backticks
    content = re.sub(r'`([^`]+)`', r'\1', content)

    # Remove HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

    # Remove markdown image syntax but keep alt text
    content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', content)

    # Remove markdown links but keep text
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

    # Remove extra whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


def extract_title(content: str, filepath: Path) -> str:
    """Extract the title from MD content or use the filename."""
    # Try to find # Title at the beginning
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()

    # Try to find title in frontmatter
    frontmatter_match = re.search(r'^---\s*\n.*?title:\s*["\']?([^"\'\n]+)["\']?.*?\n---', content, flags=re.DOTALL)
    if frontmatter_match:
        return frontmatter_match.group(1).strip()

    # Use filename as fallback
    return filepath.stem.replace('-', ' ').replace('_', ' ').title()


def chunk_text(text: str, min_tokens: int = 300, max_tokens: int = 500) -> List[str]:
    """
    Split text into chunks of approximately min_tokens to max_tokens.
    Tries to split on paragraph boundaries.
    """
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        potential_chunk = current_chunk + ("\n\n" if current_chunk else "") + para
        tokens = estimate_tokens(potential_chunk)

        if tokens > max_tokens and current_chunk:
            # Current chunk is good, start new one
            chunks.append(current_chunk.strip())
            current_chunk = para
        elif tokens > max_tokens:
            # Single paragraph is too long, split by sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                potential = current_chunk + (" " if current_chunk else "") + sentence
                if estimate_tokens(potential) > max_tokens and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk = potential
        else:
            current_chunk = potential_chunk

    # Don't forget the last chunk
    if current_chunk:
        # If it's too small, append to previous chunk
        if chunks and estimate_tokens(current_chunk) < min_tokens:
            chunks[-1] = chunks[-1] + "\n\n" + current_chunk
        else:
            chunks.append(current_chunk.strip())

    return chunks


def scan_md_files(docs_path: Path) -> List[Dict[str, Any]]:
    """
    Scan directory for .md files and extract content.
    """
    documents = []

    for md_file in docs_path.rglob('*.md'):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            title = extract_title(content, md_file)
            cleaned_content = clean_md_content(content)

            if len(cleaned_content) < 100:
                print(f"  Skipping {md_file.name} - too short after cleaning")
                continue

            # Generate source URL (relative path)
            relative_path = md_file.relative_to(docs_path)
            source_url = f"/docs/{str(relative_path).replace('.md', '').replace(os.sep, '/')}"

            documents.append({
                'filepath': str(md_file),
                'title': title,
                'content': cleaned_content,
                'source': source_url,
            })

            print(f"  Found: {title} ({len(cleaned_content)} chars)")

        except Exception as e:
            print(f"  Error reading {md_file}: {e}")

    return documents


def embed_chunk(backend_url: str, chunk: str, source: str, title: str, chunk_id: str) -> bool:
    """Send a chunk to the backend for embedding."""
    try:
        response = requests.post(
            f"{backend_url}/api/chatbot/embed",
            json={
                "text": chunk,
                "source": source,
                "page_title": title,
                "chunk_id": chunk_id,
            },
            timeout=30,
        )
        return response.status_code == 200
    except Exception as e:
        print(f"    Error embedding chunk: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Auto-chunker for RAG Chatbot')
    parser.add_argument(
        '--docs-path',
        type=str,
        default='../physical-ai-humanoid-robotics/docs',
        help='Path to the Docusaurus docs folder'
    )
    parser.add_argument(
        '--backend-url',
        type=str,
        default='http://localhost:8000',
        help='Backend API URL'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only scan and chunk, do not embed'
    )
    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    docs_path = Path(args.docs_path)
    if not docs_path.is_absolute():
        docs_path = (script_dir / docs_path).resolve()

    print(f"RAG Chatbot Auto-Chunker")
    print(f"========================")
    print(f"Docs path: {docs_path}")
    print(f"Backend URL: {args.backend_url}")
    print(f"Dry run: {args.dry_run}")
    print()

    if not docs_path.exists():
        print(f"Error: Docs path does not exist: {docs_path}")
        sys.exit(1)

    # Scan for MD files
    print("Scanning for MD files...")
    documents = scan_md_files(docs_path)
    print(f"\nFound {len(documents)} documents")
    print()

    # Process each document
    total_chunks = 0
    successful_embeds = 0

    for doc in documents:
        print(f"Processing: {doc['title']}")

        # Chunk the content
        chunks = chunk_text(doc['content'])
        print(f"  Created {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc['source'].replace('/', '_')}_{i}"
            tokens = estimate_tokens(chunk)
            print(f"    Chunk {i+1}: {tokens} tokens")

            if not args.dry_run:
                success = embed_chunk(
                    args.backend_url,
                    chunk,
                    doc['source'],
                    doc['title'],
                    chunk_id,
                )
                if success:
                    successful_embeds += 1
                    print(f"    ✓ Embedded")
                else:
                    print(f"    ✗ Failed to embed")

            total_chunks += 1

        print()

    # Summary
    print("=" * 40)
    print("Summary")
    print("=" * 40)
    print(f"Documents processed: {len(documents)}")
    print(f"Total chunks created: {total_chunks}")
    if not args.dry_run:
        print(f"Successfully embedded: {successful_embeds}")
        print(f"Failed: {total_chunks - successful_embeds}")
    print()

    if args.dry_run:
        print("Dry run complete. No data was sent to the backend.")
    else:
        print("Chunking and embedding complete!")


if __name__ == '__main__':
    main()
