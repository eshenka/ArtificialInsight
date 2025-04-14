use anyhow::anyhow;
use sqlx::PgPool;

use db_service::*;

pub mod db_service {
    tonic::include_proto!("userdb");
}

pub struct DatabaseService {
    _pool: PgPool,
}

impl DatabaseService {
    pub async fn new(postgres_url: &str) -> anyhow::Result<Self> {
        let pool = PgPool::connect(postgres_url)
            .await
            .map_err(|e| anyhow!("connecting to postgres: {e}"))?;

        Ok(Self { _pool: pool })
    }
}

#[tonic::async_trait]
impl db_service::database_service_server::DatabaseService for DatabaseService {
    async fn create_user(
        &self,
        _request: tonic::Request<CreateUserRequest>,
    ) -> tonic::Result<tonic::Response<CreateUserResponse>> {
        todo!()
    }

    async fn get_user(
        &self,
        _request: tonic::Request<GetUserRequest>,
    ) -> tonic::Result<tonic::Response<GetUserResponse>> {
        todo!()
    }

    async fn update_user(
        &self,
        _request: tonic::Request<UpdateUserRequest>,
    ) -> tonic::Result<tonic::Response<UpdateUserResponse>> {
        todo!()
    }

    async fn delete_user(
        &self,
        _request: tonic::Request<DeleteUserRequest>,
    ) -> tonic::Result<tonic::Response<DeleteUserResponse>> {
        todo!()
    }

    async fn update_user_request_count(
        &self,
        _request: tonic::Request<UpdateUserRequestCountRequest>,
    ) -> tonic::Result<tonic::Response<UpdateUserRequestCountResponse>> {
        todo!()
    }
}
