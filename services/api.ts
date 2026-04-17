/**
 * Fustog API Client
 * Connects to local server that serves Panda + Tamimi + Danube product data
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8787';

async function fetchJson<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        url.searchParams.set(k, String(v));
      }
    });
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const fustogApi = {
  // Categories
  getCategories: () => fetchJson<any[]>('/api/categories'),

  // Products by category
  getProductsByCategory: (params: { categoryId: number; page?: number; limit?: number }) =>
    fetchJson<any>('/api/products', {
      categoryId: params.categoryId,
      page: params.page || 1,
      limit: params.limit || 50,
    }).then(r => r.products || []),

  // All prices
  getItemsPrices: () => fetchJson<any[]>('/api/prices'),

  // Search products across all stores
  search: (q: string, store?: string, limit?: number) =>
    fetchJson<{ products: any[]; total: number }>('/api/search', {
      q,
      ...(store ? { store } : {}),
      limit: limit || 100,
    }),

  // Compare prices across stores
  compare: (q: string, limit?: number) =>
    fetchJson<{ comparisons: any[]; total: number }>('/api/compare', {
      q,
      limit: limit || 20,
    }),

  // Stores info
  getStores: () => fetchJson<any[]>('/api/stores'),

  // Stats
  getStats: () => fetchJson<any>('/api/stats'),

  // All cities (stub)
  getAllCities: async () => [
    { id: 1, name: 'Riyadh', nameAr: 'الرياض' },
  ],

  // Nearest stores (stub)
  getNearestStores: async (_params: any) => [],

  // Retailer settings
  getRetailerSettings: async () => ({
    currency: 'SAR',
    primaryColor: '#e94560',
    secondaryColor: '#1a1a2e',
  }),

  // Image URL
  getImageUrl: (imageId: number | string) => String(imageId),

  // All data at once
  getAllData: async () => {
    const [categories, stats, stores] = await Promise.all([
      fustogApi.getCategories(),
      fustogApi.getStats(),
      fustogApi.getStores(),
    ]);
    return {
      categories,
      products: [],
      prices: [],
      stores,
      cities: [{ id: 1, name: 'Riyadh', nameAr: 'الرياض' }],
      settings: { currency: 'SAR' },
      stats,
    };
  },
};
