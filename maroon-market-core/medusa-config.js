const dotenv = require("dotenv");

let ENV_FILE_NAME = "";
switch (process.env.NODE_ENV) {
  case "production":
    ENV_FILE_NAME = ".env.production";
    break;
  case "test":
    ENV_FILE_NAME = ".env.test";
    break;
  default:
    ENV_FILE_NAME = ".env";
    break;
}

try {
  dotenv.config({ path: process.cwd() + "/" + ENV_FILE_NAME });
} catch (e) {}

// CORS when consuming Medusa from admin
const ADMIN_CORS = process.env.ADMIN_CORS || "http://localhost:7000,http://localhost:7001";

// CORS to avoid issues when consuming Medusa from a storefront
const STORE_CORS = process.env.STORE_CORS || "http://localhost:8000";

// Database URL linking to Maroon Palantir Lake
const DATABASE_URL = process.env.DATABASE_URL || "postgres://localhost/maroon_palantir_lake";

const plugins = [
  `medusa-fulfillment-manual`,
  `medusa-payment-manual`,
  // Add other plugins here for split-tender and EBT routing
];

const modules = {
  // Event bus and cache modules for scalability
};

module.exports = {
  projectConfig: {
    redis_url: process.env.REDIS_URL,
    database_url: DATABASE_URL,
    database_type: "postgres",
    store_cors: STORE_CORS,
    admin_cors: ADMIN_CORS,
    // Strict multi-region setup for autonomous tax calculations
  },
  plugins,
  modules,
};
