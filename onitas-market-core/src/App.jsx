/**
 * Onita's Market Core — Sovereign Grocery Storefront (v4.0)
 * Codex §4.2: First-party grocery entity consuming Maroon Market APIs.
 * React/Next.js frontend with EBT-eligible product catalog.
 */
import React from 'react';

// ---------------------------------------------------------------------------
// Telemetry Hook (Palantir Mandate)
// ---------------------------------------------------------------------------
function useTelemetry() {
  const emit = (eventType, data) => {
    const envelope = {
      source: 'onitas-market-core',
      event_type: eventType,
      timestamp: new Date().toISOString(),
      data,
      verification_status: 'PENDING_MERKLE_HASH',
    };
    console.log('[Telemetry]', JSON.stringify(envelope));
    // In production: POST to maroon-palantir-lake /api/v1/ingest
  };
  return { emit };
}

// ---------------------------------------------------------------------------
// Product Card Component
// ---------------------------------------------------------------------------
function ProductCard({ product, onAddToCart }) {
  return (
    <div className="product-card" data-ebt={product.ebt_eligible}>
      <img src={product.image_url} alt={product.name} />
      <h3>{product.name}</h3>
      <p className="price">${product.price.toFixed(2)}</p>
      {product.ebt_eligible && <span className="ebt-badge">EBT Eligible</span>}
      <p className="nutrition">
        Cal: {product.nutrition?.calories || 'N/A'} | 
        Protein: {product.nutrition?.protein || 'N/A'}g
      </p>
      <button onClick={() => onAddToCart(product)}>Add to Cart</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Cart Component
// ---------------------------------------------------------------------------
function Cart({ items, onCheckout }) {
  const ebtTotal = items
    .filter(i => i.ebt_eligible)
    .reduce((sum, i) => sum + i.price, 0);
  const fiatTotal = items
    .filter(i => !i.ebt_eligible)
    .reduce((sum, i) => sum + i.price, 0);

  return (
    <div className="cart">
      <h2>Your Cart ({items.length} items)</h2>
      <div className="cart-summary">
        <p>EBT Eligible: <strong>${ebtTotal.toFixed(2)}</strong></p>
        <p>Standard: <strong>${fiatTotal.toFixed(2)}</strong></p>
        <p>Total: <strong>${(ebtTotal + fiatTotal).toFixed(2)}</strong></p>
      </div>
      <button className="checkout-btn" onClick={onCheckout}>
        Sovereign Checkout
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main App
// ---------------------------------------------------------------------------
export default function OnitasMarket() {
  const [cart, setCart] = React.useState([]);
  const { emit } = useTelemetry();

  const sampleProducts = [
    { id: '1', name: 'Organic Collard Greens', price: 3.99, ebt_eligible: true, 
      image_url: '/images/greens.jpg', nutrition: { calories: 45, protein: 4 } },
    { id: '2', name: 'Black-Eyed Peas (1lb)', price: 2.49, ebt_eligible: true,
      image_url: '/images/peas.jpg', nutrition: { calories: 160, protein: 8 } },
    { id: '3', name: 'Sweet Potato Pie', price: 8.99, ebt_eligible: true,
      image_url: '/images/pie.jpg', nutrition: { calories: 280, protein: 3 } },
    { id: '4', name: 'Household Cleaner', price: 5.99, ebt_eligible: false,
      image_url: '/images/cleaner.jpg', nutrition: null },
  ];

  const handleAddToCart = (product) => {
    setCart(prev => [...prev, product]);
    emit('item_added_to_cart', { product_id: product.id, name: product.name });
  };

  const handleCheckout = async () => {
    emit('checkout_initiated', { item_count: cart.length });
    // POST to maroon-market-core /store/checkout
    try {
      const response = await fetch('http://localhost:9000/store/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart_id: `cart-${Date.now()}`, items: cart }),
      });
      const result = await response.json();
      emit('checkout_complete', result);
      setCart([]);
    } catch (err) {
      emit('checkout_failed', { error: err.message });
    }
  };

  return (
    <div className="onitas-market">
      <header>
        <h1>Onita's Market</h1>
        <p>Fresh. Sovereign. Community-Owned.</p>
      </header>
      <main className="product-grid">
        {sampleProducts.map(p => (
          <ProductCard key={p.id} product={p} onAddToCart={handleAddToCart} />
        ))}
      </main>
      {cart.length > 0 && <Cart items={cart} onCheckout={handleCheckout} />}
    </div>
  );
}
