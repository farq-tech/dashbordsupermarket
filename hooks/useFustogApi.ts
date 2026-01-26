import { useState, useEffect, useCallback } from 'react';
import { fustogApi } from '../services/api';
import type {
  Category,
  City,
  Product,
  ItemPrice,
  Store,
  RetailerSettings,
  NearestStoresQuery,
  ProductsByCategoryQuery,
  AllData,
} from '../types/api';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

// Generic hook for API calls
function useApiCall<T>(
  apiCall: () => Promise<T>,
  deps: any[] = []
): UseApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// Categories Hook
export function useCategories(): UseApiState<Category[]> {
  return useApiCall(() => fustogApi.getCategories());
}

// Cities Hook
export function useCities(): UseApiState<City[]> {
  return useApiCall(() => fustogApi.getAllCities());
}

// Products by Category Hook
export function useProductsByCategory(
  params: ProductsByCategoryQuery
): UseApiState<Product[]> {
  return useApiCall(
    () => fustogApi.getProductsByCategory(params),
    [params.categoryId, params.page, params.limit]
  );
}

// Items Prices Hook
export function useItemsPrices(): UseApiState<ItemPrice[]> {
  return useApiCall(() => fustogApi.getItemsPrices());
}

// Nearest Stores Hook
export function useNearestStores(
  params: NearestStoresQuery | null
): UseApiState<Store[]> {
  return useApiCall(
    () => {
      if (!params) {
        throw new Error('Location parameters are required');
      }
      return fustogApi.getNearestStores(params);
    },
    [params?.latitude, params?.longitude, params?.radius, params?.limit]
  );
}

// Retailer Settings Hook
export function useRetailerSettings(): UseApiState<RetailerSettings> {
  return useApiCall(() => fustogApi.getRetailerSettings());
}

// Helper hook for getting image URL
export function useImageUrl(imageId: number | string | undefined): string | null {
  if (!imageId) return null;
  return fustogApi.getImageUrl(imageId);
}

// All data hook (fetches everything in parallel on mount)
// يجلب جميع البيانات الأساسية عند تركيب المكوّن ويعيدها مع حالة التحميل والخطأ
export function useAllData(): UseApiState<AllData> {
  return useApiCall(() => fustogApi.getAllData());
}
