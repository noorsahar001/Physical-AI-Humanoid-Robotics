#!/usr/bin/env python3
"""
CLI script for ingesting book content into the vector database.
Constitution v1.1.0: Standalone ingestion for Physical AI & Humanoid Robotics book.

Usage:
    python -m scripts.ingest [--docs-path PATH] [--force]

    Or from backend directory:
    python scripts/ingest.py [--docs-path PATH] [--force]
"""

import argparse
import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.embedding_service import get_embedding_service
from app.services.qdrant_service import get_qdrant_service
from app.services.ingestion_service import get_ingestion_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the ingestion CLI."""
    parser = argparse.ArgumentParser(
        description="Ingest book content into the Qdrant vector database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Ingest using default docs path from .env
    python -m scripts.ingest

    # Ingest from a specific directory
    python -m scripts.ingest --docs-path ../physical-ai-humanoid-robotics/docs

    # Force re-ingestion of all documents
    python -m scripts.ingest --force
        """,
    )
    parser.add_argument(
        "--docs-path",
        type=str,
        default=None,
        help=f"Path to the docs directory (default: {settings.DOCS_PATH})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion of all documents (ignores cache)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    docs_path = args.docs_path or settings.DOCS_PATH

    print("=" * 60)
    print("RAG Chatbot Content Ingestion")
    print("Constitution v1.1.0")
    print("=" * 60)
    print(f"\nDocs Path: {docs_path}")
    print(f"Force Re-ingest: {args.force}")
    print(f"Qdrant Collection: {settings.QDRANT_COLLECTION}")
    print()

    try:
        # Initialize services
        print("Initializing services...")
        embedding_service = get_embedding_service()
        print("  - Embedding service: OK")

        qdrant_service = get_qdrant_service()
        print("  - Qdrant service: OK")

        ingestion_service = get_ingestion_service(embedding_service, qdrant_service)
        print("  - Ingestion service: OK")
        print()

        # Discover documents first
        print("Discovering documents...")
        file_paths = ingestion_service.discover_documents(docs_path)
        print(f"  Found {len(file_paths)} documents")
        print()

        if not file_paths:
            print(f"ERROR: No documents found in {docs_path}")
            print("Make sure the docs directory exists and contains .md or .mdx files.")
            sys.exit(1)

        # Run ingestion
        print("Starting ingestion...")
        result = ingestion_service.ingest_documents(
            docs_path=docs_path,
            force_reingest=args.force,
        )

        # Print results
        print()
        print("=" * 60)
        print("INGESTION COMPLETE")
        print("=" * 60)
        print(f"Status: {result['status'].upper()}")
        print(f"Documents Processed: {result['documents_processed']}")
        print(f"Chunks Created: {result['chunks_created']}")

        if result['errors']:
            print(f"\nErrors ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"  - {error}")

        # Get collection stats
        print()
        print("Collection Status:")
        try:
            info = qdrant_service.get_collection_info()
            print(f"  Name: {info['name']}")
            print(f"  Vectors Count: {info['vectors_count']}")
            print(f"  Points Count: {info['points_count']}")
            print(f"  Status: {info['status']}")
        except Exception as e:
            print(f"  Error getting collection info: {e}")

        print()

        if result['status'] == 'success':
            print("Ingestion completed successfully!")
            sys.exit(0)
        elif result['status'] == 'partial':
            print("Ingestion completed with some errors.")
            sys.exit(1)
        else:
            print("Ingestion failed.")
            sys.exit(2)

    except KeyboardInterrupt:
        print("\nIngestion cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logger.exception("Ingestion failed with error")
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
