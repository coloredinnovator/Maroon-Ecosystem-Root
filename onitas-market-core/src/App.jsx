/**
 * Onita's Market Core — Sovereign Grocery Storefront (v4.0)
 * Integrated with Firebase/Firestore and NASA-grade Telemetry
 */
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { collection, getDocs, addDoc, serverTimestamp } from 'firebase/firestore';
import { db } from './firebase';

// ---------------------------------------------------------------------------
// Telemetry Hook (Firebase Integration)
// ---------------------------------------------------------------------------
function useTelemetry() {
  const emit = async (eventType, data) => {
    try {
      await addDoc(collection(db, 'telemetry'), {
        source: 'onitas-market-core',
        event_type: eventType,
        timestamp: serverTimestamp(),
        data,
        verification_status: 'PENDING_MERKLE_HASH',
      });
      console.log(`[Telemetry Logged] ${eventType}`);
    } catch (e) {
      console.error("[Telemetry Failed]", e);
    }
  };
  return { emit };
}

// ---------------------------------------------------------------------------
// Product Card Component
// ---------------------------------------------------------------------------
function ProductCard({ product, onAddToCart }) {
  return (
    <motion.div 
      className="product-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      layout
    >
      <div className="img-container" style={{height: '200px', background: '#1e293b', borderRadius: '12px', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '3rem'}}>
        {product.icon || '🛒'}
      </div>
      <h3>{product.name}</h3>
      <p className="price">${Number(product.price).toFixed(2)}</p>
      {product.ebt_eligible && <span className="ebt-badge">EBT Eligible</span>}
      <p className="nutrition">
        Cal: {product.nutrition?.calories || 'N/A'} | 
        Protein: {product.nutrition?.protein || 'N/A'}g
      </p>
      <motion.button 
        whileTap={{ scale: 0.95 }}
        onClick={() => onAddToCart(product)}
      >
        Add to Cart
      </motion.button>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Cart Component
// ---------------------------------------------------------------------------
function Cart({ items, onCheckout, isCheckingOut }) {
  const ebtTotal = items
    .filter(i => i.ebt_eligible)
    .reduce((sum, i) => sum + Number(i.price), 0);
  const fiatTotal = items
    .filter(i => !i.ebt_eligible)
    .reduce((sum, i) => sum + Number(i.price), 0);
  const total = ebtTotal + fiatTotal;

  return (
    <motion.div 
      className="cart"
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 50 }}
    >
      <h2>Your Cart ({items.length} items)</h2>
      <div className="cart-summary">
        <p>EBT Eligible: <strong>${ebtTotal.toFixed(2)}</strong></p>
        <p>Standard: <strong>${fiatTotal.toFixed(2)}</strong></p>
        <p>Total: <strong>${total.toFixed(2)}</strong></p>
      </div>
      <motion.button 
        className="checkout-btn" 
        onClick={() => onCheckout(total)}
        disabled={isCheckingOut}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {isCheckingOut ? "Processing..." : "Sovereign Checkout"}
      </motion.button>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main App
// ---------------------------------------------------------------------------
export default function App() {
  const [cart, setCart] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const { emit } = useTelemetry();

  // Fallback products if Firestore is empty or not seeded
  const fallbackProducts = [
    { id: '1', name: 'Organic Collard Greens', price: 3.99, ebt_eligible: true, icon: '🥬', nutrition: { calories: 45, protein: 4 } },
    { id: '2', name: 'Black-Eyed Peas (1lb)', price: 2.49, ebt_eligible: true, icon: '🫘', nutrition: { calories: 160, protein: 8 } },
    { id: '3', name: 'Sweet Potato Pie', price: 8.99, ebt_eligible: true, icon: '🥧', nutrition: { calories: 280, protein: 3 } },
    { id: '4', name: 'Household Cleaner', price: 5.99, ebt_eligible: false, icon: '🧼', nutrition: null },
    { id: '5', name: 'Fresh Yam (Organic)', price: 4.50, ebt_eligible: true, icon: '🍠', nutrition: { calories: 110, protein: 2 } },
    { id: '6', name: 'Filtered Water (1 Gal)', price: 1.99, ebt_eligible: true, icon: '💧', nutrition: { calories: 0, protein: 0 } },
  ];

  useEffect(() => {
    async function fetchProducts() {
      try {
        const querySnapshot = await getDocs(collection(db, "products"));
        if (querySnapshot.empty) {
          console.log("No products found in Firestore. Using fallback data.");
          setProducts(fallbackProducts);
        } else {
          const fetched = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
          setProducts(fetched);
        }
      } catch (err) {
        console.error("Error fetching products:", err);
        setProducts(fallbackProducts); // Fallback if no connection
      } finally {
        setLoading(false);
      }
    }
    fetchProducts();
  }, []);

  const handleAddToCart = (product) => {
    setCart(prev => [...prev, product]);
    emit('item_added_to_cart', { product_id: product.id, name: product.name });
  };

  const handleCheckout = async (total) => {
    setIsCheckingOut(true);
    emit('checkout_initiated', { item_count: cart.length, total });
    
    try {
      // Write the checkout securely to Firestore
      await addDoc(collection(db, 'checkouts'), {
        cart_id: `cart-${Date.now()}`,
        items: cart,
        total: total,
        timestamp: serverTimestamp()
      });
      
      emit('checkout_complete', { total });
      setCart([]);
      alert("Checkout Successful! Sovereign ledger updated.");
    } catch (err) {
      console.error(err);
      emit('checkout_failed', { error: err.message });
      alert("Checkout failed: " + err.message);
    } finally {
      setIsCheckingOut(false);
    }
  };

  if (loading) {
    return <div className="loading">Initializing Sovereign Datasets...</div>;
  }

  return (
    <div className="onitas-market">
      <header>
        <motion.h1 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          Onita's Market
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          Fresh. Sovereign. Community-Owned.
        </motion.p>
      </header>
      
      <main className="product-grid">
        {products.map((p, i) => (
          <ProductCard key={p.id} product={p} onAddToCart={handleAddToCart} />
        ))}
      </main>

      <AnimatePresence>
        {cart.length > 0 && (
          <Cart 
            items={cart} 
            onCheckout={handleCheckout} 
            isCheckingOut={isCheckingOut}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
