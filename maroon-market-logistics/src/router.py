"""
Maroon Market Logistics — Route Optimization & Delivery Engine (v4.0)
Codex §4.2: Google OR-Tools for route optimization.
Real-time delivery tracking with driver assignment.
Geofenced delivery zones with dynamic pricing.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
import uuid

app = FastAPI(
    title="Maroon Market Logistics",
    description="Sovereign Delivery & Route Optimization Engine — OR-Tools Powered",
    version="4.0.0",
)


# ---------------------------------------------------------------------------
# Enums & Models
# ---------------------------------------------------------------------------

class DeliveryStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class GeoPoint(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class DeliveryZone(BaseModel):
    zone_id: str
    name: str
    center: GeoPoint
    radius_km: float = Field(default=10.0)
    base_fee: float = Field(default=5.99)
    per_km_surcharge: float = Field(default=0.75)


class Driver(BaseModel):
    driver_id: str
    name: str
    current_location: GeoPoint
    is_available: bool = True
    vehicle_type: str = "sedan"
    capacity_kg: float = 50.0


class DeliveryOrder(BaseModel):
    order_id: str
    pickup: GeoPoint
    dropoff: GeoPoint
    weight_kg: float = 1.0
    priority: int = Field(default=1, ge=1, le=5)
    customer_id: str = ""


class RouteOptimizationRequest(BaseModel):
    orders: List[DeliveryOrder]
    drivers: List[Driver]
    depot: GeoPoint


class AssignedRoute(BaseModel):
    driver_id: str
    driver_name: str
    stops: List[Dict[str, Any]]
    total_distance_km: float
    estimated_time_minutes: float
    delivery_fee: float


class RouteOptimizationResponse(BaseModel):
    routes: List[AssignedRoute]
    unassigned_orders: List[str]
    total_distance_km: float
    optimization_hash: str


# ---------------------------------------------------------------------------
# Telemetry (Palantir Mandate)
# ---------------------------------------------------------------------------

def emit_telemetry(event_type: str, payload: dict):
    envelope = {
        "source": "maroon-market-logistics",
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
        "verification_status": "PENDING_MERKLE_HASH",
    }
    print(f"[Telemetry] {json.dumps(envelope, default=str)}")


# ---------------------------------------------------------------------------
# Geo Utilities
# ---------------------------------------------------------------------------

def haversine(p1: GeoPoint, p2: GeoPoint) -> float:
    """Calculate distance in km between two GPS coordinates."""
    R = 6371.0
    lat1, lat2 = math.radians(p1.lat), math.radians(p2.lat)
    dlat = math.radians(p2.lat - p1.lat)
    dlng = math.radians(p2.lng - p1.lng)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_distance_matrix(points: List[GeoPoint]) -> List[List[float]]:
    """Builds a full distance matrix between all points."""
    n = len(points)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(points[i], points[j])
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix


# ---------------------------------------------------------------------------
# Delivery Zone Pricing
# ---------------------------------------------------------------------------

# Pre-configured zones (production: loaded from PostgreSQL)
ZONES = [
    DeliveryZone(zone_id="z1", name="Downtown Core", center=GeoPoint(lat=33.749, lng=-84.388), radius_km=5, base_fee=3.99, per_km_surcharge=0.50),
    DeliveryZone(zone_id="z2", name="Midtown", center=GeoPoint(lat=33.785, lng=-84.385), radius_km=8, base_fee=5.99, per_km_surcharge=0.75),
    DeliveryZone(zone_id="z3", name="Outer Metro", center=GeoPoint(lat=33.82, lng=-84.36), radius_km=20, base_fee=8.99, per_km_surcharge=1.25),
]


def calculate_delivery_fee(pickup: GeoPoint, dropoff: GeoPoint) -> float:
    """Calculates dynamic delivery fee based on geofenced zones."""
    distance = haversine(pickup, dropoff)
    # Find the zone closest to the dropoff
    best_zone = ZONES[-1]
    for zone in ZONES:
        if haversine(zone.center, dropoff) <= zone.radius_km:
            best_zone = zone
            break
    return round(best_zone.base_fee + distance * best_zone.per_km_surcharge, 2)


# ---------------------------------------------------------------------------
# Route Optimization (Greedy Nearest-Neighbor; OR-Tools in production)
# ---------------------------------------------------------------------------

def optimize_routes(request: RouteOptimizationRequest) -> RouteOptimizationResponse:
    """
    Greedy nearest-neighbor route optimization.
    In production, swap this with Google OR-Tools CVRP solver.
    """
    available_drivers = [d for d in request.drivers if d.is_available]
    remaining_orders = list(request.orders)
    routes: List[AssignedRoute] = []
    total_km = 0.0

    for driver in available_drivers:
        if not remaining_orders:
            break

        stops = []
        current_pos = driver.current_location
        driver_distance = 0.0
        load = 0.0

        while remaining_orders:
            # Find nearest unassigned order
            nearest_idx = -1
            nearest_dist = float("inf")
            for i, order in enumerate(remaining_orders):
                if load + order.weight_kg > driver.capacity_kg:
                    continue
                d = haversine(current_pos, order.pickup)
                if d < nearest_dist:
                    nearest_dist = d
                    nearest_idx = i

            if nearest_idx == -1:
                break

            order = remaining_orders.pop(nearest_idx)
            pickup_dist = haversine(current_pos, order.pickup)
            delivery_dist = haversine(order.pickup, order.dropoff)
            leg_dist = pickup_dist + delivery_dist

            stops.append({
                "order_id": order.order_id,
                "pickup": {"lat": order.pickup.lat, "lng": order.pickup.lng},
                "dropoff": {"lat": order.dropoff.lat, "lng": order.dropoff.lng},
                "distance_km": round(leg_dist, 2),
            })

            driver_distance += leg_dist
            load += order.weight_kg
            current_pos = order.dropoff

        if stops:
            fee = sum(
                calculate_delivery_fee(
                    GeoPoint(lat=s["pickup"]["lat"], lng=s["pickup"]["lng"]),
                    GeoPoint(lat=s["dropoff"]["lat"], lng=s["dropoff"]["lng"]),
                )
                for s in stops
            )
            routes.append(AssignedRoute(
                driver_id=driver.driver_id,
                driver_name=driver.name,
                stops=stops,
                total_distance_km=round(driver_distance, 2),
                estimated_time_minutes=round(driver_distance / 0.5, 1),  # ~30km/h avg
                delivery_fee=fee,
            ))
            total_km += driver_distance

    unassigned = [o.order_id for o in remaining_orders]

    # Cryptographic hash of the optimization result
    canonical = json.dumps({"routes": [r.model_dump() for r in routes], "unassigned": unassigned}, sort_keys=True, default=str)
    opt_hash = hashlib.sha512(canonical.encode()).hexdigest()

    return RouteOptimizationResponse(
        routes=routes,
        unassigned_orders=unassigned,
        total_distance_km=round(total_km, 2),
        optimization_hash=opt_hash,
    )


# ---------------------------------------------------------------------------
# Delivery Tracking (In-memory; production: Redis + PostgreSQL)
# ---------------------------------------------------------------------------

_tracking: Dict[str, Dict[str, Any]] = {}


class TrackingUpdate(BaseModel):
    order_id: str
    status: DeliveryStatus
    driver_id: Optional[str] = None
    location: Optional[GeoPoint] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.post("/api/v1/optimize", response_model=RouteOptimizationResponse)
async def optimize(request: RouteOptimizationRequest):
    """Optimize delivery routes using nearest-neighbor (OR-Tools in prod)."""
    result = optimize_routes(request)
    emit_telemetry("route_optimized", {
        "num_routes": len(result.routes),
        "total_km": result.total_distance_km,
        "unassigned": len(result.unassigned_orders),
    })
    return result


@app.post("/api/v1/tracking")
async def update_tracking(update: TrackingUpdate):
    """Update delivery tracking status."""
    _tracking[update.order_id] = {
        "order_id": update.order_id,
        "status": update.status.value,
        "driver_id": update.driver_id,
        "location": update.location.model_dump() if update.location else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "notes": update.notes,
    }
    emit_telemetry("tracking_updated", _tracking[update.order_id])
    return {"status": "updated", "tracking": _tracking[update.order_id]}


@app.get("/api/v1/tracking/{order_id}")
async def get_tracking(order_id: str):
    """Get current delivery tracking for an order."""
    if order_id not in _tracking:
        raise HTTPException(status_code=404, detail="Order not found")
    return _tracking[order_id]


@app.get("/api/v1/zones")
async def list_zones():
    """List all configured delivery zones."""
    return {"zones": [z.model_dump() for z in ZONES]}


@app.post("/api/v1/pricing")
async def calculate_price(pickup: GeoPoint, dropoff: GeoPoint):
    """Calculate dynamic delivery fee for a pickup/dropoff pair."""
    fee = calculate_delivery_fee(pickup, dropoff)
    distance = haversine(pickup, dropoff)
    return {"fee": fee, "distance_km": round(distance, 2)}


@app.get("/health")
async def health_check():
    return {"status": "online", "service": "maroon-market-logistics", "version": "4.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
