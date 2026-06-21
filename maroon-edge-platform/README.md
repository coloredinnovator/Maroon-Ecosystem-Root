# Maroon Edge Platform (Sovereign Control Plane)

This directory contains the edge infrastructure and routing mesh for the Maroon Ecosystem.

## Architecture & Separateness

**Mission Critical Separation:**
This edge platform is explicitly decoupled from the core application code (`maroon-council-core`, `maroon-market-core`, etc.). 

1. **Ingress Only:** This platform defines the Envoy proxies, the `xDS` Sovereign Control Plane, and the routing logic. It acts as the front door.
2. **No App Code:** No application business logic lives here.
3. **Cybersecurity Isolation:** The ExtAuthz token verification logic does NOT live here. It is physically isolated in the standalone `maroon-safespace-core` repository to guarantee a "completely standalone, solo" security posture.
4. **Design System Independence:** The Maroon Kernel design system (`maroon-kernel`) is not embedded here. The UI components are consumed by the individual applications downstream, not by the routing layer.

This strict separation ensures that multi-agent systems and engineers do not conflate routing logic with application logic, design tokens, or security policies.
