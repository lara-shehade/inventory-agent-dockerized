from decimal import Decimal

from .models import Item


def check_stock(name):
    """Look up an item's quantity and unit price."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    return {
        "name": item.name,
        "quantity": item.quantity,
        "price": str(item.price),
    }


def list_items():
    """Return every item with its quantity and unit price."""
    items = Item.objects.all()
    return {
        "items": [
            {
                "name": item.name,
                "quantity": item.quantity,
                "price": str(item.price),
            }
            for item in items
        ]
    }


def add_item(name, quantity, price):
    """Create an item or add stock, and set its unit price."""
    price = Decimal(str(price))
    if price <= 0:
        return {
            "error": "A positive unit price is required. Ask the user for the price before adding this item."
        }
    item = Item.objects.filter(name__iexact=name).first()
    if item is not None:
        item.quantity += quantity
        item.price = price
        item.save()
        return {
            "name": item.name,
            "quantity": item.quantity,
            "price": str(item.price),
            "created": False,
        }
    item = Item.objects.create(name=name, quantity=quantity, price=price)
    return {
        "name": item.name,
        "quantity": item.quantity,
        "price": str(item.price),
        "created": True,
    }


def remove_stock(name, quantity):
    """Take a quantity out of stock."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    if quantity > item.quantity:
        return {
            "error": f"Cannot remove {quantity}. Only {item.quantity} in stock.",
            "name": item.name,
            "quantity": item.quantity,
        }
    item.quantity -= quantity
    item.save()
    return {"name": item.name, "quantity": item.quantity}


def delete_item(name):
    """Remove an item from the inventory entirely."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    item.delete()
    return {"deleted": name}


TOOL_DECLARATIONS = [
    {
        "type": "function",
        "name": "check_stock",
        "description": "Look up the current quantity and unit price of a single inventory item. Use this for stock questions and cost calculations.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "list_items",
        "description": "Return every item in the inventory with its quantity and unit price. Use this when the user asks what is in stock generally, or asks for a list, rather than about one specific item.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "add_item",
        "description": "Add stock and set its unit price. If the item does not exist it is created; if it already exists the quantity is added and its unit price is updated. Use this for restocking and for new deliveries.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to add. Must be positive.",
                },
                "price": {
                    "type": "number",
                    "minimum": 0.01,
                    "description": "The positive price of one unit, e.g. 2.50. Never guess this value; the user must provide it.",
                },
            },
            "required": ["name", "quantity", "price"],
        },
    },
    {
        "type": "function",
        "name": "remove_stock",
        "description": "Reduce the quantity of an existing item. Use this when items are sold, shipped or used. This does NOT delete the item; it only lowers the number.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to remove. Must be positive.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "delete_item",
        "description": "Permanently remove an item and its record from the inventory entirely. This is destructive. Only use it when the user clearly wants the item gone, not when they want to reduce its quantity.",
        "parameters": {
            "type": "object",
            "properties": {

                "name": {
                    "type": "string",
                    "description": "The name of the item to delete.",
                },
            },
            "required": ["name"],
        },
    },
]

TOOL_FUNCTIONS = {
    "check_stock": check_stock,
    "list_items": list_items,
    "add_item": add_item,
    "remove_stock": remove_stock,
    "delete_item": delete_item,
}
