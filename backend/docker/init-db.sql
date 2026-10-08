-- Runs once, on first container creation, to provision the test database
-- alongside the main one (POSTGRES_DB) created automatically by the image.
CREATE DATABASE nureon_test;
