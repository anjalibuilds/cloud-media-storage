# Cloud Based Media File Storage Service

## ER Diagram

```mermaid
erDiagram

    USERS {
        uuid id PK
        varchar email UK
        text password_hash
        varchar full_name
        varchar google_id UK
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    FOLDERS {
        uuid id PK
        varchar name
        uuid owner_id FK
        uuid parent_id FK
        boolean is_deleted
        timestamp deleted_at
        timestamp created_at
        timestamp updated_at
    }

    FILES {
        uuid id PK
        varchar name
        varchar original_name
        varchar mime_type
        bigint size
        text storage_path UK
        uuid owner_id FK
        uuid folder_id FK
        boolean is_deleted
        timestamp deleted_at
        boolean is_starred
        integer current_version
        timestamp created_at
        timestamp updated_at
    }

    FILE_VERSIONS {
        uuid id PK
        uuid file_id FK
        integer version_number
        text storage_path
        bigint size
        varchar mime_type
        uuid created_by FK
        timestamp created_at
    }

    SHARES {
        uuid id PK
        uuid file_id FK
        uuid folder_id FK
        uuid owner_id FK
        uuid shared_with_user_id FK
        enum role
        timestamp created_at
    }

    LINK_SHARES {
        uuid id PK
        uuid file_id FK
        uuid folder_id FK
        varchar token UK
        text password_hash
        timestamp expires_at
        boolean is_active
        uuid created_by FK
        timestamp created_at
    }

    STARS {
        uuid id PK
        uuid user_id FK
        uuid file_id FK
        timestamp created_at
    }

    ACTIVITIES {
        uuid id PK
        uuid user_id FK
        uuid file_id FK
        uuid folder_id FK
        enum activity_type
        jsonb metadata
        timestamp created_at
    }

    USERS ||--o{ FOLDERS : owns
    USERS ||--o{ FILES : owns
    USERS ||--o{ FILE_VERSIONS : creates

    FOLDERS ||--o{ FOLDERS : contains
    FOLDERS ||--o{ FILES : contains

    FILES ||--o{ FILE_VERSIONS : has
    FILES ||--o{ SHARES : shared
    FOLDERS ||--o{ SHARES : shared

    USERS ||--o{ SHARES : receives
    USERS ||--o{ SHARES : creates

    FILES ||--o{ LINK_SHARES : exposes
    FOLDERS ||--o{ LINK_SHARES : exposes

    USERS ||--o{ STARS : creates
    FILES ||--o{ STARS : starred

    USERS ||--o{ ACTIVITIES : performs
    FILES ||--o{ ACTIVITIES : generates
    FOLDERS ||--o{ ACTIVITIES : generates