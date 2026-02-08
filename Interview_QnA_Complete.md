# DevOps Interview Q&A - Complete Guide

**Last Updated:** January 29, 2026

---

## Table of Contents
1. [Kubernetes](#kubernetes)
2. [AWS & Cloud](#aws--cloud)
3. [Terraform](#terraform)
4. [Jenkins & CI/CD](#jenkins--cicd)
5. [Architecture & Design](#architecture--design)

---

# KUBERNETES

## ❓ Q1: Difference Between Desired Count vs Minimum Count

**Desired Count:**
- Target number of pods Kubernetes maintains as steady state
- Defined by `replicas` or adjusted by HPA
- Best-effort - Kubernetes tries to maintain it
- Can temporarily fall below desired during issues

**Minimum Count:**
- Guaranteed minimum availability (via HPA minReplicas or PodDisruptionBudgets)
- Safety constraint to ensure app stays available
- Enforced during scaling or maintenance
- Cannot be violated during disruptions

**Simple Mental Model:**
```
Desired = "What I want"
Current = "What I have now"
Kubernetes = "Keep fixing the gap"
```

**Failure & Edge Cases:**

```
Case 1: Desired > Cluster Capacity
┌────────────────────────────────────┐
│ Desired: 5 pods                    │
│ Cluster can hold: 3 pods           │
│ Result: 2 pods stay PENDING        │
└────────────────────────────────────┘

Case 2: PDB blocks deployment
┌────────────────────────────────────┐
│ Min Available: 2 pods              │
│ Rolling update needs 3 pods down   │
│ Result: Update STUCK (waits)       │
└────────────────────────────────────┘

Case 3: HPA + PDB conflict
┌────────────────────────────────────┐
│ PDB wins during disruptions        │
│ HPA wins during metric scaling     │
└────────────────────────────────────┘
```

---

## ❓ Q2: How Do You Expose Your Application in Kubernetes?

**Answer:**
We expose applications using an **Ingress controller backed by an ALB**, which provides:
- ✅ HTTPS/TLS termination
- ✅ Path-based and host-based routing
- ✅ Cost-efficient (single LB for multiple apps)
- ✅ Better than NodePort (no high ports needed)

**Architecture:**
```
User Request
    ↓
Route53 DNS
    ↓
CloudFront (if caching)
    ↓
ALB (Load Balancer)
    ↓
Ingress Controller
    ↓
Service → Pods
```

**Example Ingress:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
spec:
  ingressClassName: alb
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /users
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 8080
```

---

## ❓ Q3: Difference Between Taints and Tolerations

**Taints (Node-level restriction):**
- Prevent pods from being scheduled on a node
- Applied at node level
- Repel pods

```bash
kubectl taint node node1 key=value:NoSchedule
```

**Tolerations (Pod-level permission):**
- Allow selected pods to bypass taint restrictions
- Applied at pod level
- Enable pods to run on tainted nodes

```yaml
tolerations:
- key: "key"
  operator: "Equal"
  value: "value"
  effect: "NoSchedule"
```

**Real-world Analogy:**
```
Taint = "No entry without permission"
Toleration = "I have permission to enter"

Master Node: 
  Taint = node-role.kubernetes.io/master:NoSchedule
  User pods = Cannot run (no toleration)
  System pods = Can run (have toleration)
```

**Common Use Cases:**
```
1. Dedicated Nodes (GPU, High Memory)
   - Taint: gpu=true:NoSchedule
   - Only GPU workloads tolerate it

2. Master Nodes
   - Taint: node-role.kubernetes.io/master:NoSchedule
   - Only system components tolerate it

3. Node Maintenance
   - Taint: node.kubernetes.io/unschedulable:NoExecute
   - Forces pods off node
```

---

## ❓ Q4: Why Pods Never Scheduled on Master Node

**Main Reason: Taints**

In Kubernetes, the master (control-plane) node has a **taint** applied by default:

```
node-role.kubernetes.io/master:NoSchedule
```

**Why This Design?**
- Resource Protection: Master runs critical control-plane components
- Stability: Prevents user workloads from affecting cluster control
- Best Practice: Separates control-plane from worker nodes

**How to Schedule Pods on Master (If Needed):**
```yaml
tolerations:
- key: node-role.kubernetes.io/master
  operator: Equal
  effect: NoSchedule
```

---

## ❓ Q5: Deployment with 3 Replicas but Only 1 Pod Scheduled

**Common Causes (Narrowed Down):**

Since 1 pod is scheduled successfully, we can rule out:
- ❌ Image Pull Errors
- ❌ Init Container Failures
- ❌ PVC Binding Issues
- ❌ Node Affinity Mismatch (at least one node matches)

**Most Likely Reasons:**
1. **Insufficient Resources** (Highest probability)
   - Only one node has enough CPU/memory
   - Others fully utilized

2. **Pod Disruption Budget (PDB)**
   - Only allows 1 pod to run

3. **Resource Quota Limits**
   - Namespace quota allows only 1 pod

**Debugging:**
```bash
kubectl describe deployment <deployment-name>
kubectl describe nodes          # Check capacity
kubectl get events --sort-by='.lastTimestamp'
```

---

## ❓ Q6: Will Cluster Autoscaler Handle 2 Pending Pods?

**In Theory:** YES ✅

**In Practice:** Depends on:

1. **Is it installed?** Not default - must be explicitly enabled
2. **Cloud provider integration:** Needs AWS ASG, GCP instance groups, etc.
3. **Node group limits:** Max nodes already at capacity?
4. **Pod constraints:** Node affinity only matches existing node?
5. **Resource requests:** Pod size > max node capacity?

**Pod Constraints Issue (Important):**

If pending pods have node affinity that only matches existing node:
```yaml
nodeSelector:
  disktype: ssd  # Only one node has this
```

Autoscaler can't help because:
- New nodes won't have `disktype: ssd` label
- Pods still can't schedule on new nodes
- Solution: Relax affinity or provision nodes with matching labels

---

## ❓ Q7: What is Ingress Controller?

**Definition:**
Reverse proxy and load balancer that reads Ingress resources and configures itself to route external traffic to services inside the cluster.

**Simple Analogy:**
```
Smart receptionist at front desk:
- Listens to incoming requests
- Reads routing rules
- Routes to correct service
```

**How It Works:**
```
Internet Traffic
    ↓
Ingress Controller (Reverse Proxy)
    ↓
Routes based on Hostname/Path
    ↓
Kubernetes Service → Pod
```

**Example:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /users
        backend:
          service:
            name: user-service
            port:
              number: 8080
      - path: /products
        backend:
          service:
            name: product-service
            port:
              number: 8080
```

**Popular Ingress Controllers:**
| Controller | Use Case |
|-----------|----------|
| NGINX Ingress | General purpose, most popular |
| HAProxy | High performance |
| Istio | Service mesh with advanced routing |
| AWS ALB | Native AWS integration |
| Traefik | Cloud-native, dynamic |

**Key Features:**
✅ Path-based routing  
✅ Host-based routing  
✅ SSL/TLS termination  
✅ Load balancing  
✅ Virtual hosting  

---

## ❓ Q8: Use of Annotations in Ingress

**What Are Annotations?**
Metadata (key-value pairs) providing controller-specific configuration.

**Why?**
- Core Ingress spec covers basic routing
- Different controllers need different features
- Annotations allow customization without changing spec

**Common Annotations (NGINX Ingress):**

1. **SSL/TLS Redirect**
```yaml
annotations:
  nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
```

2. **Rewrite URL**
```yaml
annotations:
  nginx.ingress.kubernetes.io/rewrite-target: /
```

3. **Rate Limiting**
```yaml
annotations:
  nginx.ingress.kubernetes.io/limit-rps: "10"
```

4. **CORS Headers**
```yaml
annotations:
  nginx.ingress.kubernetes.io/enable-cors: "true"
  nginx.ingress.kubernetes.io/cors-allow-origin: "*"
```

5. **Authentication**
```yaml
annotations:
  nginx.ingress.kubernetes.io/auth-type: basic
  nginx.ingress.kubernetes.io/auth-secret: basic-auth
```

**Important Notes:**
⚠️ Annotations are controller-specific
- `nginx.ingress.kubernetes.io/*` → NGINX only
- `alb.ingress.kubernetes.io/*` → AWS ALB only

✅ No validation - invalid annotations silently ignored

---

## ❓ Q9: What is Service? How Does It Work with kube-proxy?

**Service Definition:**
Abstraction providing stable network endpoint to access ephemeral pods. Since pod IPs change, Services give consistent access via ClusterIP, NodePort, or LoadBalancer.

**How kube-proxy Works:**

```
┌──────────────────────────────────────────────────────┐
│         Kubernetes Service Creation                   │
└─────────────────────┬────────────────────────────────┘
                      │
        ┌─────────────▼─────────────┐
        │ Kubernetes API Server     │
        │ Creates: Service          │
        │ Creates: Endpoints        │
        └─────────────┬─────────────┘
                      │
    ┌─────────────────▼─────────────────┐
    │  kube-proxy (runs on every node)  │
    │  Watches Service & Endpoint       │
    │  changes                          │
    └─────────────────┬─────────────────┘
                      │
        ┌─────────────▼─────────────┐
        │  Programs routing rules:  │
        │  - iptables               │
        │  - IPVS                   │
        │  - eBPF                   │
        └─────────────┬─────────────┘
                      │
    ┌─────────────────▼─────────────────┐
    │  Kernel routes traffic to pods    │
    │  based on rules                   │
    └───────────────────────────────────┘
```

**Traffic Flow:**
```
Client → Service IP (10.0.0.1:80)
    ↓
kube-proxy rule (iptables/IPVS)
    ↓
Selected Pod IP (10.244.1.5:8080)
    ↓
Pod receives request
```

**Key Points:**
```
✓ kube-proxy doesn't proxy (misleading name)
✓ Programs kernel routing rules
✓ Automatic load balancing across pods
✓ Updates rules when pods die/scale
✓ Very efficient (kernel-level forwarding)
```

**One-liner:** "Services provide stable IPs; kube-proxy programs node kernel routing rules to forward traffic to backend pods."

---

## ❓ Q10: DNS Name for Pod-to-Pod Communication Across Namespaces

**Format:**
```
<service-name>.<namespace>.svc.cluster.local
```

**Example:**
```
Frontend pod (frontend namespace) → Backend service (production namespace)
URL: backend-api.production.svc.cluster.local
```

**Full DNS Breakdown:**
```
backend-api    = Service name
.production    = Namespace
.svc           = Service resource type
.cluster.local = Cluster domain
```

**DNS Variations:**

```
Same Namespace (short form):
└─ backend-api

Same Cluster, different namespace:
└─ backend-api.production.svc.cluster.local

Shorter version (optional .svc.cluster.local):
└─ backend-api.production

Direct Pod DNS (rare):
└─ 10-244-1-5.production.pod.cluster.local
   (Pod IP with dashes, rarely used)
```

**Important Notes:**
```
✓ Always use Service DNS for pod-to-pod communication
✓ Pods are ephemeral - IPs change
✓ Services provide stable endpoint
✓ Namespace is required for cross-namespace communication
✓ Network policies can restrict communication
```

**Example YAML:**
```yaml
# Backend service in production namespace
apiVersion: v1
kind: Service
metadata:
  name: backend-api
  namespace: production
spec:
  selector:
    app: backend
  ports:
  - port: 8080

---

# Frontend pod in frontend namespace
apiVersion: v1
kind: Pod
metadata:
  name: frontend-pod
  namespace: frontend
spec:
  containers:
  - name: app
    image: frontend:1.0
    env:
    - name: BACKEND_URL
      value: "http://backend-api.production.svc.cluster.local:8080"
```

**Quick Answer:** "service-name.namespace.svc.cluster.local - that's how pods discover and communicate across namespaces."

---

## ❓ Q11: Difference Between PV and PVC

**PersistentVolume (PV):**
- Actual storage resource (physical disk/cloud storage)
- Provisioned by admin or dynamically created
- Cluster-wide resource
- Lifecycle independent of pods

**PersistentVolumeClaim (PVC):**
- Request for storage by user/application
- Like a "ticket" saying "I need 10GB storage"
- Namespace-scoped
- Binds to matching PV

**Relationship Flow:**
```
Admin provisions PV (10GB, NFS, fast)
    ↓
User creates PVC (needs 10GB, fast)
    ↓
Kubernetes binds PVC → matching PV
    ↓
Pod references PVC (not PV directly)
    ↓
Pod gets storage
```

**Real-world Analogy:**
```
Hotel Scenario:
PV = Physical hotel room (pre-built)
PVC = Your reservation (request)
Pod = You (guest)
```

**Example:**
```yaml
# Admin creates PV
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  nfs:
    server: nfs.example.com
    path: "/data"

---

# User creates PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi

---

# Pod uses PVC
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: app
    volumeMounts:
    - mountPath: /data
      name: storage
  volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: my-pvc
```

**One-liner:** "PV = storage, PVC = request for storage, Pod = consumer."

---

# AWS & CLOUD

## ❓ Q12: Current Architecture of the Project

```
┌─────────────────────────────────────────────────────────────┐
│                     USER REQUEST                             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Route53 DNS       │
                    │  (Domain routing)   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  CloudFront CDN     │
                    │  (Caches static)    │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         │                                           │
    ┌────▼────┐                                ┌────▼────────┐
    │  S3     │                                │  ALB/NLB     │
    │ (Static)│                                │ (Load Bal)   │
    └─────────┘                                └────┬────────┘
                                                    │
                                      ┌─────────────▼──────────────┐
                                      │    EKS Cluster             │
                                      │  ┌──────┐  ┌──────┐        │
                                      │  │ Pod1 │  │ Pod2 │        │
                                      │  └──────┘  └──────┘        │
                                      │  ┌──────┐                  │
                                      │  │ Pod3 │                  │
                                      │  └──────┘                  │
                                      └─────────────┬──────────────┘
                                                    │
                                      ┌─────────────▼──────────────┐
                                      │   RDS/DynamoDB             │
                                      │   (Database)               │
                                      └────────────────────────────┘
```

---

## ❓ Q13: Request Flow: Frontend S3 to Backend Pods

```
User Request
    ↓
Route53 (DNS lookup) → Returns CloudFront IP
    ↓
CloudFront (Check cache)
    ├─ Cache HIT → Serve from edge location
    └─ Cache MISS → Forward to origin (S3/ALB)
    ↓
For API requests → ALB (Layer 7 routing)
    ↓
ALB routes to EKS Service → Selects Pod based on labels
    ↓
Pod processes request → Queries RDS/DynamoDB
    ↓
Response back through ALB → CloudFront → User
```

---

## ❓ Q14: CloudFront Caching & Cache Invalidation

**How caching works:**
- CloudFront caches objects at edge locations
- TTL (Time To Live) determines cache duration
- User requests served from edge (fast, no origin call)

**Cache Invalidation:**
- Delete cached object before TTL expires
- Use path pattern: `/logo.png` or `/*` (all files)
- Invalidation takes 1-5 minutes to propagate

**Logo change scenario:**
```
1. Update logo.png in S3
2. Create CloudFront invalidation for /logo.png
3. Edge caches are cleared
4. Next user gets fresh logo from S3
```

**Without invalidation:** Users see old logo until TTL expires (hours/days).

---

## ❓ Q15: How Do You Optimize Cost During Non-Working Hours?

**Infrastructure Level:**
- Schedule Auto Scaling Groups to scale down after hours
- Stop non-prod EC2/RDS instances
- Use AWS Lambda scheduler to power off resources

**Kubernetes Level:**
- Scale deployments to zero for dev/test environments
- Use HPA + cluster autoscaler for automatic sizing
- Reduce node count after business hours

**Cloud Level:**
- Use Spot Instances (70% cheaper, acceptable for non-prod)
- S3 lifecycle policies (move old data to Glacier)
- Reserved Instances for baseline capacity

**Real-world Answer:**
```
We schedule non-prod workloads to scale down after 6 PM:
├─ AWS EventBridge triggers Lambda at 6 PM
├─ Lambda scales ASG to minimum (1 node)
├─ Kubernetes HPA scale-down kicks in
├─ Saves ~60% cost overnight
└─ Scales back up at 7 AM automatically
```

---

## ❓ Q16: How Do You Decide Container Size?

**Approach:**

**Step 1: Measure with load testing**
```
Run app under realistic load
Monitor for 24-48 hours
Track CPU & memory usage
Focus on P95/P99 values (not averages)
```

**Step 2: Calculate sizing**
```
Memory Request = (Average Usage × 1.2) + Baseline Overhead
- Baseline Overhead: 50-200MB (JVM), 20-50MB (Node.js)
- Memory Limit = Request × 1.5 (handles spikes)

CPU Request = Average Usage × 1.5
CPU Limit = Request × 2-4 (burstability)
```

**Step 3: Implementation**
```yaml
resources:
  requests:
    memory: "256Mi"    # What to reserve
    cpu: "100m"
  limits:
    memory: "512Mi"    # Max allowed
    cpu: "500m"
```

**Key Principles:**
```
1. Memory is non-compressible
   - OOMKill happens if exceeded
   - Be conservative

2. CPU is compressible
   - Can throttle without killing pod
   - More flexible with limits

3. Start with estimates, iterate
   - Deploy and monitor
   - Adjust based on metrics

4. Prefer horizontal over vertical scaling
   - Scale pods, not just resources
   - Better for availability
```

---

## ❓ Q17: End-to-End AWS Setup

```
1. Networking:    VPC → Subnets → NAT Gateway → Security Groups
2. Compute:       EKS Cluster → Node Groups
3. Storage:       S3 buckets + RDS database
4. CDN:           CloudFront distribution
5. DNS:           Route53 hosted zone
6. Security:      KMS keys, IAM roles, secrets
7. Monitoring:    CloudWatch, CloudTrail
8. Backup:        Cross-region replication, snapshots
```

---

## ❓ Q18: Private S3 Bucket - Host Application

**Problem:** Private subnet = no internet access to S3

**Solution:**

```
┌─────────────────────────────────────────────┐
│         EKS Pods (Private Subnet)           │
└────────────────────┬────────────────────────┘
                     │
    ┌────────────────▼────────────────┐
    │   S3 VPC Endpoint (Gateway)     │
    │   - No internet needed          │
    │   - Secure private connection   │
    └────────────────┬────────────────┘
                     │
                ┌────▼────────┐
                │  S3 Bucket  │
                └─────────────┘
```

**Implementation:**
1. Create S3 Gateway VPC Endpoint
2. Attach to EKS node IAM role with S3 permissions
3. Pods access S3 via endpoint (no NAT Gateway needed)

**No charges for VPC endpoint data transfer** ✅

# **S3 + CloudFront (Private S3) **
┌──────────────────┐
│   User Request   │
└────────┬─────────┘
         │
    ┌────▼──────────┐
    │  CloudFront   │
    │  (OAI/OAC)    │ ← Origin Access Identity/Control
    └────┬──────────┘
         │
    ┌────▼──────────┐
    │  Private S3   │ ← NOT publicly accessible
    │  (Static      │   Only CloudFront can access
    │   website)    │
    └───────────────┘

Interview Answer (Both Scenarios)
For hosting static website:
"Use S3 + CloudFront with Origin Access Control (OAC). Keep S3 private (block all public access). CloudFront uses OAC to access the private S3 bucket. Users access only through CloudFront URL—direct S3 access is blocked."

For EKS pods accessing S3:
"If pods in private subnet need to access S3, use an S3 Gateway VPC Endpoint. This provides private connectivity without internet access. Attach S3 permissions to EKS node IAM role. Pods can then read/write to S3 securely."

---

## ❓ Q19: KMS Keys - Why Use Them

**KMS:** Encryption key management service

**Use cases:**
- Encrypt S3 objects at rest
- Encrypt RDS/EBS volumes
- Encrypt Secrets Manager data
- Compliance (HIPAA, PCI-DSS)
- Separate keys per environment/service

**Benefits:**
```
✓ Data encrypted at rest
✓ Keys managed by AWS
✓ Audit trail of key usage
✓ Key rotation policies
✓ Compliance requirements
```

---

## ❓ Q20: S3 Lifecycle Rules

```
Day 0:     Object created (STANDARD)
Day 30:    Move to STANDARD_IA (infrequent access)
Day 90:    Move to GLACIER (archival)
Day 365:   Move to DEEP_ARCHIVE
Day 2555:  Delete permanently
```

**Use case:** Auto-reduce costs for old logs/backups

---

## ❓ Q21: Update Statefile for Console Changes

**Problem:** Resource created in console, Terraform doesn't know

**Solutions:**

```bash
# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Refresh state from AWS
terraform refresh

# Remove from state (if mistakenly added)
terraform state rm aws_instance.web
```

**Best practice:** Never create resources in console; use IaC only.

---

## ❓ Q22: Load Balancer & Route53

**Load Balancer (ALB/NLB):**
- Distributes traffic across targets (EC2, pods, Lambda)
- ALB = Layer 7 (HTTP/HTTPS, path/host-based routing)
- NLB = Layer 4 (TCP/UDP, ultra-high performance)

**Route53:**
- DNS service (domain routing)
- Routes traffic based on policies (failover, geolocation, latency)

**Setup:**
```
Domain (Route53)
    ↓
ALB DNS alias
    ↓
Target Group → EKS Pods
```

---

## ❓ Q23: Firewall - Single IP, Multiple DNS/Regions

**Problem:** Firewall allows 1 IP only, app in multiple regions

**Solution:**

```
Each Region:
Region1 → NAT Gateway (IP: 1.2.3.4)
Region2 → NAT Gateway (IP: 5.6.7.8)
          ↓
        Firewall whitelist both IPs
```

**Alternative:**
- Use AWS PrivateLink (no IP exposure)
- VPN endpoint (single connection point)

**Best:** NAT Gateway in each region (predictable, secure).

---

## ❓ Q24: Setup Monitoring

```
┌─────────────────────────────────────────────┐
│         Application & Infrastructure         │
└──────────────────┬──────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐  ┌──────▼──────┐  ┌──▼────────┐
│CloudWatch   CloudTrail     X-Ray
│ Metrics     (API logs)   (Tracing)
└───┬────┘  └──────┬──────┘  └──┬────────┘
    │              │            │
    └──────────────┼────────────┘
                   │
            ┌──────▼──────┐
            │   Alarms    │
            │ (Threshold) │
            └──────┬──────┘
                   │
         ┌─────────▼────────┐
         │  SNS → Notify    │
         │ (Email/Slack)    │
         └──────────────────┘
```

**Key metrics:**
- CPU, Memory, Disk usage
- Network I/O
- Request count, error rate, latency
- Pod restart count
- Database connections

---

## ❓ Q25: Custom CloudWatch Metric

**Via CLI:**
```bash
aws cloudwatch put-metric-data \
  --namespace "MyApp" \
  --metric-name "LoginAttempts" \
  --value 42 \
  --dimensions Name=Environment,Value=prod
```

**Via Python:**
```python
import boto3
cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='MyApp',
    MetricData=[{
        'MetricName': 'LoginAttempts',
        'Value': 42,
        'Dimensions': [{'Name': 'Environment', 'Value': 'prod'}]
    }]
)
```

---

## ❓ Q26: Disaster Recovery - Entire Region Down

**Strategy: Multi-Region Active-Passive**

```
┌──────────────────────┐         ┌──────────────────────┐
│  Primary Region      │         │  Standby Region      │
│  (Active)            │         │  (Standby)           │
│ ┌────────────────┐   │         │ ┌────────────────┐   │
│ │ EKS Cluster    │◄──┼─────────┼─│ EKS Cluster    │   │
│ └────────┬───────┘   │         │ └────────┬───────┘   │
│          │           │         │          │           │
│ ┌────────▼───────┐   │         │ ┌────────▼───────┐   │
│ │  RDS (Primary) │   │         │ │  RDS (Replica) │   │
│ └────────────────┘   │         │ └────────────────┘   │
└──────────────────────┘         └──────────────────────┘
         ↑                                    │
         │         Route53 Failover           │
         │         Health check fails         │
         └────────────────────────────────────┘
             Traffic switches to standby
```

**Recovery steps:**
1. CloudWatch detects region down
2. Route53 fails over to secondary region
3. Secondary region promotes read replica → primary
4. App resumes in secondary region
5. Once primary recovers, failback gradually

---

# TERRAFORM

## ❓ Q27: S3 Block to Create Multiple S3 Buckets

**Using `for_each` (Recommended):**
```hcl
variable "bucket_names" {
  type = list(string)
  default = ["my-bucket-1", "my-bucket-2", "my-bucket-3"]
}

resource "aws_s3_bucket" "buckets" {
  for_each = toset(var.bucket_names)
  bucket = each.value
  
  tags = {
    Name = each.value
  }
}

# Enable versioning
resource "aws_s3_bucket_versioning" "bucket_versioning" {
  for_each = aws_s3_bucket.buckets
  bucket = each.value.id
  
  versioning_configuration {
    status = "Enabled"
  }
}
```

---

## ❓ Q28: What are Provisioners?

**Provisioners:** Run scripts/commands on resources after creation or before destruction.

⚠️ **Important:** Avoid provisioners when possible - hard to debug, make infrastructure unpredictable.

**Types:**

1. **local-exec** - Run commands locally
```hcl
provisioner "local-exec" {
  command = "echo ${self.public_ip} >> /tmp/ips.txt"
}
```

2. **remote-exec** - Run commands on resource
```hcl
provisioner "remote-exec" {
  inline = [
    "sudo apt-get update",
    "sudo apt-get install -y nginx"
  ]
  
  connection {
    type = "ssh"
    user = "ec2-user"
    private_key = file("~/.ssh/id_rsa")
    host = self.public_ip
  }
}
```

3. **file** - Copy files to resource
```hcl
provisioner "file" {
  source = "local/path/app.conf"
  destination = "/tmp/app.conf"
}
```

**Better Alternative:** Use user_data instead of provisioners.

---

## ❓ Q29: What is null Block/Resource?

**null_resource:** Placeholder resource from null provider, used for triggering actions without managing actual infrastructure.

**Use Cases:**

1. **Trigger provisioners without resources**
```hcl
resource "null_resource" "cluster" {
  provisioners "local-exec" {
    command = "kubectl apply -f deployment.yaml"
  }
}
```

2. **Recreate on variable change**
```hcl
resource "null_resource" "config_update" {
  triggers = {
    config_hash = filemd5("${path.module}/config.yaml")
  }
  
  provisioner "local-exec" {
    command = "echo Config updated"
  }
}
```

---

## ❓ Q30: What is Dynamic Resource/Block?

**Dynamic blocks:** Generate resource/block configurations from lists or maps.

**Without Dynamic (Repetitive):**
```hcl
resource "aws_security_group" "web" {
  name = "web-sg"
  
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

**With Dynamic (Clean):**
```hcl
variable "ingress_rules" {
  type = list(object({
    from_port = number
    to_port = number
    protocol = string
    cidr_blocks = list(string)
  }))
}

resource "aws_security_group" "web" {
  name = "web-sg"
  
  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port = ingress.value.from_port
      to_port = ingress.value.to_port
      protocol = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
```

**Benefits:**
✅ Reduces code repetition  
✅ Makes configuration scalable  
✅ Works with for_each and count  

---

## ❓ Q31: Terraform Plugins vs Modules

**Plugins:**
- Extend Terraform functionality (providers, provisioners)
- Example: `aws`, `kubernetes`, `docker`
- Auto-downloaded from registry
- Enable provider-specific resources

**Modules:**
- Reusable Terraform code blocks
- Collection of resources (VPC, EKS, RDS)
- Organized for code reuse

**Difference:**
```
Plugins = Tools to talk to platforms
Modules = Organized code blueprints
```

---

## ❓ Q32: Terraform Modules & Directories

```
terraform/
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── eks/
│   ├── rds/
│   ├── s3/
│   └── cloudfront/
├── environments/
│   ├── dev/
│   │   ├── main.tf (calls modules)
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── main.tf
│       └── terraform.tfvars
├── main.tf
├── variables.tf
├── outputs.tf
└── terraform.tfvars
```

---

# JENKINS & CI/CD

## ❓ Q33: Pipeline Failed at SonarQube Stage - Stop & Notify

**Solution:**

```groovy
pipeline {
    agent any
    
    stages {
        stage('SonarQube Analysis') {
            steps {
                sh '''
                    mvn sonar:sonar \
                        -Dsonar.projectKey=my-app \
                        -Dsonar.host.url=http://sonar-server:9000 \
                        -Dsonar.login=${SONAR_TOKEN}
                '''
            }
            post {
                failure {
                    script {
                        // Send email notification
                        emailext(
                            subject: "Pipeline Failed: SonarQube - ${env.JOB_NAME}",
                            body: "Build #${env.BUILD_NUMBER} failed. URL: ${env.BUILD_URL}",
                            to: "${EMAIL_RECIPIENTS}"
                        )
                        
                        // Send Slack notification
                        slackSend(
                            color: 'danger',
                            message: "❌ ${env.JOB_NAME} failed at SonarQube: ${env.BUILD_URL}"
                        )
                        
                        // Mark build failed and stop
                        currentBuild.result = 'FAILURE'
                        error("SonarQube analysis failed. Pipeline stopped.")
                    }
                }
            }
        }
        
        // Deploy only runs if SonarQube succeeds
        stage('Deploy') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                echo "Deploying..."
            }
        }
    }
}
```

**Explanation:**
1. **post { failure }** - Executes when SonarQube stage fails
2. **emailext()** - Sends email notification to team
3. **slackSend()** - Posts failure alert to Slack
4. **currentBuild.result = 'FAILURE'** - Marks build as failed
5. **error()** - Throws exception to stop pipeline
6. **when condition** - Deploy stage only runs on success

---

# ARCHITECTURE & DESIGN

## ❓ Q34: Container vs VM

| Aspect | Container | VM |
|--------|-----------|-----|
| Size | ~MB | ~GB |
| Startup | Milliseconds | Minutes |
| OS | Shares host kernel | Full OS copy |
| Resource usage | Light | Heavy |
| Portability | Works anywhere | OS-dependent |
| Isolation | Process-level | Hardware-level |
| Example | Docker | EC2 |

---

## ❓ Q35: Dockerfile Commands

```dockerfile
FROM          # Base image to extend
RUN           # Execute commands during build
COPY          # Copy files from host to container
ADD           # Like COPY + extract tar files
ENV           # Set environment variables
WORKDIR       # Set working directory for commands
EXPOSE        # Document which ports app listens
CMD           # Default command when container starts
ENTRYPOINT    # Primary entry point (overrides CMD)
ARG           # Build-time variables
VOLUME        # Mount points for external storage
USER          # Run container as specific user
HEALTHCHECK   # Health check command
LABEL         # Metadata key-value pairs
```

---

## ❓ Q36: Dynamic Image Version in FROM

**Cannot use variable directly in FROM. Use workaround:**

```dockerfile
ARG BASE_IMAGE_VERSION=latest
FROM node:${BASE_IMAGE_VERSION}

RUN echo "Building with base image version: ${BASE_IMAGE_VERSION}"
```

**Build command:**
```bash
docker build --build-arg BASE_IMAGE_VERSION=18-alpine -t app:1.0 .
```

---

## Summary Table

| Concept | What It Is | Example |
|---------|-----------|---------|
| Desired Count | Target pod count | 5 replicas |
| Minimum Count | Guaranteed availability | minReplicas: 2 |
| Taints | Node-level restriction | NoSchedule |
| Tolerations | Pod permission on tainted node | tolerationSeconds: 300 |
| Service | Stable endpoint for pods | ClusterIP: 10.0.0.1 |
| kube-proxy | Programs kernel routing | iptables, IPVS |
| PV | Actual storage resource | 10GB NFS |
| PVC | Request for storage | "I need 10GB" |
| Ingress | Expose app externally | ALB controller |
| CloudFront | CDN caching | Cache + invalidate |
| VPC Endpoint | Private S3 access | No NAT needed |
| KMS | Encryption service | Data at rest |

---

**Last Updated:** January 29, 2026  
**Total Questions:** 36  
**Total Topics:** 5
