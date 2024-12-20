from fastapi import Depends, Query, HTTPException, APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
import asyncio
from functools import partial
import time
from app.db.db_check_order import get_db

router = APIRouter(
    prefix='/storehub',
    tags=['StoreHub']
)

async def execute_query_with_timeout(db: Session, query: text, params: dict, timeout: int = 5):
    # Convert synchronous database operation to run in a thread pool
    loop = asyncio.get_running_loop()
    try:
        async with asyncio.timeout(timeout):
            # Run database query in thread pool
            result = await loop.run_in_executor(
                None,
                partial(db.execute, query, params)
            )
            return result.fetchall()
    except asyncio.TimeoutError:
        # If timeout occurs, return None to trigger retry
        return None

async def retry_query(db: Session, query: text, params: dict, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            results = await execute_query_with_timeout(db, query, params)
            if results is not None:
                return results
            
            # If we get None result (timeout), wait before retry
            wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
            print(f"Attempt {attempt + 1} timed out. Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            if attempt == max_retries - 1:  # If this was the last attempt
                raise e
            
            wait_time = (attempt + 1) * 2
            print(f"Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    
    raise HTTPException(
        status_code=500,
        detail="Max retries reached while attempting to fetch inventory"
    )

@router.get("/inventory_check")
async def check_all_branches_inventory(
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
        
        # Use retry logic for query execution
        results = await retry_query(db, query, params)

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
                "quantity": result.quantityOnHand - 1,
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