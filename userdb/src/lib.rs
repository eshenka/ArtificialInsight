use anyhow::anyhow;
use log::{info, warn, debug, error};
use sqlx::{PgPool, Row, postgres::PgRow};
use tonic::{Request, Response, Status};
use uuid::Uuid;

use db_service::*;

pub mod db_service {
    tonic::include_proto!("userdb");

}

pub struct DatabaseService {
    pool: PgPool,
}

impl DatabaseService {
    pub async fn new(postgres_url: &str) -> anyhow::Result<Self> {
        info!("Initializing DatabaseService");
        let pool = PgPool::connect(postgres_url)
            .await
            .map_err(|e| {
                error!("Failed to connect to postgres: {}", e);
                anyhow!("connecting to postgres: {e}")
            })?;

        debug!("Database connection pool established successfully");
        Ok(Self { pool })
    }
}

#[tonic::async_trait]
impl db_service::database_service_server::DatabaseService for DatabaseService {
    async fn create_user(
        &self,
        request: Request<CreateUserRequest>,
    ) -> Result<Response<CreateUserResponse>, Status> {
        debug!("Received request to create user");
        
        let user = request.into_inner().user.ok_or_else(|| {
            warn!("Create user request missing user data");
            Status::invalid_argument("User data is required")
        })?;

        // Generate a random UUID for the token
        let token = Uuid::new_v4().to_string();
        
        debug!("Creating user with token: {}, language: {}, llm_preference: {}", 
               &token, &user.language, &user.llm_preference);

        let result = sqlx::query(
            r#"
            INSERT INTO users (token, language, llm_preference, description, num_requests)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING token
            "#)
            .bind(&token)
            .bind(&user.language)
            .bind(&user.llm_preference)
            .bind(&user.description)
            .bind(user.num_requests as i32)
            .map(|row: PgRow| row.get::<String, _>("token"))
            .fetch_one(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while creating user: {}", e);
                Status::internal(format!("Failed to create user: {}", e))
            })?;

        info!("User created successfully with token: {}", result);
        let response = CreateUserResponse {
            token: result,
        };

        Ok(Response::new(response))
    }

    async fn get_user(
        &self,
        request: Request<GetUserRequest>,
    ) -> Result<Response<GetUserResponse>, Status> {
        let token = request.into_inner().token;
        debug!("Received request to get user with token: {}", token);

        let row = sqlx::query(
            r#"
            SELECT token, language, llm_preference, description, num_requests
            FROM users
            WHERE token = $1
            "#)
            .bind(&token)
            .fetch_optional(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while fetching user {}: {}", token, e);
                Status::internal(format!("Database error: {}", e))
            })?;

        let row = match row {
            Some(row) => {
                debug!("User found with token: {}", token);
                row
            },
            None => {
                warn!("User not found with token: {}", token);
                return Err(Status::not_found(format!("User with token {} not found", token)))
            }
        };

        let user = User {
            token: row.get("token"),
            language: row.get("language"),
            llm_preference: row.get("llm_preference"),
            description: row.get("description"),
            num_requests: row.get::<i32, _>("num_requests"),
        };

        let response = GetUserResponse {
            user: Some(user),
        };

        Ok(Response::new(response))
    }

    async fn update_user(
        &self,
        request: Request<UpdateUserRequest>,
    ) -> Result<Response<UpdateUserResponse>, Status> {
        debug!("Received request to update user");
        
        let user = request.into_inner().user.ok_or_else(|| {
            warn!("Update user request missing user data");
            Status::invalid_argument("User data is required")
        })?;

        if user.token.is_empty() {
            warn!("Update user request received with empty token");
            return Err(Status::invalid_argument("User token is required"));
        }

        debug!("Updating user with token: {}", &user.token);

        // Check if user exists
        let exists = sqlx::query("SELECT EXISTS(SELECT 1 FROM users WHERE token = $1) as exists")
            .bind(&user.token)
            .fetch_one(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while checking if user {} exists: {}", &user.token, e);
                Status::internal(format!("Database error: {}", e))
            })?
            .get::<bool, _>("exists");

        if !exists {
            warn!("Update request for non-existent user token: {}", &user.token);
            return Err(Status::not_found(format!("User with token {} not found", &user.token)));
        }

        // Update only non-empty fields
        let row = sqlx::query(
            r#"
            UPDATE users
            SET
                language = COALESCE(NULLIF($1, ''), language),
                llm_preference = COALESCE(NULLIF($2, ''), llm_preference),
                description = COALESCE(NULLIF($3, ''), description),
                num_requests = COALESCE($4, num_requests)
            WHERE token = $5
            RETURNING token, language, llm_preference, description, num_requests
            "#)
            .bind(&user.language)
            .bind(&user.llm_preference)
            .bind(&user.description)
            .bind(user.num_requests)
            .bind(&user.token)
            .fetch_one(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while updating user {}: {}", &user.token, e);
                Status::internal(format!("Failed to update user: {}", e))
            })?;

        info!("User {} updated successfully", &user.token);
        
        let updated_user = User {
            token: row.get("token"),
            language: row.get("language"),
            llm_preference: row.get("llm_preference"),
            description: row.get("description"),
            num_requests: row.get::<i32, _>("num_requests"),
        };

        let response = UpdateUserResponse {
            user: Some(updated_user),
        };

        Ok(Response::new(response))
    }

    async fn delete_user(
        &self,
        request: Request<DeleteUserRequest>,
    ) -> Result<Response<DeleteUserResponse>, Status> {
        let token = request.into_inner().token;
        debug!("Received request to delete user with token: {}", token);

        let row = sqlx::query(
            r#"
            DELETE FROM users
            WHERE token = $1
            RETURNING token, language, llm_preference, description, num_requests
            "#)
            .bind(&token)
            .fetch_optional(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while deleting user {}: {}", token, e);
                Status::internal(format!("Database error: {}", e))
            })?;

        let row = match row {
            Some(row) => {
                info!("User {} deleted successfully", token);
                row
            },
            None => {
                warn!("Delete request for non-existent user token: {}", token);
                return Err(Status::not_found(format!("User with token {} not found", token)))
            }
        };

        let user = User {
            token: row.get("token"),
            language: row.get("language"),
            llm_preference: row.get("llm_preference"),
            description: row.get("description"),
            num_requests: row.get::<i32, _>("num_requests"),
        };

        let response = DeleteUserResponse {
            user: Some(user),
        };

        Ok(Response::new(response))
    }

    async fn update_user_request_count(
        &self,
        request: Request<UpdateUserRequestCountRequest>,
    ) -> Result<Response<UpdateUserRequestCountResponse>, Status> {
        let req = request.into_inner();
        let token = req.token;
        let delta = req.delta as i32;
        
        debug!("Received request to update request count for user {}: +{}", token, delta);

        let row = sqlx::query(
            r#"
            UPDATE users
            SET num_requests = num_requests + $1
            WHERE token = $2
            RETURNING num_requests
            "#)
            .bind(delta)
            .bind(&token)
            .fetch_optional(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while updating request count for user {}: {}", token, e);
                Status::internal(format!("Database error: {}", e))
            })?;

        let row = match row {
            Some(row) => {
                let new_count = row.get::<i32, _>("num_requests");
                info!("User {} request count updated to {}", token, new_count);
                row
            },
            None => {
                warn!("Request count update for non-existent user token: {}", token);
                return Err(Status::not_found(format!("User with token {} not found", token)))
            }
        };

        let response = UpdateUserRequestCountResponse {
            requests: row.get::<i32, _>("num_requests") as u64,
        };

        Ok(Response::new(response))
    }
}
