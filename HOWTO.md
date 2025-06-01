# Microsoft Entra Workload Identity + Azure Key Vault + AKS + Python SDK

This project demonstrates how to securely access **Azure Key Vault secrets** from a **Python application** running in **Azure Kubernetes Service (AKS)** using **Microsoft Entra Workload Identity** and the Azure Python SDKs.

---

## ✨ Features

- Secure access to Key Vault from AKS pods
- Uses Entra Workload Identity (OIDC federation, per-pod identity)
- Python app using `azure-identity` + `azure-keyvault-secrets`
- Containerized with Docker
- Kubernetes deployment with annotated ServiceAccount

---

## 👀 Prerequisites

- Azure CLI with `aks-preview` extension
- Docker
- Kubernetes CLI (`kubectl`)
- Azure subscription with Owner role

---

## ⚙️ Setup Steps

### 1. Install CLI Preview Features (One-Time)

```bash
az extension add --name aks-preview
az extension update --name aks-preview
az feature register --name EnableWorkloadIdentityPreview --namespace Microsoft.ContainerService
az feature register --name AKS-AzureADWorkloadIdentity --namespace Microsoft.ContainerService
az provider register -n Microsoft.ContainerService
```

Wait ~10 minutes for registration to propagate.

### 2. Define Environment Variables

```bash
LOCATION=eastasia
RESOURCE_GROUP=aks-wi-demo-rg
AKS_NAME=aks-wi-demo
KEYVAULT_NAME=kvwi$RANDOM
SECRET_NAME=DemoSecret
SECRET_VALUE="SuperSecret123"
APP_NAME=kv-reader
SERVICE_ACCOUNT=kv-reader-sa
NAMESPACE=default
IMAGE_NAME=kv-reader
ACR_NAME=wiacr$RANDOM
```

### 3. Create AKS Cluster with Workload Identity

```bash
az group create -n $RESOURCE_GROUP -l $LOCATION

az aks create   -g $RESOURCE_GROUP   -n $AKS_NAME   --enable-oidc-issuer   --enable-workload-identity   --node-count 1   --generate-ssh-keys

az aks get-credentials -n $AKS_NAME -g $RESOURCE_GROUP
```

### 4. Create Key Vault + Secret

```bash
az keyvault create   --name $KEYVAULT_NAME   --resource-group $RESOURCE_GROUP   --location $LOCATION   --enable-rbac-authorization true

az keyvault secret set   --vault-name $KEYVAULT_NAME   --name $SECRET_NAME   --value "$SECRET_VALUE"
```

### 5. Create and Configure Managed Identity

```bash
az identity create   --name kv-wi-identity   --resource-group $RESOURCE_GROUP   --location $LOCATION

IDENTITY_CLIENT_ID=$(az identity show -g $RESOURCE_GROUP -n kv-wi-identity --query clientId -o tsv)
IDENTITY_PRINCIPAL_ID=$(az identity show -g $RESOURCE_GROUP -n kv-wi-identity --query principalId -o tsv)
OIDC_ISSUER=$(az aks show -n $AKS_NAME -g $RESOURCE_GROUP --query "oidcIssuerProfile.issuerUrl" -o tsv)
```

```bash
az role assignment create   --assignee-object-id $IDENTITY_PRINCIPAL_ID   --role "Key Vault Secrets User"   --scope $(az keyvault show --name $KEYVAULT_NAME --query id -o tsv)

az identity federated-credential create   --name kv-reader-cred   --identity-name kv-wi-identity   --resource-group $RESOURCE_GROUP   --issuer $OIDC_ISSUER   --subject "system:serviceaccount:$NAMESPACE:$SERVICE_ACCOUNT"   --audience "api://AzureADTokenExchange"
```

---

## 👾 Python App

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

## 📦 Build and Push Image

```bash
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic
az aks update -n $AKS_NAME -g $RESOURCE_GROUP --attach-acr $ACR_NAME
az acr login --name $ACR_NAME

docker build -t $ACR_NAME.azurecr.io/$IMAGE_NAME:v1 .
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:v1
```

---

## ⚙️ Kubernetes Deployment

### `serviceaccount.yaml`

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kv-reader-sa
  namespace: default
  annotations:
    azure.workload.identity/client-id: <IDENTITY_CLIENT_ID>
```

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
      serviceAccountName: kv-reader-sa
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
kubectl apply -f serviceaccount.yaml
kubectl apply -f deployment.yaml
```

---

## 🔍 Verify

```bash
kubectl get pods
kubectl logs <pod-name>
```

You should see:

```
Secret value: SuperSecret123
```

---

## 🧹 Cleanup

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

