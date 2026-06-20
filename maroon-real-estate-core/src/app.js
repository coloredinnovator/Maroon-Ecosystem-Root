/**
 * Maroon Real Estate Core — Land Trust & Asset Management (v4.0)
 * Codex §4.4: Property acquisition, sovereign trust management,
 * tax lien tracking, opportunity zone analysis, portfolio valuation.
 */
const express = require('express');
const crypto = require('crypto');

const app = express();
app.use(express.json());

// ---------------------------------------------------------------------------
// Telemetry (Palantir Mandate — Codex §5.1)
// ---------------------------------------------------------------------------
function emitTelemetry(eventType, payload) {
  const envelope = {
    source: 'maroon-real-estate-core',
    event_type: eventType,
    timestamp: new Date().toISOString(),
    data: payload,
    verification_status: 'VERIFIED',
    merkle_hash: crypto.createHash('sha512').update(JSON.stringify(payload)).digest('hex'),
  };
  console.log('[Telemetry]', JSON.stringify(envelope));
}

function computeHash(data) {
  return crypto.createHash('sha512').update(JSON.stringify(data)).digest('hex');
}

// ---------------------------------------------------------------------------
// In-Memory Stores (Production: PostgreSQL)
// ---------------------------------------------------------------------------
const properties = new Map();
const trusts = new Map();
const taxLiens = new Map();
const opportunityZones = new Map();
let propertyIdCounter = 1;

// Seed Opportunity Zones
[
  { zone_id: 'OZ-001', name: 'Atlanta Westside', state: 'GA', census_tract: '13121006500', designation_year: 2018, investment_cap: 50000000 },
  { zone_id: 'OZ-002', name: 'Detroit Corktown', state: 'MI', census_tract: '26163523400', designation_year: 2018, investment_cap: 30000000 },
  { zone_id: 'OZ-003', name: 'Houston Third Ward', state: 'TX', census_tract: '48201311300', designation_year: 2018, investment_cap: 40000000 },
].forEach(oz => opportunityZones.set(oz.zone_id, oz));

// ---------------------------------------------------------------------------
// Property Endpoints
// ---------------------------------------------------------------------------

app.post('/api/v1/properties', (req, res) => {
  const { address, city, state, zip, parcel_id, property_type, acreage, assessed_value, market_value, owner_entity, opportunity_zone_id } = req.body;
  const id = `PROP-${String(propertyIdCounter++).padStart(5, '0')}`;
  const property = {
    property_id: id,
    address, city, state, zip, parcel_id,
    property_type: property_type || 'RESIDENTIAL',
    acreage: acreage || 0,
    assessed_value: assessed_value || 0,
    market_value: market_value || 0,
    owner_entity: owner_entity || '',
    opportunity_zone_id: opportunity_zone_id || null,
    trust_id: null,
    status: 'ACTIVE',
    acquisition_date: new Date().toISOString(),
    property_hash: computeHash({ address, parcel_id, assessed_value }),
    created_at: new Date().toISOString(),
  };
  properties.set(id, property);
  emitTelemetry('property_registered', { property_id: id, type: property.property_type, city, state });
  res.status(201).json({ status: 'registered', property_id: id, hash: property.property_hash });
});

app.get('/api/v1/properties', (req, res) => {
  let results = Array.from(properties.values());
  if (req.query.state) results = results.filter(p => p.state === req.query.state);
  if (req.query.type) results = results.filter(p => p.property_type === req.query.type);
  if (req.query.oz) results = results.filter(p => p.opportunity_zone_id === req.query.oz);
  res.json({ properties: results, total: results.length });
});

app.get('/api/v1/properties/:id', (req, res) => {
  const prop = properties.get(req.params.id);
  if (!prop) return res.status(404).json({ error: 'Property not found' });
  res.json(prop);
});

// ---------------------------------------------------------------------------
// Trust Endpoints (Sovereign Land Trusts)
// ---------------------------------------------------------------------------

app.post('/api/v1/trusts', (req, res) => {
  const { name, trust_type, beneficiaries, trustee, property_ids, formation_state } = req.body;
  const trust_id = `TRT-${crypto.randomUUID().slice(0, 8)}`;
  const trust = {
    trust_id,
    name, 
    trust_type: trust_type || 'LAND_TRUST',
    beneficiaries: beneficiaries || [],
    trustee: trustee || '',
    property_ids: property_ids || [],
    formation_state: formation_state || 'GA',
    total_asset_value: 0,
    status: 'ACTIVE',
    trust_hash: computeHash({ name, trustee, property_ids }),
    created_at: new Date().toISOString(),
  };

  // Calculate total asset value from linked properties
  trust.total_asset_value = (trust.property_ids || []).reduce((sum, pid) => {
    const prop = properties.get(pid);
    return sum + (prop ? prop.market_value : 0);
  }, 0);

  // Link properties to trust
  for (const pid of trust.property_ids) {
    if (properties.has(pid)) {
      properties.get(pid).trust_id = trust_id;
    }
  }

  trusts.set(trust_id, trust);
  emitTelemetry('trust_created', { trust_id, name, type: trust.trust_type, properties: trust.property_ids.length });
  res.status(201).json({ status: 'created', trust_id, total_asset_value: trust.total_asset_value });
});

app.get('/api/v1/trusts', (req, res) => {
  res.json({ trusts: Array.from(trusts.values()), total: trusts.size });
});

app.get('/api/v1/trusts/:id', (req, res) => {
  const trust = trusts.get(req.params.id);
  if (!trust) return res.status(404).json({ error: 'Trust not found' });
  res.json(trust);
});

// ---------------------------------------------------------------------------
// Tax Lien Endpoints
// ---------------------------------------------------------------------------

app.post('/api/v1/tax-liens', (req, res) => {
  const { property_id, lien_amount, interest_rate, jurisdiction, auction_date } = req.body;
  const lien_id = `LIEN-${crypto.randomUUID().slice(0, 8)}`;
  const lien = {
    lien_id,
    property_id,
    lien_amount: lien_amount || 0,
    interest_rate: interest_rate || 12.0,
    jurisdiction: jurisdiction || '',
    auction_date: auction_date || null,
    status: 'ACTIVE',
    redemption_deadline: null,
    created_at: new Date().toISOString(),
  };
  taxLiens.set(lien_id, lien);
  emitTelemetry('tax_lien_tracked', { lien_id, property_id, amount: lien.lien_amount });
  res.status(201).json({ status: 'tracked', lien_id });
});

app.get('/api/v1/tax-liens', (req, res) => {
  let results = Array.from(taxLiens.values());
  if (req.query.property_id) results = results.filter(l => l.property_id === req.query.property_id);
  res.json({ liens: results, total: results.length });
});

// ---------------------------------------------------------------------------
// Opportunity Zone Endpoints
// ---------------------------------------------------------------------------

app.get('/api/v1/opportunity-zones', (req, res) => {
  let zones = Array.from(opportunityZones.values());
  if (req.query.state) zones = zones.filter(z => z.state === req.query.state);
  res.json({ opportunity_zones: zones, total: zones.length });
});

app.get('/api/v1/opportunity-zones/:id/analysis', (req, res) => {
  const zone = opportunityZones.get(req.params.id);
  if (!zone) return res.status(404).json({ error: 'Opportunity zone not found' });
  
  const zoneProperties = Array.from(properties.values()).filter(p => p.opportunity_zone_id === req.params.id);
  const totalValue = zoneProperties.reduce((sum, p) => sum + p.market_value, 0);
  
  res.json({
    zone,
    properties_count: zoneProperties.length,
    total_portfolio_value: totalValue,
    available_investment_capacity: zone.investment_cap - totalValue,
    analysis_hash: computeHash({ zone_id: req.params.id, total_value: totalValue }),
  });
});

// ---------------------------------------------------------------------------
// Portfolio Valuation
// ---------------------------------------------------------------------------

app.get('/api/v1/portfolio/valuation', (req, res) => {
  const allProperties = Array.from(properties.values());
  const allTrusts = Array.from(trusts.values());
  
  const totalAssessed = allProperties.reduce((sum, p) => sum + p.assessed_value, 0);
  const totalMarket = allProperties.reduce((sum, p) => sum + p.market_value, 0);
  
  const byType = {};
  allProperties.forEach(p => {
    byType[p.property_type] = (byType[p.property_type] || 0) + p.market_value;
  });
  
  const byState = {};
  allProperties.forEach(p => {
    byState[p.state] = (byState[p.state] || 0) + p.market_value;
  });

  const valuation = {
    total_properties: allProperties.length,
    total_trusts: allTrusts.length,
    total_assessed_value: totalAssessed,
    total_market_value: totalMarket,
    appreciation: totalMarket - totalAssessed,
    value_by_type: byType,
    value_by_state: byState,
    active_liens: Array.from(taxLiens.values()).filter(l => l.status === 'ACTIVE').length,
    valuation_hash: computeHash({ total: totalMarket, properties: allProperties.length }),
    generated_at: new Date().toISOString(),
  };

  emitTelemetry('portfolio_valuation', { total_market: totalMarket, total_properties: allProperties.length });
  res.json(valuation);
});

// ---------------------------------------------------------------------------
// Health (Codex §5.4)
// ---------------------------------------------------------------------------

app.get('/health', (req, res) => {
  res.json({ status: 'online', service: 'maroon-real-estate-core', version: '4.0.0' });
});

const PORT = process.env.PORT || 8003;
app.listen(PORT, () => {
  console.log(`[Real Estate Core] Sovereign Land Trust Engine v4.0 Online. Port ${PORT}.`);
});

module.exports = app;
