# Sovereign Edge Control Plane Architecture

The Maroon Edge Platform is a globally distributed edge routing mesh powered by Envoy proxies, an xDS Sovereign Control Plane, and async provisioning workers. This system forms the root infrastructure for the Maroon Ecosystem.

## Architecture Diagram

```mermaid
graph TD
    %% Define Nodes
    Client((Client Request))
    ALB[AWS Load Balancer]
    Envoy[Envoy Edge Fleet <br/> Auto Scaling Group]
    RustSidecar[Rust Auth/Rate Limit Sidecar]
    
    FastAPI[Broker FastAPI]
    DynamoDB[(DynamoDB State)]
    SQS[AWS SQS Queue]
    Worker[Python Worker]
    
    Sovereign[Sovereign Control Plane <br/> xDS Server]
    S3[(S3 Templates)]
    
    BigQuery[(BigQuery <br/> KIRO Brain)]
    Apps[Maroon Apps <br/> Safe Space Core, Council Core]

    %% Data Plane
    Client -->|HTTPS| ALB
    ALB --> Envoy
    Envoy <-->|gRPC ExtAuthz| RustSidecar
    Envoy -->|Proxies Traffic| Apps

    %% Control Plane (Sovereign)
    Sovereign -->|Streams Config xDS| Envoy
    Sovereign -->|Reads Context| DynamoDB
    Sovereign -->|Loads Templates| S3
    
    %% BigQuery / KIRO Integration
    Sovereign -.->|Syncs Config Events| BigQuery
    Worker -.->|Syncs Provision Events| BigQuery

    %% Broker Provisioning Flow
    Apps -->|1. Requests Infrastructure| FastAPI
    FastAPI -->|2. Saves State| DynamoDB
    FastAPI -->|3. Enqueues Task| SQS
    SQS -->|4. Consumes Task| Worker
    Worker -->|5. Provisions DNS/ACM| AWS[AWS APIs]
    Worker -->|6. Updates State| DynamoDB
```

## BigQuery & Project KIRO Integration

This architecture natively integrates with **Project KIRO (The AWS IDE / Brain Repo)** and **BigQuery**.

- As infrastructure is requested and provisioned via the Broker/Worker layer, event states are synced directly to BigQuery.
- As the Sovereign Control Plane streams dynamic configurations to Envoy, the `cds_update` and `lds_update` events are logged to BigQuery.
- This creates a centralized, queryable ledger (Master Codex) of all infrastructure mutations, enabling the KIRO AI brain to analyze routing patterns, perform autonomous anomaly detection, and optimize edge configurations.
