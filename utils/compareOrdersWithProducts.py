from fastapi import HTTPException
from utils.getAllOrder import getAllOrder
from utils.getProducts import getAllProducts


def compareOrdersWithAllProducts(access_token: str, start_date: str, end_date: str):
    """
    Compare Shopee orders with all products from StoreHub.
    """
    try:
        # Step 1: Fetch orders from Shopee
        orders_response = getAllOrder(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )

        if "order_details" not in orders_response or not isinstance(orders_response["order_details"], list):
            return {
                "message": "No order details found in the specified date range.",
                "matched_items": [],
                "unmatched_items": [],
            }

        order_details = orders_response["order_details"]

        # Step 2: Fetch all products from StoreHub
        storehub_products = getAllProducts()

        # Create a dictionary for quick SKU lookup
        product_sku_dict = {product["sku"]: product for product in storehub_products}

        # Step 3: Compare SKUs in orders with StoreHub SKUs
        matched_items = []
        unmatched_items = []

        for order in order_details:
            if "item_list" not in order or not isinstance(order["item_list"], list):
                continue

            for item in order["item_list"]:
                if "model_sku" not in item:
                    continue

                order_sku = item["model_sku"]

                if order_sku in product_sku_dict:
                    product = product_sku_dict[order_sku]
                    matched_items.append({
                        "order_sn": order.get("order_sn", "Unknown"),
                        "model_sku": order_sku,
                        "quantity_ordered": item.get("model_quantity_purchased", 0),
                        "product_name": product.get("name", "Unknown"),
                        "storehub_sku": product.get("sku", "Unknown"),
                    })
                else:
                    unmatched_items.append({
                        "order_sn": order.get("order_sn", "Unknown"),
                        "model_sku": order_sku,
                        "quantity_ordered": item.get("model_quantity_purchased", 0),
                    })

        return {
            "message": "Comparison complete.",
            "matched_items": matched_items,
            "unmatched_items": unmatched_items,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare orders: {str(e)}")
