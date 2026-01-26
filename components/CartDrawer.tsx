import React, { useState } from 'react';
import { useApp } from '../context/AppContext';

interface CartDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onCheckout: () => void;
}

export function CartDrawer({ isOpen, onClose, onCheckout }: CartDrawerProps) {
  const { cart, cartTotal, updateQuantity, removeFromCart, clearCart } = useApp();

  if (!isOpen) return null;

  return (
    <>
      <div className="cart-overlay" onClick={onClose}></div>
      <div className={`cart-drawer ${isOpen ? 'open' : ''}`}>
        <div className="cart-header">
          <h2>السلة ({cart.length})</h2>
          <button onClick={onClose} className="btn-close">✕</button>
        </div>

        {cart.length === 0 ? (
          <div className="cart-empty">
            <p>السلة فارغة</p>
            <button onClick={onClose} className="btn-continue">
              تصفح المنتجات
            </button>
          </div>
        ) : (
          <>
            <div className="cart-items">
              {cart.map((item) => (
                <div key={item.productId} className="cart-item">
                  {item.image && (
                    <img src={item.image} alt={item.productNameAr} className="cart-item-image" />
                  )}

                  <div className="cart-item-info">
                    <h4>{item.productNameAr}</h4>
                    <p className="cart-item-price">
                      {item.price.toFixed(2)} ريال
                      {item.unit && ` / ${item.unit}`}
                    </p>
                  </div>

                  <div className="cart-item-actions">
                    <div className="quantity-controls">
                      <button
                        onClick={() => updateQuantity(item.productId, item.quantity - 1)}
                        className="qty-btn"
                      >
                        -
                      </button>
                      <span className="qty-value">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.productId, item.quantity + 1)}
                        className="qty-btn"
                      >
                        +
                      </button>
                    </div>

                    <button
                      onClick={() => removeFromCart(item.productId)}
                      className="btn-remove"
                      title="حذف"
                    >
                      🗑️
                    </button>
                  </div>

                  <div className="cart-item-total">
                    {(item.price * item.quantity).toFixed(2)} ريال
                  </div>
                </div>
              ))}
            </div>

            <div className="cart-footer">
              <button onClick={clearCart} className="btn-clear-cart">
                إفراغ السلة
              </button>

              <div className="cart-total">
                <span>المجموع:</span>
                <span className="total-amount">{cartTotal.toFixed(2)} ريال</span>
              </div>

              <button onClick={onCheckout} className="btn-checkout">
                إرسال الطلب
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}
