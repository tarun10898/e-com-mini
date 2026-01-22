import httpx
import sys

# Configuration
API_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "strongpassword123"

def print_step(message):
    print(f"\n--- {message} ---")

def test_flow():
    # 1. Register Admin
    print_step("1. Registering Admin User")
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "full_name": "Admin User",
        "role": "admin"
    }
    
    # Use httpx.Client instead of requests
    with httpx.Client() as client:
        response = client.post(f"{API_URL}/auth/register", json=payload)
        
        if response.status_code == 200:
            print("✅ Registered successfully")
        elif response.status_code == 400 and "already exists" in response.text:
            print("⚠️ User already exists (Skipping registration)")
        else:
            print(f"❌ Failed to register: {response.text}")
            sys.exit(1)

        # 2. Login
        print_step("2. Logging In")
        login_data = {
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        response = client.post(f"{API_URL}/auth/login", data=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.text}")
            sys.exit(1)
        
        token = response.json()["access_token"]
        print("✅ Login successful! Token acquired.")
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create Product
        print_step("3. Creating a Product (as Admin)")
        product_data = {
            "name": "Gaming Laptop",
            "description": "High performance laptop",
            "price": 1500.0,
            "stock": 10,
            "category": "Electronics"
        }
        response = client.post(f"{API_URL}/products/", json=product_data, headers=headers)
        if response.status_code == 200:
            print(f"✅ Product created: {response.json()['name']}")
        else:
            print(f"❌ Failed to create product: {response.text}")

        # 4. List Products
        print_step("4. Listing Products")
        response = client.get(f"{API_URL}/products/", headers=headers)
        products = response.json()
        print(f"✅ Found {len(products)} products in the catalog.")
        for p in products:
            print(f"   - {p['name']} (${p['price']})")

if __name__ == "__main__":
    try:
        test_flow()
    except httpx.ConnectError:
        print("\n❌ Could not connect to the server.")
        print("💡 Hint: Did you start the backend? Run 'uvicorn app.main:app --reload'")
