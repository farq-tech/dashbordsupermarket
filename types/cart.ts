// Cart and Order Types

export interface CartItem {
  productId: number;
  productName: string;
  productNameAr: string;
  price: number;
  quantity: number;
  image?: string;
  unit?: string;
}

export interface Cart {
  items: CartItem[];
  total: number;
}

export interface UserLocation {
  latitude: number;
  longitude: number;
  address?: string;
}

export interface Order {
  id?: string;
  items: CartItem[];
  total: number;
  location: UserLocation;
  status: 'pending' | 'confirmed' | 'preparing' | 'on_the_way' | 'delivered' | 'cancelled';
  createdAt: Date;
  estimatedDelivery?: Date;
}

export interface OrderRequest {
  items: {
    productId: number;
    quantity: number;
  }[];
  location: UserLocation;
  notes?: string;
}

export interface OrderResponse {
  orderId: string;
  status: 'success' | 'error';
  message: string;
  estimatedDelivery?: string;
  trackingUrl?: string;
}
