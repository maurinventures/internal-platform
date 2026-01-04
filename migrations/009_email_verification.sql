-- Migration 009: Add email verification fields to users table
-- This migration adds email verification requirement for new signups

-- Add email verification columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token_expires TIMESTAMP WITH TIME ZONE;

-- Mark existing users as verified (they were added before this requirement)
UPDATE users SET email_verified = 1 WHERE email_verified IS NULL OR email_verified = 0;

-- Add index for token lookups
CREATE INDEX IF NOT EXISTS idx_users_verification_token ON users(verification_token);
