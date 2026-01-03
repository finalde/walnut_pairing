-- Create extension for vector support
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS walnut_comparison;
DROP TABLE IF EXISTS walnut_image_embedding;
DROP TABLE IF EXISTS walnut_image;
DROP TABLE IF EXISTS walnut;

-- Create walnut table
CREATE TABLE walnut (
    id TEXT PRIMARY KEY,
    description text not null,
    width_mm DOUBLE PRECISION,
    height_mm DOUBLE PRECISION,
    thickness_mm DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW() not null,
    created_by TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() not null,
    updated_by TEXT NOT NULL
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
    walnut_width_px DOUBLE PRECISION NOT NULL,
    walnut_height_px DOUBLE PRECISION NOT NULL,
    camera_distance_mm DOUBLE PRECISION NOT NULL,
    focal_length_px DOUBLE PRECISION NOT NULL,
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

-- Create walnut_comparison table
CREATE TABLE walnut_comparison (
    id BIGSERIAL PRIMARY KEY,
    walnut_id TEXT NOT NULL,
    compared_walnut_id TEXT NOT NULL,
    -- Basic similarity metrics
    width_diff_mm DOUBLE PRECISION NOT NULL,
    height_diff_mm DOUBLE PRECISION NOT NULL,
    thickness_diff_mm DOUBLE PRECISION NOT NULL,
    basic_similarity DOUBLE PRECISION NOT NULL,
    width_weight DOUBLE PRECISION NOT NULL,
    height_weight DOUBLE PRECISION NOT NULL,
    thickness_weight DOUBLE PRECISION NOT NULL,
    -- Advanced similarity metrics (from embeddings)
    front_embedding_score DOUBLE PRECISION,
    back_embedding_score DOUBLE PRECISION,
    left_embedding_score DOUBLE PRECISION,
    right_embedding_score DOUBLE PRECISION,
    top_embedding_score DOUBLE PRECISION,
    down_embedding_score DOUBLE PRECISION,
    advanced_similarity DOUBLE PRECISION,
    -- Final combined similarity
    final_similarity DOUBLE PRECISION NOT NULL,
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW() not null,
    created_by TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() not null,
    updated_by TEXT NOT NULL,

    CONSTRAINT uq_walnut_comparison UNIQUE (walnut_id, compared_walnut_id),
    CONSTRAINT fk_walnut
        FOREIGN KEY (walnut_id)
        REFERENCES walnut(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_compared_walnut
        FOREIGN KEY (compared_walnut_id)
        REFERENCES walnut(id)
        ON DELETE CASCADE
);
