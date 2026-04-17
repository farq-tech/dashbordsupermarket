// Fustog API Types

export interface Category {
  id: number;
  name: string;
  nameAr: string;
  image?: string;
  icon?: string;
  color?: string;
  parentId?: number;
  productCount?: number;
}

export interface Product {
  id: number;
  name: string;
  nameAr: string;
  description?: string;
  descriptionAr?: string;
  price: number;
  originalPrice?: number;
  onSale?: boolean;
  image?: string;
  categoryId?: number;
  categoryName?: string;
  brand?: string;
  brandAr?: string;
  unit?: string;
  size?: string;
  barcode?: string;
  inStock: boolean;
  store: string;
  storeName: string;
}

export interface ItemPrice {
  productId: number;
  productName: string;
  productNameAr: string;
  price: number;
  originalPrice?: number;
  onSale?: boolean;
  storeId: number;
  storeName: string;
  store: string;
  currency: string;
}

export interface Store {
  id: number;
  name: string;
  nameAr: string;
  address?: string;
  addressAr?: string;
  phone?: string;
  latitude?: number;
  longitude?: number;
  distance?: number;
  productCount?: number;
}

export interface City {
  id: number;
  name: string;
  nameAr: string;
}

export interface RetailerSettings {
  logo?: string;
  primaryColor?: string;
  secondaryColor?: string;
  currency: string;
  contactEmail?: string;
}

export interface NearestStoresQuery {
  latitude: number;
  longitude: number;
  radius?: number;
  limit?: number;
}

export interface ProductsByCategoryQuery {
  categoryId: number;
  page?: number;
  limit?: number;
}

export interface SearchQuery {
  q: string;
  store?: string;
  category?: string;
  minPrice?: number;
  maxPrice?: number;
  limit?: number;
}

export interface PriceComparison {
  productName: string;
  productNameAr: string;
  prices: {
    store: string;
    storeName: string;
    price: number;
    originalPrice?: number;
    onSale?: boolean;
    image?: string;
  }[];
  lowestPrice: number;
  lowestStore: string;
}

export interface AllData {
  categories: Category[];
  products: Product[];
  prices: ItemPrice[];
  stores: Store[];
  cities: City[];
  settings: RetailerSettings;
}
