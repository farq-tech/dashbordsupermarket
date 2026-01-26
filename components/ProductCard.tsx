import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { useImageUrl } from '../hooks/useFustogApi';
import type { Product } from '../types/api';

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const { addToCart, cart } = useApp();
  const [quantity, setQuantity] = useState(1);
  const [showAdded, setShowAdded] = useState(false);

  const imageUrl = useImageUrl(product.image || '');
  const cartItem = cart.find((item) => item.productId === product.id);

  const handleAddToCart = () => {
    addToCart(
      {
        productId: product.id,
        productName: product.name,
        productNameAr: product.nameAr || product.name,
        price: product.price || 0,
        image: imageUrl || undefined,
        unit: product.unit,
      },
      quantity
    );

    setShowAdded(true);
    setTimeout(() => setShowAdded(false), 2000);
    setQuantity(1);
  };

  return (
    <div className="product-card">
      {imageUrl && (
        <div className="product-image">
          <img src={imageUrl} alt={product.nameAr || product.name} />
          {cartItem && (
            <div className="in-cart-badge">{cartItem.quantity} في السلة</div>
          )}
        </div>
      )}

      <div className="product-info">
        <h3 className="product-name">{product.nameAr || product.name}</h3>

        {product.descriptionAr && (
          <p className="product-description">{product.descriptionAr}</p>
        )}

        <div className="product-footer">
          <div className="product-price">
            <span className="price">{product.price?.toFixed(2) || '0.00'}</span>
            <span className="currency">ريال</span>
            {product.unit && <span className="unit">/ {product.unit}</span>}
          </div>

          <div className="product-actions">
            <div className="quantity-selector">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="qty-btn"
              >
                -
              </button>
              <span className="qty-value">{quantity}</span>
              <button
                onClick={() => setQuantity(quantity + 1)}
                className="qty-btn"
              >
                +
              </button>
            </div>

            <button
              onClick={handleAddToCart}
              className={`btn-add-cart ${showAdded ? 'added' : ''}`}
            >
              {showAdded ? '✓ تمت الإضافة' : 'إضافة'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
