#!/usr/bin/env python3
"""
Generate a test JWT token for development/testing purposes.

Usage:
    python3 scripts/generate_test_jwt.py
    python3 scripts/generate_test_jwt.py --secret "your-secret-key" --exp-days 7
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jose import jwt


def generate_test_token(
    secret_key: str = "dev-secret-key-for-testing-only-min-32-chars",
    algorithm: str = "HS256",
    exp_days: int = 7,
    user_id: str = "test-user",
    email: str = "test@example.com",
):
    """
    Generate a test JWT token.
    
    Args:
        secret_key: Secret key for signing (must match server config)
        algorithm: JWT algorithm (HS256, RS256, etc.)
        exp_days: Token expiration in days
        user_id: User ID (sub claim)
        email: User email
        
    Returns:
        str: JWT token string
    """
    # Ensure secret key is at least 32 characters
    if len(secret_key) < 32:
        print(f"Warning: Secret key is only {len(secret_key)} characters. Minimum is 32.")
        print("Using a longer default secret key for this token generation.")
        secret_key = "dev-secret-key-for-testing-only-min-32-chars"
    
    # Token payload
    now = datetime.utcnow()
    payload = {
        "sub": user_id,  # Subject (user ID)
        "email": email,
        "iat": int(now.timestamp()),  # Issued at
        "exp": int((now + timedelta(days=exp_days)).timestamp()),  # Expiration
        "type": "access",
    }
    
    # Token header
    headers = {
        "alg": algorithm,
        "typ": "JWT",
    }
    
    # Generate token
    token = jwt.encode(payload, secret_key, algorithm=algorithm, headers=headers)
    
    return token


def main():
    parser = argparse.ArgumentParser(description="Generate a test JWT token")
    parser.add_argument(
        "--secret",
        default="dev-secret-key-for-testing-only-min-32-chars",
        help="Secret key for signing (must match server JWT_SECRET_KEY)",
    )
    parser.add_argument(
        "--algorithm",
        default="HS256",
        choices=["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"],
        help="JWT algorithm",
    )
    parser.add_argument(
        "--exp-days",
        type=int,
        default=7,
        help="Token expiration in days (default: 7)",
    )
    parser.add_argument(
        "--user-id",
        default="test-user",
        help="User ID (sub claim)",
    )
    parser.add_argument(
        "--email",
        default="test@example.com",
        help="User email",
    )
    
    args = parser.parse_args()
    
    try:
        token = generate_test_token(
            secret_key=args.secret,
            algorithm=args.algorithm,
            exp_days=args.exp_days,
            user_id=args.user_id,
            email=args.email,
        )
        
        print("=" * 80)
        print("Test JWT Token Generated")
        print("=" * 80)
        print(f"\nToken:\n{token}\n")
        print("=" * 80)
        print("\nUsage Examples:")
        print("=" * 80)
        print("\n1. Using curl:")
        print(f'   curl -X POST http://localhost:8000/mcp \\')
        print(f'     -H "Content-Type: application/json" \\')
        print(f'     -H "Authorization: Bearer {token[:50]}..." \\')
        print(f'     -d \'{{"jsonrpc": "2.0", "method": "tools/list", "id": 1}}\'')
        
        print("\n2. Using Python requests:")
        print(f'   import requests')
        print(f'   headers = {{"Authorization": "Bearer {token[:50]}..."}}')
        print(f'   response = requests.post("http://localhost:8000/mcp", headers=headers, json={{"jsonrpc": "2.0", "method": "tools/list", "id": 1}})')
        
        print("\n3. Using JavaScript fetch:")
        print(f'   fetch("http://localhost:8000/mcp", {{')
        print(f'     method: "POST",')
        print(f'     headers: {{')
        print(f'       "Content-Type": "application/json",')
        print(f'       "Authorization": "Bearer {token[:50]}..."')
        print(f'     }},')
        print(f'     body: JSON.stringify({{"jsonrpc": "2.0", "method": "tools/list", "id": 1}})')
        print(f'   }})')
        
        print("\n" + "=" * 80)
        print(f"\nNote: Make sure JWT_SECRET_KEY in your config matches: {args.secret[:30]}...")
        print(f"Token expires in {args.exp_days} days")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error generating token: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
