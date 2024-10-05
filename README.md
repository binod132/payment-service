# payment-service
#k3s installation without external DB.
# Step 1: Install K3s on Control Plane Node
```yaml 
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.23.8+k3s1 sh -
```
sudo systemctl status k3s
kubectl get nodes
# Step 2: Install K3s on Worker Node
```yaml 
sudo cat /var/lib/rancher/k3s/server/node-token
```
```yaml
curl -sfL https://get.k3s.io | K3S_URL=https://<CONTROL_PLANE_IP>:6443 K3S_TOKEN=<NODE_TOKEN> sh -
```
```yaml
kubectl get nodes
```

# K3s Installation With External PostgreSQL Database for etcd  
##Step 1 Install PG, create user, db and connection
```yaml
sudo apt update
sudo apt install postgresql postgresql-contrib
```
## create user and database k3s
```yaml
sudo -i -u postgres
psql
CREATE DATABASE k3s;
CREATE USER k3suser WITH ENCRYPTED PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE k3s TO k3suser;
```
##Allow external connections in the postgresql.conf:
```yaml
sudo nano /etc/postgresql/12/main/postgresql.conf
listen_addresses = '*'
```
###Modify pg_hba.conf to allow connections
```yaml
sudo nano /etc/postgresql/12/main/pg_hba.conf
host    all             all             0.0.0.0/0            md5
```
###Verify the PostgreSQL Connection:
```yaml
psql -h <POSTGRESQL_SERVER_IP> -U k3suser -d k3s -W
```
##Step 2: Install K3s on Control Plane Node with PostgreSQL
```yaml
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.23.8+k3s1 sh -s - server \
--datastore-endpoint="postgres://k3suser:password@<POSTGRESQL_SERVER_IP>:5432/k3s"
```
##Step 3: Install K3s on Worker Node

# Backup K3s
```yaml
k3s etcd-snapshot save --name <backup-name>
```
```yaml
cp /var/lib/rancher/k3s/server/db/snapshots/<backup-name> /backup-location
```
##Backup PostgreSQL Database:
```yaml
pg_dump -U k3suser k3s > k3s-backup.sql
```
```yaml
cp k3s-backup.sql /backup-location
```
#Upgrade K3s to v1.24.1
##Step 1: Upgrade the Control Plane Node
```yaml
sudo systemctl stop k3s
```
```yaml
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.24.1+k3s1 sh -s - server \
--datastore-endpoint="postgres://k3suser:password@<POSTGRESQL_SERVER_IP>:5432/k3s"
```
```yaml
sudo systemctl start k3s
k3s -v
```
##Step 2: Upgrade the Worker Node
```yaml
sudo systemctl stop k3s-agent
```
```yaml
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.24.1+k3s1 K3S_URL=https://<CONTROL_PLANE_IP>:6443 K3S_TOKEN=<NODE_TOKEN> sh -
```
```yaml
sudo systemctl start k3s-agent
k3s -v
```
#if cardon
```yaml
kubectl cordon <worker-node>
kubectl drain <worker-node> --ignore-daemonsets --delete-emptydir-data
Upgrade the Worker Node
kubectl uncordon <worker-node>
```
#kubeconfig
```yaml
/etc/rancher/k3s/k3s.yaml
```
```yaml
scp <user>@<control-plane-ip>:/etc/rancher/k3s/k3s.yaml ~/k3s-config.yaml
```
```yaml
export KUBECONFIG=~/k3s-config.yaml
```
#  GitOps
## Install Flux CLI: (on control plane)
curl -s https://fluxcd.io/install.sh | sudo bash
## Bootstrap Flux with a GitHub Repository:
export GITHUB_TOKEN=<your-github-token>
export GITHUB_USER=binod132

flux bootstrap github \
  --owner=$GITHUB_USER \
  --repository=payment-service \
  --branch=main \
  --path=k8s \
  --personal


##Configure GitOps for payment-service Application
### Create a file called payment-git-repo.yaml and define the GitRepository resource:
```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: payment-service-repo
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/binod132/payment-service
  branch: main
  ref:
    branch: main
  timeout: 20s
  ignore: |
    # Ignore any files outside the k8s directory
    /*
    !/k8s
```
```yaml
kubectl apply -f payment-git-repo.yaml
```

### Create a Flux Kustomization Resource
```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: payment-service-kustomization
  namespace: flux-system
spec:
  interval: 1m
  path: "./k8s"
  prune: true
  sourceRef:
    kind: GitRepository
    name: payment-service-repo
  targetNamespace: default
```
```yaml
kubectl apply -f payment-kustomization.yaml
```
###Verify the Flux GitOps Setup
flux get sources git  
flux get kustomizations  
change manifest file and see its working..








