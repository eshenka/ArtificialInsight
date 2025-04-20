use anyhow::anyhow;
use log::{info, warn, debug, error};
use sqlx::{PgPool, Row, postgres::PgRow};
use tonic::{Request, Response, Status};

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

        debug!("Creating user with language: {}, llm_preference: {}", 
               &user.language, &user.llm_preference);

        let result = sqlx::query(
            r#"
            INSERT INTO users (token, language, llm_preference, description, num_requests)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            "#)
            .bind(&user.token)
            .bind(&user.language)
            .bind(&user.llm_preference)
            .bind(&user.description)
            .bind(user.num_requests as i32)
            .map(|row: PgRow| row.get::<i64, _>("id"))
            .fetch_one(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while creating user: {}", e);
                Status::internal(format!("Failed to create user: {}", e))
            })?;

        info!("User created successfully with ID: {}", result);
        let response = CreateUserResponse {
            user_id: result as u64,
        };

        Ok(Response::new(response))
    }

    async fn get_user(
        &self,
        request: Request<GetUserRequest>,
    ) -> Result<Response<GetUserResponse>, Status> {
        let user_id = request.into_inner().user_id;
        debug!("Received request to get user with ID: {}", user_id);

        let row = sqlx::query(
            r#"
            SELECT id, token, language, llm_preference, description, num_requests
            FROM users
            WHERE id = $1
            "#)
            .bind(user_id as i64)
            .fetch_optional(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while fetching user {}: {}", user_id, e);
                Status::internal(format!("Database error: {}", e))
            })?;

        let row = match row {
            Some(row) => {
                debug!("User found with ID: {}", user_id);
                row
            },
            None => {
                warn!("User not found with ID: {}", user_id);
                return Err(Status::not_found(format!("User with ID {} not found", user_id)))
            }
        };

        let user = User {
            id: row.get::<i64, _>("id") as u64,
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

        if user.id == 0 {
            warn!("Update user request received with ID 0");
            return Err(Status::invalid_argument("User ID is required"));
        }

        debug!("Updating user with ID: {}", user.id);

        // Check if user exists
        let exists = sqlx::query("SELECT EXISTS(SELECT 1 FROM users WHERE id = $1) as exists")
            .bind(user.id as i64)
            .fetch_one(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while checking if user {} exists: {}", user.id, e);
                Status::internal(format!("Database error: {}", e))
            })?
            .get::<bool, _>("exists");

        if !exists {
            warn!("Update request for non-existent user ID: {}", user.id);
            return Err(Status::not_found(format!("User with ID {} not found", user.id)));
        }

        // Update only non-empty fields
        let row = sqlx::query(
            r#"
            UPDATE users
            SET
                token = COALESCE(NULLIF($1, ''), token),
                language = COALESCE(NULLIF($2, ''), language),
                llm_preference = COALESCE(NULLIF($3, ''), llm_preference),
                description = COALESCE(NULLIF($4, ''), description),
                num_requests = COALESCE($5, num_requests)
            WHERE id = $6
            RETURNING id, token, language, llm_preference, description, num_requests
            "#)
            .bind(&user.token)
            .bind(&user.language)
            .bind(&user.llm_preference)
            .bind(&user.description)
            .bind(user.num_requests)
            .bind(user.id as i64)
            .fetch_one(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while updating user {}: {}", user.id, e);
                Status::internal(format!("Failed to update user: {}", e))
            })?;

        info!("User {} updated successfully", user.id);
        
        let updated_user = User {
            id: row.get::<i64, _>("id") as u64,
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
        let user_id = request.into_inner().user_id;
        debug!("Received request to delete user with ID: {}", user_id);

        let row = sqlx::query(
            r#"
            DELETE FROM users
            WHERE id = $1
            RETURNING id, token, language, llm_preference, description, num_requests
            "#)
            .bind(user_id as i64)
            .fetch_optional(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while deleting user {}: {}", user_id, e);
                Status::internal(format!("Database error: {}", e))
            })?;

        let row = match row {
            Some(row) => {
                info!("User {} deleted successfully", user_id);
                row
            },
            None => {
                warn!("Delete request for non-existent user ID: {}", user_id);
                return Err(Status::not_found(format!("User with ID {} not found", user_id)))
            }
        };

        let user = User {
            id: row.get::<i64, _>("id") as u64,
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
        let user_id = req.user_id;
        let delta = req.delta as i32;
        
        debug!("Received request to update request count for user {}: +{}", user_id, delta);

        let row = sqlx::query(
            r#"
            UPDATE users
            SET num_requests = num_requests + $1
            WHERE id = $2
            RETURNING num_requests
            "#)
            .bind(delta)
            .bind(user_id as i64)
            .fetch_optional(&self.pool)
            .await
            .map_err(|e| {
                error!("Database error while updating request count for user {}: {}", user_id, e);
                Status::internal(format!("Database error: {}", e))
            })?;

        let row = match row {
            Some(row) => {
                let new_count = row.get::<i32, _>("num_requests");
                info!("User {} request count updated to {}", user_id, new_count);
                row
            },
            None => {
                warn!("Request count update for non-existent user ID: {}", user_id);
                return Err(Status::not_found(format!("User with ID {} not found", user_id)))
            }
        };

        let response = UpdateUserRequestCountResponse {
            requests: row.get::<i32, _>("num_requests") as u64,
        };

        Ok(Response::new(response))
    }
}
