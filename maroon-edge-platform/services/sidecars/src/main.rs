use warp::Filter;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
struct AuthRequest {
    headers: std::collections::HashMap<String, String>,
}

#[derive(Serialize, Deserialize, Debug)]
struct AuthResponse {
    status: u16,
    message: String,
}

#[tokio::main]
async fn main() {
    env_logger::init();
    log::info!("Starting Safe Space ExtAuthz Sidecar on port 50051");

    // ExtAuthz endpoint expected by Envoy
    let auth = warp::post()
        .and(warp::path("auth"))
        .and(warp::body::json())
        .map(|req: AuthRequest| {
            // Check for Safe Space token or specific headers
            let is_authorized = req.headers.contains_key("x-maroon-safe-space-token");
            
            if is_authorized {
                log::info!("Request authorized");
                warp::reply::json(&AuthResponse {
                    status: 200,
                    message: "OK".into()
                })
            } else {
                log::warn!("Unauthorized request dropped at the edge");
                warp::reply::json(&AuthResponse {
                    status: 403,
                    message: "Forbidden by Safe Space Layer".into()
                })
            }
        });

    warp::serve(auth).run(([0, 0, 0, 0], 50051)).await;
}
