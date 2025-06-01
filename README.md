# 🔐 AKS + Key Vault + Python App using Microsoft Entra Workload Identity

Securely access **Azure Key Vault** secrets from a **Python application** running in **Azure Kubernetes Service (AKS)** using **Microsoft Entra Workload Identity (federated identity)**.

## 📦 Features

- Native Kubernetes support with Entra Workload Identity
- Fine-grained, per-pod identity access to Key Vault
- Python SDK integration (`azure-identity`, `azure-keyvault-secrets`)
- Dockerized application
- Kubernetes YAML deployment with secure identity annotation

---

## 📁 Project Structure

```
aks-keyvault-python/
├── app.py                   # Python script to fetch Key Vault secret
├── Dockerfile               # Docker build for the app
├── serviceaccount.yaml      # Kubernetes SA annotated with client ID
├── deployment.yaml          # Deployment pointing to container image
├── Tutorial.md              # Full CLI walkthrough with setup and teardown
└── README.md                # Project overview and quick start guide
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Azure CLI (`az`)
- Docker & kubectl
- `aks-preview` extension installed
- Azure subscription with Owner role

### 2. Clone and Build

```bash
git clone https://github.com/<your-org>/aks-keyvault-python.git
cd aks-keyvault-python

docker build -t <acr>.azurecr.io/kv-reader:v1 .
docker push <acr>.azurecr.io/kv-reader:v1
```

### 3. Deploy to AKS

```bash
kubectl apply -f serviceaccount.yaml
kubectl apply -f deployment.yaml
```

---

## 🔐 How It Works

- AKS is created with OIDC issuer + workload identity
- A **user-assigned managed identity** is federated to a **Kubernetes ServiceAccount**
- Python app uses `DefaultAzureCredential()` which detects the projected token and authenticates to Azure
- Secret is pulled from Key Vault and logged in the pod

---

## 📘 Full Tutorial

See [`Tutorial.md`](./Tutorial.md) for:
- CLI commands to create the AKS cluster, managed identity, federated credentials
- Key Vault setup and RBAC config
- ACR build & deployment
- Cleanup commands

---

## 🧹 Cleanup

```bash
az group delete --name <resource-group> --yes --no-wait
```

---

## 🧠 Reference Docs

- [Microsoft Entra Workload Identity](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview)
- [azure-identity SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme)
- [azure-keyvault-secrets SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/key-vault-secrets-readme)

---

## 📄 License

MIT License – free to use and modify.

## Reference

- [Workload Entity on AKS](https://learn.microsoft.com/en-us/azure/aks/workload-identity-deploy-cluster)
- [AKS Preview](https://learn.microsoft.com/en-us/azure/aks/draft)
- [Microsoft Entra Workload ID with AKS](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview?tabs=dotnet)
