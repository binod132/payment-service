# payment-service
#k3s installation without external DB.
# Step 1: Install K3s on Control Plane Node
```yaml 
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.23.8+k3s1 sh -
```
sudo systemctl status k3s
kubectl get nodes

##kubeconfig 
/etc/rancher/k3s/k3s.yaml

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml (change service ip if needed but copy first)
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

# Check the Current CNI in K3s
ls /var/lib/rancher/k3s/agent/etc/cni/net.d/  
ls /opt/cni/bin/
#@ Change the CNI in K3s
#url -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--flannel-backend=none" sh -  
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
# Check the Current Load Balancer in K3s
kubectl get pods -n kube-system -o wide
## Change the Load Balancer in K3s
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable servicelb" sh -
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.12.1/manifests/metallb.yaml

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: my-ip-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.1.240-192.168.1.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: my-advertisement
  namespace: metallb-system
```
# Change CNI IP Range After Installation (Flannel CNI)
nano /etc/rancher/k3s/config.yaml 
flannel-backend: "vxlan"
cluster-cidr: "10.42.0.0/16"  # Change this to your desired pod network range

sudo systemctl restart k3s
kubectl get nodes -o wide

# /etc/rancher/k3s/config.yaml
service-load-balancer-ips: "192.168.1.200-192.168.1.220"

###########################
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

#########
#PVC
kubectl get storageclass  
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-path
provisioner: rancher.io/local-path
reclaimPolicy: Delete
volumeBindingMode: Immediate
```
```yaml
kubectl apply -f storageclass.yaml
```
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: payment-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-path  # Make sure this matches an existing StorageClass
  hostPath:
    path: "/mnt/data"  # Path on the node where the data will be stored
```
```yaml
kubectl apply -f pv.yaml
```
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: payment-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: local-path  # Ensure this matches your PV's StorageClass
```
```yaml
kubectl apply -f pvc.yaml
```
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      containers:
      - name: payment-service
        image: binod132/payment-service:latest
        ports:
        - containerPort: 8080
        volumeMounts:
        - mountPath: "/data"
          name: payment-storage
      volumes:
      - name: payment-storage
        persistentVolumeClaim:
          claimName: payment-pvc  # This references the PVC created earlier
```

### Create a Custom StorageClass (Optional)
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-storage
provisioner: nfs-client
parameters:
  archiveOnDelete: "false"
```
```yaml
kubectl patch storageclass <your-storageclass> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```








