from cryptography.fernet import Fernet,InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import AIProviderAccount
from app.settings import settings
def cipher()->Fernet:
 if not settings.credential_encryption_key:raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY is required")
 return Fernet(settings.credential_encryption_key.encode())
def encrypt(secret:str)->str:return cipher().encrypt(secret.encode()).decode()
def decrypt(secret:str)->str:
 try:return cipher().decrypt(secret.encode()).decode()
 except InvalidToken as exc:raise RuntimeError("Connector credential cannot be decrypted") from exc
def provider_key(db:Session,workspace_id,provider_name:str)->str:
 account=db.scalar(select(AIProviderAccount).where(AIProviderAccount.workspace_id==workspace_id,AIProviderAccount.provider_name==provider_name,AIProviderAccount.is_active.is_(True)))
 if account:return decrypt(account.encrypted_api_key)
 if provider_name=="openai" and settings.openai_api_key:return settings.openai_api_key
 raise RuntimeError(f"No active {provider_name} connector for this workspace")
