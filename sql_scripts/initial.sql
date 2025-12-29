-- Create extension for vector support
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS walnut_image_embedding;
DROP TABLE IF EXISTS walnut_image;
DROP TABLE IF EXISTS walnut;

-- Create walnut table
CREATE TABLE walnut (
    id TEXT PRIMARY KEY,
    description text not null,
    created_at TIMESTAMP DEFAULT NOW() not null,
    created_by TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() not null,
    updated_by TEXT NOT NULL,
    length_mm DOUBLE PRECISION,
    width_mm DOUBLE PRECISION,
    height_mm DOUBLE PRECISION
);

-- Create walnut_image table
CREATE TABLE walnut_image (
    id BIGSERIAL PRIMARY KEY,
    walnut_id TEXT NOT NULL,
    side TEXT NOT NULL,
    image_path TEXT NOT NULL,
    width INT not null,
    height INT not null,
    checksum TEXT not null,
    created_at TIMESTAMP DEFAULT NOW() not null,
    created_by TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() not null,
    updated_by TEXT NOT NULL,

    CONSTRAINT uq_walnut_side UNIQUE (walnut_id, side),
    CONSTRAINT fk_walnut
        FOREIGN KEY (walnut_id)
        REFERENCES walnut(id)
        ON DELETE CASCADE
);

-- Create walnut_image_embedding table
-- Note: VECTOR(2048) matches ResNet50 embedding dimension
CREATE TABLE walnut_image_embedding (
    id BIGSERIAL PRIMARY KEY,
    image_id BIGINT NOT NULL,
    model_name TEXT NOT NULL,
    embedding VECTOR(2048) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() not null,
    created_by TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() not null,
    updated_by TEXT NOT NULL,

    CONSTRAINT fk_image
        FOREIGN KEY (image_id)
        REFERENCES walnut_image(id)
        ON DELETE CASCADE
);
