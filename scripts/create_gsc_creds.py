#!/usr/bin/env python
"""
Create GSC service account JSON file from environment variables.

This script reads GSC_CLIENT_EMAIL and GSC_PRIVATE_KEY from environment
or command line arguments and creates a service account JSON file.
"""
import sys
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def create_service_account_json(
    client_email: str,
    private_key: str,
    output_path: str = "gsc-service-account.json"
) -> None:
    """
    Create a Google service account JSON file.

    Args:
        client_email: Service account email
        private_key: Private key (can be single-line with \\n or multi-line)
        output_path: Where to save the JSON file
    """
    # Convert single-line private key to multi-line format
    if "\\n" in private_key:
        private_key = private_key.replace("\\n", "\n")

    # Extract client_id from email (format: xxx@project-id.iam.gserviceaccount.com)
    project_id = client_email.split("@")[1].split(".")[0]
    client_id = client_email.split("@")[0]

    # Create service account info
    service_account = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": "generated-by-script",
        "private_key": private_key,
        "client_email": client_email,
        "client_id": client_id,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email}",
    }

    # Write to file
    output_file = Path(output_path)
    output_file.write_text(json.dumps(service_account, indent=2), encoding="utf-8")

    print(f"✓ Service account JSON created: {output_file}")
    print(f"  Client email: {client_email}")
    print(f"  Project ID: {project_id}")
    print(f"\nNow add this to your .env file:")
    print(f'GSC_SERVICE_ACCOUNT_PATH={output_file.absolute()}')


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Create GSC service account JSON from environment variables"
    )
    parser.add_argument(
        "--client-email",
        help="GSC client email (or set GSC_CLIENT_EMAIL env var)",
        default=os.getenv("GSC_CLIENT_EMAIL"),
    )
    parser.add_argument(
        "--private-key",
        help="GSC private key (or set GSC_PRIVATE_KEY env var)",
        default=os.getenv("GSC_PRIVATE_KEY"),
    )
    parser.add_argument(
        "--output",
        default="gsc-service-account.json",
        help="Output JSON file path (default: gsc-service-account.json)",
    )

    args = parser.parse_args()

    if not args.client_email or not args.private_key:
        print("✗ Error: Both --client-email and --private-key are required")
        print("\nYou can either:")
        print("  1. Pass them as arguments:")
        print("     python create_gsc_creds.py --client-email 'xxx@xxx.iam.gserviceaccount.com' --private-key '...' --output credentials/gsc.json")
        print("\n  2. Or set environment variables:")
        print("     export GSC_CLIENT_EMAIL='xxx@xxx.iam.gserviceaccount.com'")
        print("     export GSC_PRIVATE_KEY='-----BEGIN PRIVATE KEY-----\\n...'")
        print("     python create_gsc_creds.py")
        return 1

    try:
        create_service_account_json(
            client_email=args.client_email,
            private_key=args.private_key,
            output_path=args.output,
        )
        return 0
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
