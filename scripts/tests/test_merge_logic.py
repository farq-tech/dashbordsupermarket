import pandas as pd
from scripts.scrape_products_prices_compare import compare_prices, _normalize_columns


def test_compare_prices_basic():
	# Products
	prod = pd.DataFrame([
		{"id": 1, "name": "P1", "categoryId": 10},
		{"id": 2, "name": "P2", "categoryId": 10},
	])
	prod = _normalize_columns(prod)

	# Prices (two stores for product 1, one for product 2)
	prices = pd.DataFrame([
		{"productId": 1, "storeId": 7, "price": 12.5},
		{"productId": 1, "storeId": 9, "price": 10.0},
		{"productId": 2, "storeId": 7, "price": 8.0},
	])
	prices = _normalize_columns(prices)

	merged, summary = compare_prices(prod, prices)

	# Product 1 lowest=10.0, highest=12.5, spread=2.5, stores=2
	row1 = summary[summary["product_id"] == 1].iloc[0]
	assert row1["lowest_price"] == 10.0
	assert row1["highest_price"] == 12.5
	assert round(row1["price_spread"], 2) == 2.5
	assert row1["stores_count"] == 2

	# Product 2 lowest=8.0, highest=8.0, spread=0.0, stores=1
	row2 = summary[summary["product_id"] == 2].iloc[0]
	assert row2["lowest_price"] == 8.0
	assert row2["highest_price"] == 8.0
	assert round(row2["price_spread"], 2) == 0.0
	assert row2["stores_count"] == 1



