-- InkQ Dev Database Reset Script
-- WARNING: This script will DROP ALL DATA in the public schema
-- Only use this in development environments!

-- Drop and recreate the public schema
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

-- Grant permissions
GRANT ALL ON SCHEMA public TO inkq;
GRANT ALL ON SCHEMA public TO public;

-- Recreate common extensions if needed
-- Uncomment if your project uses these:
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";

