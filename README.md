# High-Performance Revocable JWT Authentication Service

A production-ready, security-hardened authentication microservice built with **FastAPI**, **SQLAlchemy**, and **Redis**. This service bridges the gap between the stateless scalability of JSON Web Tokens (JWTs) and the security requirement of instant session revocation (logout) by implementing a high-speed, TTL-backed Redis denylist.

---

## 🏗️ System Architecture & Design

Architecting an authentication system requires balancing stateless efficiency with secure state management. Standard JWT implementations are unguided missiles—once signed, a token remains valid until it naturally expires, leaving systems vulnerable if a token is compromised.

This service utilizes a **Hybrid State Model**:

* **Stateless by Default:** Standard API requests verify token signatures locally using a public/private key or shared secret, hitting $O(1)$ verification speeds without querying the primary database.
* **Stateful on Revocation:** Upon logging out, the token's remaining lifespan is calculated, and its signature is pushed into an in-memory **Redis** cache. A lightweight middleware intercepts incoming requests to check this denylist before processing the token.

```
                  +----------------------------------+
                  |       Incoming API Request       |
                  +----------------------------------+
                                   |
                                   v
                  +----------------------------------+
                  |   SlowAPI Client Rate Limiter    | ---> [Abuse Blocked: 429]
                  +----------------------------------+
                                   |
                                   v
                  +----------------------------------+
                  |      Redis Blacklist Check       | ---> [Token Revoked: 401]
                  +----------------------------------+
                                   |
                                   v
                  +----------------------------------+
                  |     JWT Signature Validation     | ---> [Malformed Token: 401]
                  +----------------------------------+
                                   |
                                   v
                  +----------------------------------+
                  |  Application Logic & SQL Database|
                  +----------------------------------+

```

---

## 🛠️ The Stack & Engineering "Why"

Every tool in this stack was chosen to prioritize throughput, minimize disk I/O bottlenecks, and maintain strict security boundaries.

### FastAPI

Chosen over heavy frameworks like Django or synchronous alternatives like Flask. FastAPI natively handles asynchronous execution loops, allowing the service to manage thousands of concurrent authentications per second without thread blocking. Its automatic OpenAPI documentation generation ensures clear communication for frontend integration.

### Redis

Used as the dedicated session-invalidation layer. Relational databases are built for persistent storage, but checking a SQL database on every single API request to see if a token is blacklisted ruins horizontal scalability. Redis keeps the denylist entirely in RAM, offering sub-millisecond lookup times.

Furthermore, Redis supports native **Time-To-Live (TTL)**. By calculating the exact remaining duration of a logged-out token ($TTL = exp - now$), we instruct Redis to self-delete the entry the moment the token expires naturally. This keeps the memory footprint lean without requiring background cleanup crons.

### SlowAPI (Rate Limiting)

Brute-force protection is implemented at the application entry point using a sliding-window counter linked to the client's remote IP address. The `/auth/login` endpoint is limited to 5 attempts per minute, shedding malicious bot traffic before it consumes downstream application resources or database connection pools.

### Pydantic V2 & Passlib

Data formatting and integrity are enforced at the type level. Pydantic models intercept malformed data or weak passwords before data parsing finishes. Passwords are securely hashed using memory-hard cryptography through `passlib`, raising the hardware cost for attackers trying to execute offline rainbow-table attacks.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.13+
* Docker & Docker Compose

### Environment Configuration

Create a `.env` file in the root directory:

```env
SECRET_KEY=your_super_secret_high_entropy_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./auth.db

```

### Local Deployment

1. **Spin up Infrastructure:** Start the Redis container running in the background.
```bash
docker-compose up -d

```


2. **Install Dependencies:**
```bash
pip install -r requirements.txt

```


3. **Run the Application:** Start the Uvicorn development server.
```bash
uvicorn app.main:app --reload

```


4. **Access the Documentation:** Open your browser to [http://127.0.0.1:8000/docs](https://www.google.com/search?q=http://127.0.0.1:8000/docs) to view interactive Swagger docs.

---

## 🧪 Testing

The system implements strict testing boundaries via **Pytest** and **HTTPX**. Tests are completely decoupled from production environments by injecting an ephemeral, in-memory SQLite database instance during the test life cycle.

Run the test suite:

```bash
python -m pytest

```

---

## 🔮 Future Roadmap & Scalability Improvements

While highly optimized for standalone operation, migrating this architecture to support massive enterprise traffic requires the following architectural evolutions:

### 1. Migrating to Asynchronous Postgres (`asyncpg`)

Currently, the relational data layer utilizes a synchronous SQLite driver wrapped in SQLAlchemy. To maximize FastAPI's non-blocking capabilities under heavy concurrent load, the system should be migrated to **PostgreSQL** using `asyncpg`. This prevents the Python worker process from idling while waiting for database disk writes during user registration.

### 2. Offloading the Denylist to an API Gateway

Checking the Redis denylist inside the Python application layer still requires an execution context switch. For global scale, this lookup can be pushed upstream to an edge proxy or API Gateway (e.g., **Kong** or **Nginx** using an openresty Lua script). The gateway directly reads from the shared Redis cluster and drops blacklisted requests at the network perimeter, freeing up 100% of the FastAPI application capacity for valid requests.

### 3. Distributed Redis Clusters

To handle global availability across multi-region deployments, a single Redis node introduces a single point of failure and cross-region latency. Transitioning to **Redis ElastiCache with Replication Groups** ensures that when a token is blacklisted in US-East, it replicates globally within milliseconds, neutralizing replay attacks globally.
