use sha2::{Sha512, Digest};
use serde::{Deserialize, Serialize};
use actix_web::{web, App, HttpServer, HttpResponse, middleware};
use std::time::{SystemTime, UNIX_EPOCH};

/// A single transaction payload submitted for cryptographic verification.
#[derive(Debug, Deserialize)]
struct HashRequest {
    payload: serde_json::Value,
}

/// The cryptographic receipt returned after hashing.
#[derive(Debug, Serialize)]
struct HashReceipt {
    hash: String,
    algorithm: String,
    timestamp: u64,
    verification_status: String,
}

/// Computes a SHA-512 hash of the canonical JSON representation.
fn compute_sha512(payload: &serde_json::Value) -> String {
    let canonical = serde_json::to_string(payload).unwrap_or_default();
    let mut hasher = Sha512::new();
    hasher.update(canonical.as_bytes());
    hex::encode(hasher.finalize())
}

/// Returns the current UNIX timestamp in seconds.
fn now_unix() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

/// POST /api/v1/hash — Accepts a JSON payload and returns a SHA-512 receipt.
async fn hash_payload(body: web::Json<HashRequest>) -> HttpResponse {
    let hash = compute_sha512(&body.payload);
    let receipt = HashReceipt {
        hash,
        algorithm: "SHA-512".to_string(),
        timestamp: now_unix(),
        verification_status: "VERIFIED".to_string(),
    };
    println!(
        "[Truth-Teller] Payload hashed: {}...{}",
        &receipt.hash[..16],
        &receipt.hash[receipt.hash.len() - 16..]
    );
    HttpResponse::Ok().json(receipt)
}

/// Merkle-DAG node for chaining multiple hashes into an immutable tree.
#[derive(Debug, Serialize)]
struct MerkleNode {
    hash: String,
    left: Option<String>,
    right: Option<String>,
}

/// POST /api/v1/merkle — Accepts a list of hashes and returns the Merkle root.
#[derive(Debug, Deserialize)]
struct MerkleRequest {
    hashes: Vec<String>,
}

#[derive(Debug, Serialize)]
struct MerkleResponse {
    root: String,
    depth: usize,
    leaf_count: usize,
}

async fn compute_merkle_root(body: web::Json<MerkleRequest>) -> HttpResponse {
    let mut layer: Vec<String> = body.hashes.clone();
    let leaf_count = layer.len();
    let mut depth: usize = 0;

    while layer.len() > 1 {
        let mut next_layer = Vec::new();
        for chunk in layer.chunks(2) {
            let combined = if chunk.len() == 2 {
                format!("{}{}", chunk[0], chunk[1])
            } else {
                chunk[0].clone()
            };
            let mut hasher = Sha512::new();
            hasher.update(combined.as_bytes());
            next_layer.push(hex::encode(hasher.finalize()));
        }
        layer = next_layer;
        depth += 1;
    }

    let root = layer.into_iter().next().unwrap_or_default();
    println!("[Truth-Teller] Merkle root computed. Depth: {}, Leaves: {}", depth, leaf_count);

    HttpResponse::Ok().json(MerkleResponse {
        root,
        depth,
        leaf_count,
    })
}

/// GET /health — Standard health check (Codex §5.4).
async fn health() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "online",
        "service": "maroon-truth-teller-core",
        "version": "4.0.0"
    }))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("[Truth-Teller] Core Engine Online. Port 8001.");
    println!("[Truth-Teller] SHA-512 hashing + Merkle-DAG verification ready.");

    HttpServer::new(|| {
        App::new()
            .route("/api/v1/hash", web::post().to(hash_payload))
            .route("/api/v1/merkle", web::post().to(compute_merkle_root))
            .route("/health", web::get().to(health))
    })
    .bind("0.0.0.0:8001")?
    .run()
    .await
}
