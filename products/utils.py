"""
Utility functions for product-related calculations.
Feature 6.2: Fair Price Calculator for Direct-to-Consumer sales.
"""
from decimal import Decimal, ROUND_HALF_UP

# 30% sustainability margin to ensure farmer profitability
SUSTAINABILITY_MARGIN = Decimal('0.30')


def calculate_fair_price(farmgate_price, transport_cost, quantity_kg):
    """
    Calculate fair selling price for direct-to-consumer agricultural sales.
    
    This calculation accounts for the fact that in direct-to-consumer models,
    the farmer (or buyer) pays for logistics to cut out the middleman.
    
    Args:
        farmgate_price (Decimal): Base price at the farm gate (per kg)
        transport_cost (Decimal): Total transport/gas cost for the shipment
        quantity_kg (Decimal): Total quantity being transported (in kg)
    
    Returns:
        dict: Contains calculated values:
            - fair_price: Final recommended selling price per unit
            - unit_logistics: Cost to transport 1kg
            - base_cost: Break-even point (farmgate + logistics)
            - profit_margin: The 30% sustainability margin amount
            - farmgate_price: Original farmgate price (for reference)
    
    Calculation Logic:
        1. Unit Logistics = Transport Cost / Quantity
        2. Base Cost = Farmgate Price + Unit Logistics (break-even)
        3. Fair Price = Base Cost + (Base Cost * 30%) (sustainability margin)
    """
    # Ensure all inputs are Decimal for precision
    farmgate_price = Decimal(str(farmgate_price))
    transport_cost = Decimal(str(transport_cost))
    quantity_kg = Decimal(str(quantity_kg))
    
    # Prevent division by zero
    if quantity_kg <= 0:
        raise ValueError("Quantity must be greater than zero")
    
    # Step 1: Calculate unit logistics cost
    unit_logistics = transport_cost / quantity_kg
    
    # Step 2: Calculate base cost (break-even point)
    base_cost = farmgate_price + unit_logistics
    
    # Step 3: Apply sustainability margin
    profit_amount = base_cost * SUSTAINABILITY_MARGIN
    fair_price = base_cost + profit_amount
    
    # Round to 2 decimal places for currency
    two_places = Decimal('0.01')
    
    return {
        'fair_price': fair_price.quantize(two_places, rounding=ROUND_HALF_UP),
        'unit_logistics': unit_logistics.quantize(two_places, rounding=ROUND_HALF_UP),
        'base_cost': base_cost.quantize(two_places, rounding=ROUND_HALF_UP),
        'profit_margin': profit_amount.quantize(two_places, rounding=ROUND_HALF_UP),
        'farmgate_price': farmgate_price.quantize(two_places, rounding=ROUND_HALF_UP),
    }


def calculate_buyer_savings(fair_price, supermarket_price):
    """
    Calculate the percentage a buyer saves compared to supermarket prices.
    
    Args:
        fair_price (Decimal): Our calculated fair price
        supermarket_price (Decimal): Typical supermarket price for comparison
    
    Returns:
        Decimal: Savings percentage (e.g., 25.50 for 25.5% savings)
                 Returns 0 if fair_price >= supermarket_price
    """
    fair_price = Decimal(str(fair_price))
    supermarket_price = Decimal(str(supermarket_price))
    
    if supermarket_price <= 0 or fair_price >= supermarket_price:
        return Decimal('0')
    
    savings = ((supermarket_price - fair_price) / supermarket_price) * 100
    return savings.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

