import { useState, useEffect } from 'react';
import { fustogApi } from '../services/api';
import type { Product, ItemPrice } from '../types/api';

interface ProductWithPrice extends Product {
  currentPrice?: number;
  storeId?: number;
}

interface UseProductsWithPricesResult {
  products: ProductWithPrice[];
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Hook to fetch products and merge them with their prices from ItemsPrices API
 */
export function useProductsWithPrices(categoryId?: number): UseProductsWithPricesResult {
  const [products, setProducts] = useState<ProductWithPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch products and prices in parallel
      const [productsData, pricesData] = await Promise.all([
        categoryId
          ? fustogApi.getProductsByCategory({ categoryId })
          : Promise.resolve([]), // If no category, return empty array
        fustogApi.getItemsPrices(),
      ]);

      // Create a map of prices by productId
      const priceMap = new Map<number, ItemPrice[]>();
      pricesData.forEach((priceItem) => {
        const existing = priceMap.get(priceItem.productId) || [];
        existing.push(priceItem);
        priceMap.set(priceItem.productId, existing);
      });

      // Merge products with their prices
      const productsWithPrices: ProductWithPrice[] = productsData.map((product) => {
        const productPrices = priceMap.get(product.id);

        if (productPrices && productPrices.length > 0) {
          // Get the first price (or implement logic to select best price)
          const firstPrice = productPrices[0];
          return {
            ...product,
            currentPrice: firstPrice.price,
            price: firstPrice.price, // Override product price with current price
            storeId: firstPrice.storeId,
          };
        }

        return product;
      });

      setProducts(productsWithPrices);
    } catch (err) {
      console.error('Failed to fetch products with prices:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch data'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [categoryId]);

  return { products, loading, error, refetch: fetchData };
}

/**
 * Hook to fetch all products from all categories with prices
 */
export function useAllProductsWithPrices(): UseProductsWithPricesResult {
  const [products, setProducts] = useState<ProductWithPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // First, get all categories
      const categories = await fustogApi.getCategories();

      // Fetch products for all categories and prices in parallel
      const [allProductsData, pricesData] = await Promise.all([
        Promise.all(
          categories.map((cat) =>
            fustogApi.getProductsByCategory({ categoryId: cat.id })
          )
        ),
        fustogApi.getItemsPrices(),
      ]);

      // Flatten all products from all categories
      const flatProducts = allProductsData.flat();

      // Create a map of prices by productId
      const priceMap = new Map<number, ItemPrice[]>();
      pricesData.forEach((priceItem) => {
        const existing = priceMap.get(priceItem.productId) || [];
        existing.push(priceItem);
        priceMap.set(priceItem.productId, existing);
      });

      // Merge products with their prices
      const productsWithPrices: ProductWithPrice[] = flatProducts.map((product) => {
        const productPrices = priceMap.get(product.id);

        if (productPrices && productPrices.length > 0) {
          // Get the lowest price or first price
          const lowestPrice = productPrices.reduce((min, curr) =>
            curr.price < min.price ? curr : min
          );

          return {
            ...product,
            currentPrice: lowestPrice.price,
            price: lowestPrice.price,
            storeId: lowestPrice.storeId,
          };
        }

        return product;
      });

      setProducts(productsWithPrices);
    } catch (err) {
      console.error('Failed to fetch all products with prices:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch data'));

      // Fallback to mock data
      try {
        const { mockApi } = await import('../services/mockData');
        const mockProducts = await mockApi.getProducts();
        setProducts(mockProducts);
      } catch (mockErr) {
        console.error('Failed to load mock data:', mockErr);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return { products, loading, error, refetch: fetchData };
}
