#!/bin/zsh
# =============================================================
# AWS CLI & PostgreSQL Commands for MV Internal
# =============================================================
# IMPORTANT: All --query expressions and SQL wildcards MUST be quoted
# in zsh to prevent glob expansion. Use single quotes for JMESPath.
#
# Fixed issues:
#   - [*] in --query must be quoted (zsh tries to expand * as glob)
#   - COUNT(*) in psql -c must be quoted
#   - SELECT * in psql -c must be quoted
# =============================================================

# -------------------------------------------------------------
# CONFIGURATION (from config/credentials.yaml)
# -------------------------------------------------------------
export AWS_REGION="us-east-1"
export EC2_INSTANCE_ID="i-030b974c11cf175cd"
export RDS_HOST="mv-database.cshawwjevydx.us-east-1.rds.amazonaws.com"
export RDS_DB="video_management"
export RDS_USER="postgres"
export S3_BUCKET="mv-brain"

# -------------------------------------------------------------
# EC2 COMMANDS
# -------------------------------------------------------------

# List all EC2 instances (properly quoted)
ec2_list_instances() {
    aws ec2 describe-instances \
        --region "$AWS_REGION" \
        --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' \
        --output table
}

# Get specific instance details
ec2_describe_instance() {
    local instance_id="${1:-$EC2_INSTANCE_ID}"
    aws ec2 describe-instances \
        --region "$AWS_REGION" \
        --instance-ids "$instance_id" \
        --query 'Reservations[*].Instances[*]' \
        --output json
}

# Get instance status
ec2_instance_status() {
    local instance_id="${1:-$EC2_INSTANCE_ID}"
    aws ec2 describe-instance-status \
        --region "$AWS_REGION" \
        --instance-ids "$instance_id" \
        --query 'InstanceStatuses[*].[InstanceId,InstanceState.Name,SystemStatus.Status,InstanceStatus.Status]' \
        --output table
}

# Get running instances only
ec2_running_instances() {
    aws ec2 describe-instances \
        --region "$AWS_REGION" \
        --filters "Name=instance-state-name,Values=running" \
        --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' \
        --output table
}

# -------------------------------------------------------------
# RDS COMMANDS
# -------------------------------------------------------------

# List all RDS instances
rds_list_instances() {
    aws rds describe-db-instances \
        --region "$AWS_REGION" \
        --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus,Endpoint.Address,Engine]' \
        --output table
}

# Describe specific RDS instance
rds_describe_instance() {
    local db_id="${1:-mv-database}"
    aws rds describe-db-instances \
        --region "$AWS_REGION" \
        --db-instance-identifier "$db_id" \
        --query 'DBInstances[*]' \
        --output json
}

# List all DB snapshots
rds_list_snapshots() {
    aws rds describe-db-snapshots \
        --region "$AWS_REGION" \
        --query 'DBSnapshots[*].[DBSnapshotIdentifier,DBInstanceIdentifier,Status,SnapshotCreateTime]' \
        --output table
}

# List snapshots for specific instance
rds_instance_snapshots() {
    local db_id="${1:-mv-database}"
    aws rds describe-db-snapshots \
        --region "$AWS_REGION" \
        --db-instance-identifier "$db_id" \
        --query 'DBSnapshots[*].[DBSnapshotIdentifier,Status,SnapshotCreateTime,AllocatedStorage]' \
        --output table
}

# Get latest snapshot
rds_latest_snapshot() {
    local db_id="${1:-mv-database}"
    aws rds describe-db-snapshots \
        --region "$AWS_REGION" \
        --db-instance-identifier "$db_id" \
        --query 'sort_by(DBSnapshots, &SnapshotCreateTime)[-1]' \
        --output json
}

# -------------------------------------------------------------
# S3 COMMANDS
# -------------------------------------------------------------

# List S3 bucket contents (top level)
s3_list_bucket() {
    aws s3 ls "s3://$S3_BUCKET/" --region "$AWS_REGION"
}

# List with specific prefix
s3_list_prefix() {
    local prefix="$1"
    aws s3 ls "s3://$S3_BUCKET/$prefix" --region "$AWS_REGION"
}

# Get bucket size
s3_bucket_size() {
    aws s3 ls "s3://$S3_BUCKET/" --recursive --summarize --region "$AWS_REGION" \
        | tail -2
}

# -------------------------------------------------------------
# POSTGRESQL COMMANDS (psql)
# -------------------------------------------------------------
# Note: COUNT(*) and SELECT * must be quoted in zsh

# Connect to database interactively
psql_connect() {
    PGPASSWORD="$PGPASSWORD" psql \
        -h "$RDS_HOST" \
        -U "$RDS_USER" \
        -d "$RDS_DB"
}

# Run a query (usage: psql_query "SELECT * FROM videos")
psql_query() {
    local query="$1"
    PGPASSWORD="$PGPASSWORD" psql \
        -h "$RDS_HOST" \
        -U "$RDS_USER" \
        -d "$RDS_DB" \
        -c "$query"
}

# Count rows in a table
psql_count() {
    local table="$1"
    PGPASSWORD="$PGPASSWORD" psql \
        -h "$RDS_HOST" \
        -U "$RDS_USER" \
        -d "$RDS_DB" \
        -c "SELECT COUNT(*) FROM $table"
}

# Select all from table
psql_select_all() {
    local table="$1"
    local limit="${2:-100}"
    PGPASSWORD="$PGPASSWORD" psql \
        -h "$RDS_HOST" \
        -U "$RDS_USER" \
        -d "$RDS_DB" \
        -c "SELECT * FROM $table LIMIT $limit"
}

# List tables
psql_tables() {
    PGPASSWORD="$PGPASSWORD" psql \
        -h "$RDS_HOST" \
        -U "$RDS_USER" \
        -d "$RDS_DB" \
        -c '\dt'
}

# Describe table
psql_describe() {
    local table="$1"
    PGPASSWORD="$PGPASSWORD" psql \
        -h "$RDS_HOST" \
        -U "$RDS_USER" \
        -d "$RDS_DB" \
        -c "\d $table"
}

# Run migration file
psql_migrate() {
    local migration_file="$1"
    PGPASSWORD="$PGPASSWORD" psql \
        -h "$RDS_HOST" \
        -U "$RDS_USER" \
        -d "$RDS_DB" \
        -f "$migration_file"
}

# -------------------------------------------------------------
# QUICK REFERENCE: Common one-liners (copy-paste ready)
# -------------------------------------------------------------
# All commands below are properly quoted for zsh

cat << 'COMMANDS'

# === EC2 ===
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' --output table
aws ec2 describe-instances --instance-ids i-030b974c11cf175cd --query 'Reservations[*].Instances[*]' --output json

# === RDS ===
aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus]' --output table
aws rds describe-db-snapshots --query 'DBSnapshots[*].[DBSnapshotIdentifier,Status,SnapshotCreateTime]' --output table
aws rds describe-db-snapshots --db-instance-identifier mv-database --query 'DBSnapshots[*]' --output json

# === psql ===
psql -h mv-database.cshawwjevydx.us-east-1.rds.amazonaws.com -U postgres -d video_management -c 'SELECT COUNT(*) FROM videos'
psql -h mv-database.cshawwjevydx.us-east-1.rds.amazonaws.com -U postgres -d video_management -c 'SELECT * FROM users LIMIT 10'
psql -h mv-database.cshawwjevydx.us-east-1.rds.amazonaws.com -U postgres -d video_management -f migrations/007_add_2fa.sql

COMMANDS

# -------------------------------------------------------------
# USAGE
# -------------------------------------------------------------
# Source this file: source scripts/aws_commands.sh
# Then call functions: ec2_list_instances, rds_list_snapshots, etc.
# Or copy commands from QUICK REFERENCE section
