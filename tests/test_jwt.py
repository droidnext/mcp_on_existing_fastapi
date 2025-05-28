from jose import jwt
import datetime

def create_test_token():
    """
    Generate a JWT token for testing purposes.
    This token will be valid for 30 minutes from creation.
    """
    payload = {
        "sub": "alice",
        "role": "admin",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
    return token

if __name__ == "__main__":
    # Generate and print a test token
    token = create_test_token()
    print("\nTest JWT Token:")
    print("-" * 50)
    print(token)
    print("-" * 50)
    print("\nUse this token in your Authorization header:")
    print(f"Authorization: Bearer {token}")
    print("\nNote: This token will expire in 30 minutes.") 