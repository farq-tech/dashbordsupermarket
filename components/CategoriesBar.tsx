import React from 'react';
import { useCategories } from '../hooks/useFustogApi';
import { useApp } from '../context/AppContext';

export function CategoriesBar() {
  const { data: categories, loading, error } = useCategories();
  const { selectedCategory, setSelectedCategory } = useApp();

  if (loading) {
    return (
      <div className="categories-bar loading">
        <div className="category-skeleton"></div>
        <div className="category-skeleton"></div>
        <div className="category-skeleton"></div>
      </div>
    );
  }

  if (error || !categories) {
    return (
      <div className="categories-bar error">
        <p>فشل تحميل التصنيفات</p>
      </div>
    );
  }

  return (
    <div className="categories-bar">
      <div className="categories-scroll">
        <button
          className={`category-item ${selectedCategory === null ? 'active' : ''}`}
          onClick={() => setSelectedCategory(null)}
        >
          <span>الكل</span>
        </button>

        {categories.map((category) => (
          <button
            key={category.id}
            className={`category-item ${selectedCategory === category.id ? 'active' : ''}`}
            onClick={() => setSelectedCategory(category.id)}
          >
            {category.image && (
              <img src={category.image} alt={category.nameAr || category.name} />
            )}
            <span>{category.nameAr || category.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
