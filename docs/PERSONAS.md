# WFC Persona Library

> **Complete reference of expert personas available for consensus reviews**

## Overview

WFC includes **54 expert personas** across **9 specialized panels**. Each persona brings unique expertise, perspective, and focus areas to code reviews.

## Panel Structure

### 1. Engineering Panel (11 personas)

**Purpose**: Software engineering specialists across languages and stacks

| ID | Name | Primary Skills | Best For |
|----|------|---------------|----------|
| `BACKEND_PYTHON_SENIOR` | Senior Python Backend Engineer | Python, FastAPI, SQLAlchemy, async | Python APIs, backend services |
| `BACKEND_NODE_SENIOR` | Senior Node.js Backend Engineer | Node.js, Express, TypeScript, async | Node.js APIs, real-time systems |
| `BACKEND_GO_SENIOR` | Senior Go Backend Engineer | Go, concurrency, microservices | Go services, high-performance backends |
| `BACKEND_RUST_EXPERT` | Rust Systems Engineer | Rust, memory safety, performance | Systems programming, Rust services |
| `BACKEND_JAVA_SENIOR` | Senior Java Backend Engineer | Java, Spring Boot, JPA | Enterprise Java, microservices |
| `FRONTEND_REACT_EXPERT` | Frontend React Expert | React, TypeScript, hooks, state | React applications, component design |
| `FRONTEND_VUE_EXPERT` | Frontend Vue Expert | Vue 3, Composition API, Pinia | Vue applications, reactive patterns |
| `FRONTEND_ANGULAR_EXPERT` | Frontend Angular Expert | Angular, RxJS, TypeScript, DI | Enterprise frontends, Angular apps |
| `MOBILE_IOS_EXPERT` | iOS Development Expert | Swift, SwiftUI, Combine | iOS applications, Apple platforms |
| `MOBILE_ANDROID_EXPERT` | Android Development Expert | Kotlin, Jetpack Compose, Android SDK | Android applications |
| `FULLSTACK_GENERALIST` | Full-Stack Generalist Engineer | Frontend + Backend, integration | End-to-end features, integration tasks |

### 2. Security Panel (8 personas)

**Purpose**: Security specialists across application, infrastructure, and compliance

| ID | Name | Primary Skills | Best For |
|----|------|---------------|----------|
| `APPSEC_SPECIALIST` | Application Security Specialist | OWASP Top 10, auth/authz, XSS/CSRF | Application security, vulnerability detection |
| `API_SECURITY_SPECIALIST` | API Security Specialist | OAuth, JWT, OWASP API Top 10 | API authentication, authorization |
| `INFRASEC_ENGINEER` | Infrastructure Security Engineer | Network security, firewalls, IDS | Infrastructure security, network hardening |
| `CLOUD_SECURITY_AWS` | AWS Cloud Security Specialist | AWS IAM, Security Groups, KMS | AWS security, cloud infrastructure |
| `PENTESTER` | Penetration Testing Specialist | Pen testing, vulnerability assessment | Security testing, attack vectors |
| `COMPLIANCE_AUDITOR` | Compliance Auditor | SOC2, ISO 27001, GDPR, HIPAA | Regulatory compliance, audits |
| `SECRETS_MANAGEMENT_EXPERT` | Secrets Management Expert | Vault, Secrets Manager, rotation | Credential management, secret detection |
| `CRYPTOGRAPHY_EXPERT` | Cryptography Expert | Encryption, TLS, key management | Cryptographic implementations |

### 3. Architecture Panel (7 personas)

**Purpose**: Architecture and design specialists

| ID | Name | Primary Skills | Best For |
|----|------|---------------|----------|
| `SOLUTIONS_ARCHITECT` | Solutions Architect | System design, scalability, cloud | Enterprise architecture, system design |
| `API_DESIGNER` | API Design Specialist | REST, GraphQL, API patterns | API design, contract definition |
| `MICROSERVICES_ARCHITECT` | Microservices Architect | Service decomposition, boundaries | Microservices design, service boundaries |
| `DDD_EXPERT` | Domain-Driven Design Expert | Bounded contexts, aggregates | Domain modeling, DDD patterns |
| `EVENT_DRIVEN_ARCHITECT` | Event-Driven Architecture Specialist | Event sourcing, CQRS, Kafka | Event-driven systems, messaging |
| `CLOUD_ARCHITECT` | Cloud Architecture Specialist | AWS/Azure/GCP, IaC, scalability | Cloud architecture, infrastructure |
| `INTEGRATION_ARCHITECT` | Integration Architecture Specialist | ESB, API gateway, integration patterns | System integration, API management |

### 4. Quality Panel (8 personas)

**Purpose**: Quality assurance and testing specialists

| ID | Name | Primary Skills | Best For |
|----|------|---------------|----------|
| `PERF_TESTER` | Performance Testing Specialist | Load testing, profiling, benchmarking | Performance testing, optimization |
| `LOAD_TESTING_SPECIALIST` | Load Testing Specialist | k6, JMeter, capacity planning | Load testing, scalability validation |
| `TEST_AUTOMATION_EXPERT` | Test Automation Expert | Selenium, Cypress, test frameworks | Test automation, E2E testing |
| `QA_AUTOMATION_LEAD` | QA Automation Lead | Test strategy, CI/CD testing | QA strategy, test automation leadership |
| `CODE_REVIEWER` | Code Review Specialist | Code quality, refactoring, clean code | Code reviews, maintainability |
| `CHAOS_ENGINEER` | Chaos Engineering Specialist | Chaos Monkey, resilience, failure modes | Resilience testing, chaos engineering |
| `ACCESSIBILITY_TESTER` | Accessibility QA Specialist | WCAG testing, screen readers | Accessibility testing, a11y compliance |
| `SECURITY_TESTER` | Security QA Specialist | SAST, DAST, security scanning | Security testing, vulnerability scanning |

### 5. Data Panel (4 personas)

**Purpose**: Data engineering and architecture specialists

| ID | Name | Primary Skills | Best For |
|----|------|---------------|----------|
| `DB_ARCHITECT_SQL` | SQL Database Architect | PostgreSQL, query optimization, schema design | SQL databases, query optimization |
| `NOSQL_ARCHITECT` | NoSQL Architecture Specialist | MongoDB, Redis, DynamoDB | NoSQL databases, data modeling |
| `DATA_ENGINEER` | Data Engineer | ETL, data pipelines, Spark | Data pipelines, ETL processes |
| `ML_ENGINEER` | ML Engineering Specialist | ML ops, model deployment, Python | ML systems, model deployment |

### 6. Product Panel (3 personas)

**Purpose**: Product and user experience specialists

| ID | Name | Primary Skills | Best For |
|----|------|---------------|----------|
| `DX_SPECIALIST` | Developer Experience Specialist | API design, SDK, documentation | Developer-facing products, APIs |
| `TECHNICAL_PM` | Technical Product Manager | Requirements, feasibility, user value | Product features, requirement clarity |
| `UX_RESEARCHER` | UX Research Specialist | User research, usability, accessibility | User experience, usability testing |

### 7. Operations Panel (4 personas)

**Purpose**: Operations and reliability specialists

| ID | Name | Primary Skills | Best For |
|----|------|---------------|----------|
| `SRE_SPECIALIST` | SRE Specialist | Observability, SLOs, incident response | Production reliability, monitoring |
| `PLATFORM_ENGINEER` | Platform Engineer | Kubernetes, platform services | Platform engineering, infrastructure |
| `DEVOPS_ENGINEER` | DevOps Engineer | CI/CD, automation, IaC | DevOps practices, automation |
| `OBSERVABILITY_ENGINEER` | Observability Engineer | Metrics, logging, tracing | Observability, monitoring systems |

### 8. Domain Experts Panel (5 personas)

**Purpose**: Industry domain specialists

| ID | Name | Primary Skills | Best For |
|----|------|---------------|----------|
| `FINTECH_PAYMENTS` | Fintech/Payments Expert | Payment processing, PCI-DSS, idempotency | Payment systems, financial services |
| `HEALTHCARE_HIPAA` | Healthcare/HIPAA Specialist | HIPAA, PHI, healthcare workflows | Healthcare applications, medical data |
| `ECOMMERCE_EXPERT` | E-commerce Specialist | Shopping carts, inventory, checkout | E-commerce platforms, retail |
| `GAMING_EXPERT` | Gaming/Real-time Systems Expert | Real-time, game loops, latency | Gaming, real-time systems |
| `IOT_EMBEDDED_EXPERT` | IoT/Embedded Specialist | Embedded systems, constrained devices | IoT, embedded development |

### 9. Specialists Panel (4 personas)

**Purpose**: Niche specializations

| ID | Name | Primary Skills | Best For |
|----|------|---------------|----------|
| `ACCESSIBILITY_WCAG` | Accessibility (WCAG) Expert | WCAG 2.2 AA/AAA, ARIA, screen readers | Accessibility compliance, inclusive design |
| `PERFORMANCE_OPTIMIZATION_GURU` | Performance Optimization Guru | Profiling, optimization, algorithms | Performance optimization, bottlenecks |
| `I18N_EXPERT` | Internationalization Specialist | i18n, l10n, Unicode, translations | International applications, localization |
| `TECH_DEBT_ANALYST` | Technical Debt Analyst | Refactoring, debt analysis, metrics | Technical debt, code health |

## Using Personas

### Automatic Selection

WFC automatically selects 5 personas based on:
- Tech stack (extracted from files)
- Task complexity
- Review properties (SECURITY, PERFORMANCE, etc.)
- Task type (api-implementation, refactoring, etc.)

### Manual Override

Select specific personas:
```
/wfc:consensus-review TASK-001 --personas APPSEC_SPECIALIST,DB_ARCHITECT_SQL,BACKEND_PYTHON_SENIOR
```

### Persona Traits

Each persona has:
- **Skills**: Technical expertise areas
- **Lens**: What they focus on during reviews
- **Personality**: Communication style and risk tolerance
- **Selection Criteria**: When they're automatically selected

## Adding Custom Personas

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add your own personas to extend the library.

---

**Current Count**: 54 personas
**Last Updated**: 2026-02-10
