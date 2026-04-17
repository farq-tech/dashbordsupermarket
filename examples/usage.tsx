// Examples of how to use Fustog API hooks

import React from 'react';
import {
  useCategories,
  useCities,
  useProductsByCategory,
  useNearestStores,
  useRetailerSettings,
  useImageUrl,
} from '../hooks/useFustogApi';

// Example 1: Display Categories
export function CategoriesExample() {
  const { data: categories, loading, error } = useCategories();

  if (loading) return <div>Loading categories...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!categories) return null;

  return (
    <div>
      <h2>Categories</h2>
      <ul>
        {categories.map((category) => (
          <li key={category.id}>
            {category.nameAr || category.name}
            {category.image && <img src={category.image} alt={category.name} />}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Example 2: Display Products by Category
export function ProductsExample() {
  const [selectedCategoryId, setSelectedCategoryId] = React.useState(1);
  const { data: products, loading, error } = useProductsByCategory({
    categoryId: selectedCategoryId,
    limit: 20,
  });

  if (loading) return <div>Loading products...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!products) return null;

  return (
    <div>
      <h2>Products</h2>
      <div>
        {products.map((product) => (
          <div key={product.id}>
            <h3>{product.nameAr || product.name}</h3>
            {product.image && <img src={product.image} alt={product.name} />}
            <p>{product.descriptionAr || product.description}</p>
            {product.price && <span>{product.price} SR</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

// Example 3: Display Nearest Stores
export function NearestStoresExample() {
  // Example coordinates (Riyadh)
  const [location] = React.useState({
    latitude: 24.7136,
    longitude: 46.6753,
    radius: 10, // 10 km
  });

  const { data: stores, loading, error } = useNearestStores(location);

  if (loading) return <div>Loading stores...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!stores) return null;

  return (
    <div>
      <h2>Nearest Stores</h2>
      <ul>
        {stores.map((store) => (
          <li key={store.id}>
            <h3>{store.nameAr || store.name}</h3>
            <p>{store.addressAr || store.address}</p>
            {store.distance && <span>Distance: {store.distance} km</span>}
            {store.phone && <p>Phone: {store.phone}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Example 4: Display Cities with Selection
export function CitiesExample() {
  const { data: cities, loading, error } = useCities();
  const [selectedCity, setSelectedCity] = React.useState<number | null>(null);

  if (loading) return <div>Loading cities...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!cities) return null;

  return (
    <div>
      <h2>Select City</h2>
      <select
        value={selectedCity || ''}
        onChange={(e) => setSelectedCity(Number(e.target.value))}
      >
        <option value="">Select a city</option>
        {cities.map((city) => (
          <option key={city.id} value={city.id}>
            {city.nameAr || city.name}
          </option>
        ))}
      </select>
    </div>
  );
}

// Example 5: Display Product with Image
export function ProductWithImageExample({ productId, imageId }: { productId: number; imageId: number }) {
  const imageUrl = useImageUrl(imageId);

  return (
    <div>
      <h3>Product {productId}</h3>
      {imageUrl && (
        <img
          src={imageUrl}
          alt={`Product ${productId}`}
          style={{ maxWidth: '300px' }}
        />
      )}
    </div>
  );
}

// Example 6: Retailer Settings (Theme)
export function RetailerThemeExample() {
  const { data: settings, loading, error } = useRetailerSettings();

  React.useEffect(() => {
    if (settings) {
      // Apply theme colors
      if (settings.primaryColor) {
        document.documentElement.style.setProperty('--primary-color', settings.primaryColor);
      }
      if (settings.secondaryColor) {
        document.documentElement.style.setProperty('--secondary-color', settings.secondaryColor);
      }
    }
  }, [settings]);

  if (loading) return <div>Loading settings...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!settings) return null;

  return (
    <div>
      <h2>Retailer Info</h2>
      {settings.logo && <img src={settings.logo} alt="Logo" />}
      <p>Currency: {settings.currency}</p>
      <p>Contact: {settings.contactEmail}</p>
    </div>
  );
}
