"""Helper functions for the agent to trigger MCP App UI components."""
import json
import os

BACKEND_PUBLIC_URL = os.environ.get("BACKEND_PUBLIC_URL", "http://127.0.0.1:8000")

def trigger_checkout_app(car_id: str, car_name: str, price: float, intent: str, session_id: str | None = None) -> str:
    query = f"car_id={car_id}"
    if session_id:
        query += f"&session_id={session_id}"
        
    payload = {
        "type": "mcp_app_render",
        "app_name": "CheckoutFlow",
        "data": {
            "title": f"Reserve {car_name}",
            "amount": price,
            "submit_endpoint": f"{BACKEND_PUBLIC_URL}/api/checkout/confirm?{query}",
            "form_fields": [
                {"id": "name", "label": "Full name", "type": "text", "required": True},
                {"id": "email", "label": "Email", "type": "email", "required": True},
                {"id": "phone", "label": "Phone", "type": "tel", "required": True},
                {"id": "card_number", "label": "Card Number", "type": "text", "required": True, "placeholder": "1234 5678 9876 5432"},
            ],
            "payment_mock": {
                "disclaimer": "This is a fully mocked payment - no real charge will be made.",
                "methods": ["Credit Card", "UPI", "Net Banking"],
            },
        },
    }
    return json.dumps(payload)