# Azure Key Vault + AKS + Python App using User Assigned Managed Identity (UAMI)

This guide demonstrates how to access **Azure Key Vault secrets** from a **Python app running in AKS**, using a **User Assigned Managed Identity (UAMI)** assigned to the AKS node pool.

---

## ✨ Features

- Uses UAMI assigned to AKS node pool
- Secure access to Azure Key Vault using `DefaultAzureCredential`
- No secrets in environment variables
- Simple setup using node-level identity

---

## 👀 Prerequisites

- Azure CLI
- Docker
- Kubernetes CLI (`kubectl`)
- Azure subscription with sufficient privileges

---

## ⚙️ Step-by-Step Setup

### 1. Define Environment Variables

```bash
cat <<EOF > env.sh
export LOCATION="eastasia"
export RESOURCE_GROUP="aks-uami-demo-rg"
export AKS_NAME="aks-uami-demo"
export KEYVAULT_NAME="kvuami\$RANDOM"
export SECRET_NAME="DemoSecret"
export SECRET_VALUE="SuperSecret123"
export APP_NAME="kv-reader"
export IMAGE_NAME="kv-reader"
export ACR_NAME="uamiacr\$RANDOM"
export IDENTITY_NAME="uami-kv-access"
EOF
source env.sh
```

### 2. Create Resource Group and UAMI

```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
az identity create --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --location $LOCATION
```

Store identity details:

```bash
IDENTITY_CLIENT_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query clientId -o tsv)
IDENTITY_RESOURCE_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query id -o tsv)
```

### 3. Create AKS Cluster with User Assigned Managed Identity

```bash
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_NAME \
  --enable-managed-identity \
  --assign-identity $IDENTITY_RESOURCE_ID \
  --node-count 1 \
  --generate-ssh-keys
az aks get-credentials --name $AKS_NAME --resource-group $RESOURCE_GROUP
```

### 4. Create Azure Key Vault and Set a Secret

```bash
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --enable-rbac-authorization true

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name $SECRET_NAME \
  --value "$SECRET_VALUE"
```

### 5. Grant the Managed Identity Access to Key Vault

```bash
IDENTITY_PRINCIPAL_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query principalId -o tsv)

az role assignment create \
  --assignee-object-id $IDENTITY_PRINCIPAL_ID \
  --role "Key Vault Secrets User" \
  --scope $(az keyvault show --name $KEYVAULT_NAME --query id -o tsv)
```

---

## 🐍 Python App

### `app.py`
```python
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
```

### `Dockerfile`
```Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install azure-identity azure-keyvault-secrets
CMD ["python", "app.py"]
```

---

## 📦 Build and Push Docker Image

```bash
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic
az aks update -n $AKS_NAME -g $RESOURCE_GROUP --attach-acr $ACR_NAME
az acr login --name $ACR_NAME

docker build -t $ACR_NAME.azurecr.io/$IMAGE_NAME:v1 .
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:v1
```

---

## ☸️ Kubernetes Deployment

### `deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kv-reader
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kv-reader
  template:
    metadata:
      labels:
        app: kv-reader
    spec:
      containers:
      - name: kv-reader
        image: <ACR_NAME>.azurecr.io/kv-reader:v1
        env:
        - name: KEY_VAULT_NAME
          value: "<KEYVAULT_NAME>"
        - name: SECRET_NAME
          value: "<SECRET_NAME>"
```

```bash
kubectl apply -f deployment.yaml
```

---

## 🔍 Verify Output

```bash
kubectl get pods
kubectl logs <pod-name>
```
Expected output:
```
Secret value: SuperSecret123
```

---

## 🧹 Cleanup

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

---

You have now successfully set up AKS to access Azure Key Vault using a **User Assigned Managed Identity** and Python SDK.
