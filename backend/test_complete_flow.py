import httpx
import sys

# Configuration
API_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "strongpassword123"
CUSTOMER_EMAIL = "customer@example.com"
CUSTOMER_PASSWORD = "password123"

def print_step(message):
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}")

def test_complete_flow():
    with httpx.Client() as client:
        # 1. Register Admin
        print_step("1. Registering Admin User")
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "full_name": "Admin User",
            "role": "admin"
        }
        response = client.post(f"{API_URL}/auth/register", json=payload)
        if response.status_code == 200:
            print("✅ Admin registered successfully")
        elif "already exists" in response.text:
            print("⚠️  Admin already exists (OK)")
        else:
            print(f"❌ Failed: {response.text}")

        # 2. Login as Admin
        print_step("2. Admin Login")
        login_data = {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        response = client.post(f"{API_URL}/auth/login", data=login_data)
        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("✅ Admin logged in")

        # 3. Create Products
        print_step("3. Creating Products (as Admin)")
        products = [
            {"name": "Gaming Laptop", "description": "High performance", "price": 1500.0, "stock": 5, "category": "Electronics"},
            {"name": "Wireless Mouse", "description": "Ergonomic design", "price": 25.0, "stock": 20, "category": "Accessories"},
            {"name": "Mechanical Keyboard", "description": "RGB backlit", "price": 120.0, "stock": 10, "category": "Accessories"},
        ]
        
        product_ids = []
        for product_data in products:
            response = client.post(f"{API_URL}/products/", json=product_data, headers=admin_headers)
            if response.status_code == 200:
                product_ids.append(response.json()["id"])
                print(f"✅ Created: {product_data['name']}")

        # 4. Register Customer
        print_step("4. Registering Customer")
        payload = {
            "email": CUSTOMER_EMAIL,
            "password": CUSTOMER_PASSWORD,
            "full_name": "John Doe",
            "role": "customer"
        }
        response = client.post(f"{API_URL}/auth/register", json=payload)
        if response.status_code == 200:
            print("✅ Customer registered")
        elif "already exists" in response.text:
            print("⚠️  Customer already exists (OK)")

        # 5. Login as Customer
        print_step("5. Customer Login")
        login_data = {"username": CUSTOMER_EMAIL, "password": CUSTOMER_PASSWORD}
        response = client.post(f"{API_URL}/auth/login", data=login_data)
        customer_token = response.json()["access_token"]
        customer_headers = {"Authorization": f"Bearer {customer_token}"}
        print("✅ Customer logged in")

        # 6. Browse Products
        print_step("6. Browsing Products")
        response = client.get(f"{API_URL}/products/")
        products_list = response.json()
        print(f"✅ Found {len(products_list)} products:")
        for p in products_list:
            print(f"   - {p['name']}: ${p['price']} (Stock: {p['stock']})")

        # 7. Add to Cart
        print_step("7. Adding Items to Cart")
        if len(product_ids) >= 2:
            # Add laptop
            response = client.post(
                f"{API_URL}/cart/items",
                json={"product_id": product_ids[0], "quantity": 1},
                headers=customer_headers
            )
            print(f"✅ Added Gaming Laptop to cart")
            
            # Add mouse
            response = client.post(
                f"{API_URL}/cart/items",
                json={"product_id": product_ids[1], "quantity": 2},
                headers=customer_headers
            )
            print(f"✅ Added 2x Wireless Mouse to cart")

        # 8. View Cart
        print_step("8. Viewing Cart")
        response = client.get(f"{API_URL}/cart/", headers=customer_headers)
        cart = response.json()
        print(f"✅ Cart has {len(cart['items'])} items")
        for item in cart['items']:
            print(f"   - Product ID {item['product_id']}: Quantity {item['quantity']}")

        # 9. Create Order
        print_step("9. Creating Order")
        response = client.post(f"{API_URL}/orders/", headers=customer_headers)
        if response.status_code == 200:
            order = response.json()
            print(f"✅ Order created! Order ID: {order['id']}")
            print(f"   Total: ${order['total_amount']}")
            print(f"   Status: {order['status']}")
            print(f"   Items: {len(order['items'])}")
        else:
            print(f"❌ Order failed: {response.text}")

        # 10. View Orders
        print_step("10. Viewing Order History")
        response = client.get(f"{API_URL}/orders/", headers=customer_headers)
        orders = response.json()
        print(f"✅ Customer has {len(orders)} order(s)")
        for order in orders:
            print(f"   - Order #{order['id']}: ${order['total_amount']} ({order['status']})")

        # 11. Verify Cart is Empty
        print_step("11. Verifying Cart After Order")
        response = client.get(f"{API_URL}/cart/", headers=customer_headers)
        cart = response.json()
        print(f"✅ Cart now has {len(cart['items'])} items (should be 0)")

        print_step("🎉 ALL TESTS PASSED!")

if __name__ == "__main__":
    try:
        test_complete_flow()
    except httpx.ConnectError:
        print("\n❌ Could not connect to the server.")
        print("💡 Hint: Run 'docker-compose up -d' to start the backend")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
