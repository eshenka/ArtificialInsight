use anyhow::anyhow;
use log::{info, error, debug};
use sqlx::migrate::MigrateDatabase;
use sqlx::{Postgres, PgPool};
use tonic::transport::Server;

use userdb::{DatabaseService, db_service::database_service_server::DatabaseServiceServer};

const POSTGRES_URL_ENV_VAR: &str = "USERDB_PG_URL";
const ADDRESS_ENV_VAR: &str = "USERDB_ADDR";
const PORT_ENV_VAR: &str = "USERDB_PORT";

const DEFAULT_ADDRESS: &str = "localhost";
const DEFAULT_PORT: u16 = 2780;
const DEFAULT_PG_URL: &str = "";

#[tokio::main]
async fn main() {
    // Initialize the logger
    env_logger::init();
    
    if let Err(e) = run().await {
        error!("Application error: {}", e);
    }
}

async fn run() -> anyhow::Result<()> {
    let pg_url = std::env::var(POSTGRES_URL_ENV_VAR).unwrap_or(DEFAULT_PG_URL.into());
    
    // Ensure database exists
    if !Postgres::database_exists(&pg_url).await.unwrap_or(false) {
        info!("Database does not exist. Creating database...");
        Postgres::create_database(&pg_url).await
            .map_err(|e| anyhow!("Failed to create database: {e}"))?;
        info!("Database created successfully");
    }
    
    // Run migrations
    info!("Running database migrations...");
    let pool = PgPool::connect(&pg_url)
        .await
        .map_err(|e| anyhow!("Failed to connect to database: {e}"))?;
    
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await
        .map_err(|e| anyhow!("Failed to run migrations: {e}"))?;
    
    info!("Migrations completed successfully");
    
    // Initialize the service
    let service = DatabaseService::new(&pg_url).await?;

    let address = std::env::var(ADDRESS_ENV_VAR).unwrap_or(DEFAULT_ADDRESS.into());
    let port = match std::env::var(PORT_ENV_VAR).ok() {
        Some(port) => port.parse().map_err(|e| anyhow!("parsing port: {e}"))?,
        None => DEFAULT_PORT,
    };

    let address = format!("{address}:{port}").parse()?;
    
    info!("Starting UserDB service on {}", address);

    Server::builder()
        .add_service(DatabaseServiceServer::new(service))
        .serve(address)
        .await
        .map_err(Into::into)
}
