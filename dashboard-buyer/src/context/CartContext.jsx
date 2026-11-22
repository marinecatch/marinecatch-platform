// src/context/CartContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';

const CartContext = createContext(null);
const STORAGE_KEY = 'mc_buyer_cart';

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(items)); } catch { /* ignore */ }
  }, [items]);

  const addItem = (lot, quantityKg) => {
    setItems(prev => {
      const existing = prev.find(i => i.lot_id === lot.id);
      if (existing) {
        return prev.map(i => i.lot_id === lot.id ? { ...i, quantity_kg: quantityKg } : i);
      }
      return [...prev, {
        lot_id: lot.id, species: lot.species, lot_number: lot.lot_number,
        price_per_kg: lot.selling_price_per_kg, available_kg: lot.available_kg,
        landing_site: lot.landing_site, quantity_kg: quantityKg,
      }];
    });
  };

  const updateQuantity = (lotId, quantityKg) =>
    setItems(prev => prev.map(i => i.lot_id === lotId ? { ...i, quantity_kg: quantityKg } : i));

  const removeItem = (lotId) =>
    setItems(prev => prev.filter(i => i.lot_id !== lotId));

  const clearCart = () => setItems([]);

  const total = items.reduce((sum, i) => sum + (i.price_per_kg * i.quantity_kg), 0);

  return (
    <CartContext.Provider value={{ items, addItem, updateQuantity, removeItem, clearCart, total }}>
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
