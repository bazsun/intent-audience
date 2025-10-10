# ML Intent-Based Audience Pipeline Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          ML Intent-Based Audience Pipeline                        │
│                              Architecture Overview                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────────────────────────────────────────────┐
│   USERS         │    │                   APPLICATION LAYER                      │
├─────────────────┤    ├─────────────────────────────────────────────────────────┤
│ Marketing Mgr   │────┤                   FastAPI Server                        │
│ Data Scientist  │    │            (src/api/)                                   │
│ Data Engineer   │    │  ┌───────────────┐ ┌──────────────┐ ┌─────────────────┐│
└─────────────────┘    │  │   Audiences   │ │ Intent Scores│ │ Synthetic Data  ││
                       │  │   /audiences  │ │ /intent-scores│ │ /synthetic-data ││
                       │  └───────────────┘ └──────────────┘ └─────────────────┘│
                       └─────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SERVICE LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │ Audience        │ │ Scoring         │ │ Quality         │ │ Synthetic Data  ││
│ │ Generation      │ │ Service         │ │ Validation      │ │ Generation      ││
│ │ (src/services/  │ │ (src/services/  │ │ (src/services/  │ │ (src/data/      ││
│ │  audience/)     │ │  scoring/)      │ │  quality/)      │ │  synthetic/)    ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ML/DATA LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │ Intent Models   │ │ Feature         │ │ Data Loaders    │ │ Model Training  ││
│ │ (TensorFlow/    │ │ Engineering     │ │ & Validation    │ │ & Evaluation    ││
│ │  Scikit-learn)  │ │ (Pandas/Spark)  │ │ (Great Expect.) │ │ (MLflow)        ││
│ │ (src/models/)   │ │ (src/data/prep/)│ │ (src/data/load/)│ │ (src/models/)   ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              STORAGE LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│ │ PostgreSQL      │ │ MongoDB         │ │ Redis Cache     │ │ MLflow/S3       ││
│ │ - Customers     │ │ - Product Cats  │ │ - Intent Scores │ │ - Models        ││
│ │ - Transactions  │ │ - Campaigns     │ │ - Features      │ │ - Experiments   ││
│ │ - Demographics  │ │ - Config Data   │ │ - Session Data  │ │ - Artifacts     ││
│ │ (ACID Compliance│ │ (Flexible Schema│ │ (Sub-100ms)     │ │ (Versioning)    ││
│ │  for consistency)│ │  for analytics) │ │                 │ │                 ││
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

```
                            User Story Workflows
                            
US1: Create Intent-Based Audience
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Customer Data   │───▶│ Feature         │───▶│ Intent Model    │
│ (Demographics,  │    │ Engineering     │    │ (TensorFlow/    │
│  Transactions,  │    │ (Transaction    │    │  Scikit-learn)  │
│  Marketing)     │    │  patterns, demo │    │ Predicts 30-day │
└─────────────────┘    │  fit, engagement│    │ purchase prob   │
                       └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Threshold       │◀───│ Intent Scores   │
                       │ Adjustment      │    │ (0.0 - 1.0)     │
                       │ (Min 1000 cust) │    │ Per category    │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Audience        │◀───│ Customer        │
                       │ Generation      │    │ Ranking         │
                       │ (Collection of  │    │ (By score)      │
                       │  high-intent    │    │                 │
                       │  customers)     │    │                 │
                       └─────────────────┘    └─────────────────┘

US2: Validate Audience Quality
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Generated       │───▶│ Quality Metrics │───▶│ Performance     │
│ Audience        │    │ Calculator      │    │ Dashboard       │
│ (From US1)      │    │ - Size          │    │ - Conversion    │
└─────────────────┘    │ - Avg Score     │    │ - Demographics  │
                       │ - Distribution  │    │ - Historical    │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Threshold       │
                       │ Adjustment      │
                       │ (Real-time      │
                       │  recalculation) │
                       └─────────────────┘

US3: Generate Synthetic Training Data
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Data Generation │───▶│ Correlation     │───▶│ Quality         │
│ Requirements    │    │ Engine          │    │ Validation      │
│ - Customer count│    │ (Maintains      │    │ (Statistical    │
│ - Time range    │    │  realistic      │    │  analysis for   │
│ - Categories    │    │  relationships) │    │  realism)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Customer        │    │ Transaction     │    │ Marketing       │
│ Generator       │    │ Generator       │    │ Activity        │
│ (Demographics,  │    │ (Purchase       │    │ Generator       │
│  Geography)     │    │  patterns)      │    │ (Engagement)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Detail Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API ENDPOINTS                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ POST /audiences          │ GET /audiences/{id}      │ PATCH /audiences/{id}    │
│ POST /intent-scores      │ GET /intent-scores/{id}  │ GET /health              │
│ POST /synthetic-data     │ GET /audiences           │ GET /audiences/{id}/cust │
└─────────────────────────────────────────────────────────────────────────────────┘
                                              │
                   ┌──────────────────────────┼──────────────────────────┐
                   │                          │                          │
                   ▼                          ▼                          ▼
┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
│    AUDIENCE SERVICE     │    │    SCORING SERVICE      │    │  SYNTHETIC DATA SERVICE │
├─────────────────────────┤    ├─────────────────────────┤    ├─────────────────────────┤
│ AudienceGenerator       │    │ CustomerScorer          │    │ DataOrchestrator        │
│ ThresholdAdjuster       │    │ RealtimeScoring         │    │ CustomerGenerator       │
│ StatusManager           │    │ BatchScoring            │    │ TransactionGenerator    │
│ QualityValidator        │    │ ScoreCache              │    │ MarketingGenerator      │
└─────────────────────────┘    └─────────────────────────┘    └─────────────────────────┘
           │                              │                              │
           ▼                              ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
│     INTENT MODELS       │    │   FEATURE ENGINEERING   │    │     DATA VALIDATION     │
├─────────────────────────┤    ├─────────────────────────┤    ├─────────────────────────┤
│ IntentPredictor         │    │ FeatureExtractor        │    │ DataQualityChecker      │
│ (TensorFlow/Sklearn)    │    │ TransactionProcessor    │    │ (Great Expectations)    │
│ CategorySpecific        │    │ DemographicProcessor    │    │ SchemaValidator         │
│ ModelTrainer            │    │ EngagementProcessor     │    │ CorrelationValidator    │
│ PerformanceEvaluator    │    │ GeographicProcessor     │    │ BiasDetector            │
└─────────────────────────┘    └─────────────────────────┘    └─────────────────────────┘
           │                              │                              │
           ▼                              ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA MODELS                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Customer │ Transaction │ ProductCategory │ IntentScore │ Audience │ Marketing │
│          │             │                 │             │          │ Activity  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Storage Architecture (CQRS Pattern)

```
                              Command Side (Writes)
                                      │
                                      ▼
                          ┌─────────────────────────┐
                          │      PostgreSQL         │
                          │   (Primary Database)    │
                          ├─────────────────────────┤
                          │ • Customer Demographics │
                          │ • Transaction Records   │
                          │ • Loyalty Data          │
                          │ • Audit Logs           │
                          │ • ACID Compliance      │
                          │ • Referential Integrity│
                          └─────────────────────────┘
                                      │
                              Event Synchronization
                                      │
                                      ▼
                              Query Side (Reads)
                        ┌─────────────┬─────────────┐
                        ▼             ▼             ▼
           ┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────┐
           │      MongoDB        │ │    Redis Cache  │ │   MLflow/S3     │
           │  (Document Store)   │ │  (Performance)  │ │ (ML Artifacts)  │
           ├─────────────────────┤ ├─────────────────┤ ├─────────────────┤
           │ • Product Catalogs  │ │ • Intent Scores │ │ • Model Files   │
           │ • Campaign Data     │ │ • Feature Cache │ │ • Experiments   │
           │ • Quality Metrics   │ │ • Session Data  │ │ • Training Data │
           │ • Flexible Schema   │ │ • Sub-100ms     │ │ • Hyperparams   │
           │ • Analytics         │ │ • 90%+ Hit Rate │ │ • Version Track │
           └─────────────────────┘ └─────────────────┘ └─────────────────┘
```

## Performance Architecture

```
                              Load Balancing & Scaling
                                      │
                   ┌──────────────────┼──────────────────┐
                   │                  │                  │
                   ▼                  ▼                  ▼
           ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
           │   API Instance  │ │   API Instance  │ │   API Instance  │
           │      (FastAPI)  │ │      (FastAPI)  │ │      (FastAPI)  │
           └─────────────────┘ └─────────────────┘ └─────────────────┘
                   │                  │                  │
                   └──────────────────┼──────────────────┘
                                      │
                   ┌──────────────────┼──────────────────┐
                   │                  │                  │
                   ▼                  ▼                  ▼
           ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
           │     Cache       │ │  ML Inference   │ │  Data Pipeline  │
           │    Layer        │ │     Service     │ │   (Spark Cluster│
           │ (Redis Cluster) │ │  (GPU-enabled)  │ │   for 1M+ recs) │
           └─────────────────┘ └─────────────────┘ └─────────────────┘
                   │                  │                  │
                   │                  │                  │
                   └──────────┬───────┴──────────────────┘
                              │
                              ▼
                   ┌─────────────────────────┐
                   │   Performance Goals     │
                   ├─────────────────────────┤
                   │ • <5 min: 1M customers  │
                   │ • <100ms p95: Scoring   │
                   │ • <200ms: API response  │
                   │ • 1000+ min audience    │
                   │ • 15%+ conversion lift  │
                   └─────────────────────────┘
```

## Security & Compliance Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PRIVACY BY DESIGN                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   Data Input    │───▶│  Anonymization  │───▶│   Storage       │             │
│  │                 │    │                 │    │                 │             │
│  │ • Email Hashing │    │ • PII Removal   │    │ • Encrypted     │             │
│  │ • Postcode Only │    │ • Aggregation   │    │ • Access Control│             │
│  │ • No Street Addr│    │ • Differential  │    │ • Audit Logs    │             │
│  │ • Consent Flags │    │   Privacy       │    │ • Retention     │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   Synthetic     │    │   Bias Testing  │    │   Compliance    │             │
│  │   Data Gen      │    │                 │    │   Monitoring    │             │
│  │                 │    │ • Algorithmic   │    │                 │             │
│  │ • No Real PII   │    │   Fairness      │    │ • GDPR Rights   │             │
│  │ • Realistic     │    │ • Demo Balance  │    │ • Data Deletion │             │
│  │   Patterns      │    │ • Performance   │    │ • Consent Track │             │
│  │ • POC Safe      │    │   Parity        │    │ • Privacy Impact│             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
                              Kubernetes Orchestration
                                      │
                   ┌──────────────────┼──────────────────┐
                   │                  │                  │
                   ▼                  ▼                  ▼
           ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
           │   Staging       │ │   Canary        │ │   Production    │
           │   Environment   │ │   Environment   │ │   Environment   │
           ├─────────────────┤ ├─────────────────┤ ├─────────────────┤
           │ • Full Testing  │ │ • A/B Testing   │ │ • Live Traffic  │
           │ • Model Validation│ │ • 5% Traffic   │ │ • 95% Traffic   │
           │ • Synthetic Data│ │ • Model Comp    │ │ • Full Scale    │
           └─────────────────┘ └─────────────────┘ └─────────────────┘
                   │                  │                  │
                   └──────────────────┼──────────────────┘
                                      │
                                      ▼
                          ┌─────────────────────────┐
                          │     Monitoring &        │
                          │     Observability       │
                          ├─────────────────────────┤
                          │ • Prometheus Metrics    │
                          │ • Grafana Dashboards    │
                          │ • Model Performance     │
                          │ • Business KPIs         │
                          │ • Error Tracking        │
                          │ • Cost Optimization     │
                          └─────────────────────────┘
```

## Key Architectural Decisions

### Multi-Database Strategy (CQRS)
- **PostgreSQL**: ACID compliance for critical customer/transaction data
- **MongoDB**: Flexible schema for product catalogs and analytics
- **Redis**: Sub-100ms caching for real-time intent scoring
- **MLflow/S3**: Model versioning and experiment tracking

### Microservices by User Story
- **Audience Service**: US1 - Core audience generation
- **Quality Service**: US2 - Validation and metrics
- **Synthetic Data Service**: US3 - Privacy-compliant test data

### ML Pipeline Architecture
- **Feature Store**: Centralized feature management
- **Model Registry**: Versioned model artifacts with MLflow
- **Batch + Real-time**: Spark for large datasets, Redis for low-latency scoring

### Privacy & Compliance
- **Synthetic Data First**: POC development without real PII
- **Data Minimization**: Postcode-level geography, hashed emails
- **Automated Compliance**: Retention policies, deletion workflows

This architecture supports the constitutional requirements of data privacy, model reproducibility, audience validation, and performance monitoring while enabling independent development and deployment of each user story.