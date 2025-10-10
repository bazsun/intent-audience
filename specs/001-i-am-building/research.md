# Research: ML Intent-Based Audience Pipeline Technology Stack

**Created**: 2025-10-10  
**Purpose**: Resolve technical uncertainties identified in plan.md Technical Context

## Technology Stack Decisions

### Language/Version
**Decision**: Python 3.11+  
**Rationale**: Optimal balance of ML ecosystem dominance, development velocity, and production performance. While slower than Rust for raw compute, ML workloads leverage C/C++ optimized libraries (NumPy, TensorFlow) under the hood. Python maintains ~30% share on GitHub for AI/ML with unmatched library ecosystem.  
**Alternatives Considered**: Rust (rejected due to steep learning curve, limited ML ecosystem despite 15ms vs 20ms response time advantage)

### Primary Dependencies
**Decision**: TensorFlow 2.x + Scikit-learn + FastAPI  
**Rationale**: 
- **TensorFlow**: Best for large-scale production deployment, 50% faster on NVIDIA GPUs, designed for scalability
- **Scikit-learn**: Proven for traditional ML with structured retail data (e.g., Spotify's recommendation system)  
- **FastAPI**: Handles 3,000+ requests/second with sub-100ms response times, ASGI-based async design
**Alternatives Considered**: PyTorch (better for research but TensorFlow excels in production), Django REST (heavyweight ORM creates latency)

### Storage
**Decision**: Multi-database architecture - PostgreSQL 14+ (primary), MongoDB 6.x (documents), Redis 7.x (cache), MLflow + S3 (models)  
**Rationale**: 
- **PostgreSQL**: Customer demographics/transactions requiring ACID compliance, advanced indexing
- **MongoDB**: Product catalogs with flexible schema, real-time behavior tracking  
- **Redis**: Microsecond latency for <100ms p95 requirement, cache model predictions
- **MLflow**: Industry standard for ML lifecycle management, compliance tracking
**Alternatives Considered**: Single database (rejected due to performance requirements for 1M+ records)

### Testing
**Decision**: pytest + MLflow + Great Expectations + pytest-asyncio  
**Rationale**: 
- **pytest**: Core ML testing with parametrization for model validation
- **MLflow Evaluation**: Automated performance validation, A/B testing
- **Great Expectations**: Data quality monitoring across multiple sources
- **pytest-asyncio**: FastAPI-compatible concurrent testing for latency validation
**Alternatives Considered**: unittest (rejected for limited ML testing capabilities)

## Performance Architecture

### Meeting Speed Requirements (1M+ records in 5 minutes)
**Approach**: Spark cluster (4-8 nodes) for distributed processing → Feature Store → ML Pipeline → Redis Cache  
**Optimization**:
- Parallel processing with Spark distributed customer record processing
- Pre-compute customer features in Redis, refresh incrementally
- TensorFlow Serving with GPU acceleration for batch predictions
- Database sharding by geography/category

### Real-time Scoring (<100ms p95 latency)
**Approach**: FastAPI → Redis Cache → Fallback to PostgreSQL → Model Inference → Response  
**Optimization**:
- Cache-first strategy targeting 90%+ hit rate for customer features
- TensorFlow Lite models for optimized inference
- Async database connection pooling
- CDN integration for geographic distribution

## GDPR/CCPA Compliance Implementation

### Privacy-by-Design Architecture
**Technical Controls**:
- AES-256 encryption at rest, TLS 1.3 in transit
- RBAC with comprehensive audit logging
- Automated data purging with cascade delete
- Global Privacy Control (GPC) signal processing
- Differential privacy for model outputs

**Monitoring & Compliance**:
- Real-time consent tracking for marketing activities
- Automated PII scanning in datasets
- Privacy Impact Assessment automation
- Comprehensive audit trails for all data processing

## Infrastructure Decisions

### Deployment Platform
**Decision**: Kubernetes with Kubeflow  
**Rationale**: Auto-scaling based on processing volume, ML pipeline orchestration, zero-downtime deployments  
**Cost Estimate**: ~$4,000/month for infrastructure (databases + compute + ML training)

### CI/CD Pipeline
**Components**: Automated ML model validation, blue-green deployments, instant rollback capability  
**Rationale**: Ensures model quality and system reliability for production retail environment

## Implementation Roadmap
- **Phase 1 (Weeks 1-4)**: Infrastructure setup, synthetic data generation
- **Phase 2 (Weeks 5-8)**: Core ML pipeline with scikit-learn
- **Phase 3 (Weeks 9-12)**: FastAPI development, Redis integration  
- **Phase 4 (Weeks 13-16)**: Production deployment, compliance validation

## Risk Mitigation

### Technical Risks
- **Latency**: Cache-first architecture with 90%+ hit rate target
- **Scale**: Proven Spark + TensorFlow architecture used by Netflix, Uber
- **Compliance**: Privacy-by-design with automated monitoring

### Cost Management
- **Team**: Python talent readily available ($130K-$180K vs $150K-$210K for Rust)
- **Infrastructure**: Auto-scaling prevents over-provisioning
- **Development**: Mature ecosystem reduces custom development needs