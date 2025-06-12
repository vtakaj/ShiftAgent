-- ==============================================================================
-- Shift Scheduler Database Initialization
-- ==============================================================================
-- This script sets up the initial database schema for the Shift Scheduler
-- Currently using file-based storage, but this prepares for future DB storage

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Future table structures can be added here when migrating from file storage
-- For now, this file ensures the database is properly initialized

-- Log initialization
\echo 'Shift Scheduler database initialized successfully'