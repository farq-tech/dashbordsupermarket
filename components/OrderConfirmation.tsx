import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import type { OrderRequest, OrderResponse } from '../types/cart';

interface OrderConfirmationProps {
  isOpen: boolean;
  onClose: () => void;
}

export function OrderConfirmation({ isOpen, onClose }: OrderConfirmationProps) {
  const { cart, cartTotal, userLocation, clearCart, addOrder } = useApp();
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<OrderResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmitOrder = async () => {
    if (!userLocation) {
      setError('الرجاء تحديد موقعك أولاً');
      return;
    }

    setLoading(true);
    setError(null);

    const orderRequest: OrderRequest = {
      items: cart.map((item) => ({
        productId: item.productId,
        quantity: item.quantity,
      })),
      location: userLocation,
      notes: notes || undefined,
    };

    try {
      // TODO: Replace with actual API endpoint
      // const response = await fustogApi.submitOrder(orderRequest);

      // Simulated API response for now
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const mockResponse: OrderResponse = {
        orderId: `ORD-${Date.now()}`,
        status: 'success',
        message: 'تم استلام طلبك بنجاح! سيتم التوصيل خلال 30-45 دقيقة',
        estimatedDelivery: new Date(Date.now() + 35 * 60 * 1000).toISOString(),
      };

      setResponse(mockResponse);

      // Add to orders history
      addOrder({
        id: mockResponse.orderId,
        items: cart,
        total: cartTotal,
        location: userLocation,
        status: 'confirmed',
        createdAt: new Date(),
        estimatedDelivery: mockResponse.estimatedDelivery
          ? new Date(mockResponse.estimatedDelivery)
          : undefined,
      });

      // Clear cart after successful order
      setTimeout(() => {
        clearCart();
      }, 3000);

    } catch (err) {
      setError('فشل إرسال الطلب. الرجاء المحاولة مرة أخرى');
      console.error('Order submission error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setNotes('');
    setResponse(null);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="modal-overlay" onClick={handleClose}></div>
      <div className="order-modal">
        {response ? (
          // Success Response
          <div className="order-success">
            <div className="success-icon">✓</div>
            <h2>تم إرسال الطلب بنجاح!</h2>
            <p className="order-id">رقم الطلب: {response.orderId}</p>
            <p className="success-message">{response.message}</p>

            {response.estimatedDelivery && (
              <div className="delivery-time">
                <span>وقت التوصيل المتوقع:</span>
                <span>{new Date(response.estimatedDelivery).toLocaleTimeString('ar-SA', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}</span>
              </div>
            )}

            <button onClick={handleClose} className="btn-done">
              تم
            </button>
          </div>
        ) : (
          // Order Confirmation Form
          <div className="order-form">
            <div className="modal-header">
              <h2>تأكيد الطلب</h2>
              <button onClick={handleClose} className="btn-close">✕</button>
            </div>

            <div className="order-summary">
              <h3>ملخص الطلب</h3>
              <div className="summary-items">
                {cart.map((item) => (
                  <div key={item.productId} className="summary-item">
                    <span>{item.productNameAr}</span>
                    <span>×{item.quantity}</span>
                    <span>{(item.price * item.quantity).toFixed(2)} ريال</span>
                  </div>
                ))}
              </div>

              <div className="summary-total">
                <span>المجموع الكلي:</span>
                <span>{cartTotal.toFixed(2)} ريال</span>
              </div>
            </div>

            <div className="order-location">
              <h3>موقع التوصيل</h3>
              {userLocation ? (
                <p>📍 {userLocation.latitude.toFixed(4)}, {userLocation.longitude.toFixed(4)}</p>
              ) : (
                <p className="error">الرجاء تحديد موقعك</p>
              )}
            </div>

            <div className="order-notes">
              <label htmlFor="notes">ملاحظات إضافية (اختياري)</label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="أضف أي ملاحظات للطلب..."
                rows={3}
              />
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <div className="modal-actions">
              <button
                onClick={handleSubmitOrder}
                disabled={loading || !userLocation}
                className="btn-submit"
              >
                {loading ? 'جاري الإرسال...' : 'تأكيد وإرسال'}
              </button>
              <button onClick={handleClose} className="btn-cancel">
                إلغاء
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
