from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
 model_config=SettingsConfigDict(env_file="../../.env",extra="ignore")
 environment:str="development";database_url:str="postgresql+psycopg://instahub:instahub@localhost:5432/instahub";redis_url:str="redis://localhost:6379/0";supabase_jwt_secret:str="";web_origin:str="http://localhost:3000";credential_encryption_key:str="";meta_app_id:str="";meta_app_secret:str="";meta_redirect_uri:str="";meta_graph_version:str="v24.0";pinterest_app_id:str="";pinterest_app_secret:str="";pinterest_redirect_uri:str="";openai_api_key:str="";openai_image_model:str="gpt-image-1";openai_text_model:str="gpt-4.1-mini";s3_endpoint_url:str="";s3_public_base_url:str="";s3_bucket:str="";s3_region:str="auto";s3_access_key_id:str="";s3_secret_access_key:str=""
settings=Settings()
