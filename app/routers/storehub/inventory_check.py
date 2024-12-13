from fastapi import Depends, Query, HTTPException, APIRouter #type: ignore
from sqlalchemy import text #type: ignore
from sqlalchemy.orm import Session #type: ignore
from typing import Optional
from app.db.db_check_order import get_db

router = APIRouter(
    prefix='/storehub',
    tags=['StoreHub']
)

@router.get("/inventory_check")
def check_all_branches_inventory(
    sku: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    if sku:
        sku_list = sku.split(",")
    else:
        sku_list = []

    print("Received SKU list:", sku_list)

    try:
        like_conditions = " OR ".join([f"p.barcode LIKE :barcode{i}" for i in range(len(sku_list))])
        query = text(f"""
            SELECT 
                p.barcode,
                p.sku,
                p.product_name,
                p.inventory_name, 
                p."quantityOnHand",  
                p."warningStock",
                p."unitPrice",
                p.cost,
                p."trackStockLevel"
            FROM 
                product_stock p
            WHERE 
                ({like_conditions}) 
                AND p."quantityOnHand" > 1
            ORDER BY 
                p.barcode
        """)

        params = {f'barcode{i}': sku_item for i, sku_item in enumerate(sku_list)}
        results = db.execute(query, params).fetchall()

        if not results:
            raise HTTPException(
                status_code=404, 
                detail="No products found for the given filters"
            )

        inventory_by_barcode = {}
        for result in results:
            barcode = result.barcode

            if barcode not in inventory_by_barcode:
                inventory_by_barcode[barcode] = {
                    "barcode": barcode,
                    "sku": result.sku,
                    "product_name": result.product_name,
                    "unit_price": float(result.unitPrice) if result.unitPrice is not None else 0.0,
                    "warning_stock_level": float(result.warningStock) if result.warningStock is not None else 0.0,
                    "cost": float(result.cost) if result.cost is not None else 0.0,
                    "track_stock_level": result.trackStockLevel,
                    "branches": []
                }

            inventory_by_barcode[barcode]["branches"].append({
                "branch_name": result.inventory_name,
                "quantity": result.quantityOnHand,
                "has_stock": result.quantityOnHand > 1
            })

        inventory = list(inventory_by_barcode.values())

        return {
            "inventory": inventory
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while fetching inventory: {str(e)}"
        )
