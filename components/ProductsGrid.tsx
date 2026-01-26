import React, { useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { ProductCard } from './ProductCard';
import type { Product } from '../types/api';

interface ProductsGridProps {
  products: Product[];
  loading?: boolean;
  error?: Error | null;
}

export function ProductsGrid({ products, loading, error }: ProductsGridProps) {
  const { selectedCategory } = useApp();

  // Filter products by selected category
  const filteredProducts = useMemo(() => {
    if (selectedCategory === null) {
      return products;
    }
    return products.filter((p) => p.categoryId === selectedCategory);
  }, [products, selectedCategory]);

  if (loading) {
    return (
      <div className="products-grid loading">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="product-skeleton"></div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="products-grid error">
        <div className="error-message">
          <p>فشل تحميل المنتجات</p>
          <p className="error-details">{error.message}</p>
        </div>
      </div>
    );
  }

  if (filteredProducts.length === 0) {
    return (
      <div className="products-grid empty">
        <div className="empty-message">
          <p>لا توجد منتجات في هذا التصنيف</p>
        </div>
      </div>
    );
  }

  return (
    <div className="products-grid">
      {filteredProducts.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
