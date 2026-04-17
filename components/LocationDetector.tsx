import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';

export function LocationDetector() {
  const { userLocation, setUserLocation } = useApp();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const detectLocation = () => {
    setLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      setError('المتصفح لا يدعم تحديد الموقع');
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setLoading(false);
      },
      (err) => {
        setError('فشل تحديد الموقع. الرجاء السماح بالوصول للموقع');
        setLoading(false);
      }
    );
  };

  // Auto-detect on mount if no location
  useEffect(() => {
    if (!userLocation) {
      detectLocation();
    }
  }, []);

  if (loading) {
    return (
      <div className="location-detector loading">
        <div className="spinner"></div>
        <p>جاري تحديد موقعك...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="location-detector error">
        <p>{error}</p>
        <button onClick={detectLocation}>إعادة المحاولة</button>
      </div>
    );
  }

  if (!userLocation) {
    return (
      <div className="location-detector">
        <p>نحتاج موقعك لعرض المنتجات المتاحة</p>
        <button onClick={detectLocation}>تحديد موقعي</button>
      </div>
    );
  }

  return (
    <div className="location-detector success">
      <span>📍 الموقع: {userLocation.latitude.toFixed(4)}, {userLocation.longitude.toFixed(4)}</span>
      <button onClick={detectLocation} className="btn-small">تغيير</button>
    </div>
  );
}
