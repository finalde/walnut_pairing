CREATE EXTENSION IF NOT EXISTS vector;
DROP TABLE IF EXISTS walnut_image_embedding;
DROP TABLE IF EXISTS walnut_image;
DROP TABLE IF EXISTS walnut;

CREATE TABLE walnut (
    id TEXT PRIMARY KEY,
    description text not null,
    created_at TIMESTAMP DEFAULT NOW() not null,
    created_by TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() not null,
    updated_by TEXT NOT NULL
);

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

CREATE TABLE walnut_image_embedding (
    id BIGSERIAL PRIMARY KEY,
    image_id BIGINT NOT NULL,
    model_name TEXT NOT NULL,
    embedding VECTOR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() not null,
    created_by TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() not null,
    updated_by TEXT NOT NULL,

    CONSTRAINT fk_image
        FOREIGN KEY (image_id)
        REFERENCES walnut_image(id)
        ON DELETE CASCADE
);


-- Insert test data for walnut pairing system
-- This script inserts sample data into walnut, walnut_image, and walnut_image_embedding tables

-- Helper function to generate a test vector (512 dimensions)
-- In practice, you would use actual embedding vectors from your model
CREATE OR REPLACE FUNCTION generate_test_vector(seed BIGINT) RETURNS vector(512) AS $$
DECLARE
    result real[];
    i INTEGER;
BEGIN
    -- Generate a simple test vector with values based on seed
    -- This creates a deterministic vector for testing purposes
    result := ARRAY[]::real[];
    FOR i IN 1..512 LOOP
        result := array_append(result, (0.1 * (seed + i) / 512.0)::real);
    END LOOP;
    RETURN result::vector(512);
END;
$$ LANGUAGE plpgsql;

-- Insert test walnuts
INSERT INTO walnut (id, description, created_by, updated_by) VALUES
    ('WALNUT-001', 'Premium grade walnut from batch A', 'system', 'system'),
    ('WALNUT-002', 'Standard grade walnut from batch B', 'system', 'system');

-- Insert test walnut images (6 sides for each walnut)
-- Note: image_path values are examples - adjust to match your actual image paths
INSERT INTO walnut_image (walnut_id, side, image_path, width, height, checksum, created_by, updated_by) VALUES
    -- WALNUT-001 images
    ('WALNUT-001', 'front', '/images/0001/0001_F_1.jpg', 1920, 1080, 'abc123def456', 'system', 'system'),
    ('WALNUT-001', 'back', '/images/0001/0001_B_1.jpg', 1920, 1080, 'def456ghi789', 'system', 'system'),
    ('WALNUT-001', 'left', '/images/0001/0001_L_1.jpg', 1920, 1080, 'ghi789jkl012', 'system', 'system'),
    ('WALNUT-001', 'right', '/images/0001/0001_R_1.jpg', 1920, 1080, 'jkl012mno345', 'system', 'system'),
    ('WALNUT-001', 'top', '/images/0001/0001_T_1.jpg', 1920, 1080, 'mno345pqr678', 'system', 'system'),
    ('WALNUT-001', 'down', '/images/0001/0001_D_1.jpg', 1920, 1080, 'pqr678stu901', 'system', 'system'),
    
    -- WALNUT-002 images
    ('WALNUT-002', 'front', '/images/0002/0002_F_1.jpg', 1920, 1080, 'xyz123abc456', 'system', 'system'),
    ('WALNUT-002', 'back', '/images/0002/0002_B_1.jpg', 1920, 1080, 'abc456def789', 'system', 'system'),
    ('WALNUT-002', 'left', '/images/0002/0002_L_1.jpg', 1920, 1080, 'def789ghi012', 'system', 'system'),
    ('WALNUT-002', 'right', '/images/0002/0002_R_1.jpg', 1920, 1080, 'ghi012jkl345', 'system', 'system'),
    ('WALNUT-002', 'top', '/images/0002/0002_T_1.jpg', 1920, 1080, 'jkl345mno678', 'system', 'system'),
    ('WALNUT-002', 'down', '/images/0002/0002_D_1.jpg', 1920, 1080, 'mno678pqr901', 'system', 'system');

-- Insert test walnut image embeddings (one-to-one with images)
-- Using the helper function to generate test vectors
-- In practice, these would be actual embeddings from your embedding service
INSERT INTO walnut_image_embedding (image_id, model_name, embedding, created_by, updated_by)
SELECT 
    wi.id,
    'resnet50-imagenet',
    generate_test_vector(wi.id),
    'system',
    'system'
FROM walnut_image wi
ORDER BY wi.id;

-- Clean up the helper function (optional - you can keep it if you want to reuse it)
DROP FUNCTION IF EXISTS generate_test_vector(BIGINT);

