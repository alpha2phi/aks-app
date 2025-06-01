from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

vault_name = os.getenv("KEY_VAULT_NAME")
secret_name = os.getenv("SECRET_NAME")
vault_url = f"https://{vault_name}.vault.azure.net"

credential = DefaultAzureCredential()
client = SecretClient(vault_url=vault_url, credential=credential)

retrieved = client.get_secret(secret_name)
print(f"Secret value: {retrieved.value}")
