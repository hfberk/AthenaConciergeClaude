-- AI Concierge Platform - Production MVP Schema
-- Version: 2.0
-- PostgreSQL 15+ with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =====================================================
-- DOMAIN 1: IDENTITY & MULTI-TENANCY
-- =====================================================

-- Organizations (top-level tenancy boundary)
CREATE TABLE organizations (
    org_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    settings_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Staff accounts (linked to Supabase auth)
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    auth_user_id UUID, -- Links to Supabase auth.users
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('admin', 'concierge', 'analyst')),
    is_active BOOLEAN DEFAULT true,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(org_id, email)
);

-- Universal person table (clients, family members, staff)
CREATE TABLE persons (
    person_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    auth_user_id UUID UNIQUE REFERENCES auth.users(id), -- For client authentication (added in migration 003)
    person_type VARCHAR(50) NOT NULL CHECK (person_type IN ('client', 'staff', 'family_member')),
    full_name VARCHAR(255) NOT NULL,
    preferred_name VARCHAR(100),
    birthday DATE,
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    metadata_jsonb JSONB DEFAULT '{}'::jsonb, -- Flexible preferences storage
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_persons_org ON persons(org_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_persons_type ON persons(person_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_persons_auth_user ON persons(auth_user_id);
CREATE INDEX idx_persons_metadata ON persons USING gin(metadata_jsonb);

-- =====================================================
-- DOMAIN 2: COMMUNICATION INFRASTRUCTURE
-- =====================================================

-- Communication identities (maps persons to channels)
CREATE TABLE comm_identities (
    comm_identity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    person_id UUID NOT NULL REFERENCES persons(person_id),
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('email', 'slack', 'sms', 'phone', 'web')),
    identity_value VARCHAR(500) NOT NULL, -- email address, Slack user ID, phone number, etc.
    is_primary BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMPTZ,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(org_id, channel_type, identity_value)
);

CREATE INDEX idx_comm_identities_person ON comm_identities(person_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_comm_identities_channel ON comm_identities(channel_type, identity_value) WHERE deleted_at IS NULL;

-- GDPR-compliant communication consent tracking
CREATE TABLE comm_consent (
    consent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    person_id UUID NOT NULL REFERENCES persons(person_id),
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('email', 'slack', 'sms', 'phone', 'web')),
    consent_given BOOLEAN NOT NULL DEFAULT true,
    consent_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_comm_consent_person ON comm_consent(person_id);

-- Conversation threads
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    person_id UUID NOT NULL REFERENCES persons(person_id),
    channel_type VARCHAR(50) NOT NULL CHECK (channel_type IN ('email', 'slack', 'sms', 'phone', 'web')),
    external_thread_id VARCHAR(500), -- Slack thread_ts, email Message-ID, etc.
    subject VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'closed', 'archived')),
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_conversations_person ON conversations(person_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversations_external ON conversations(channel_type, external_thread_id) WHERE deleted_at IS NULL;

-- Individual messages within conversations
CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id),
    direction VARCHAR(20) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    sender_person_id UUID REFERENCES persons(person_id),
    agent_name VARCHAR(100), -- Which AI agent generated this (for outbound)
    content_text TEXT NOT NULL,
    content_html TEXT,
    external_message_id VARCHAR(500), -- Slack ts, email Message-ID
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_messages_created ON messages(created_at DESC) WHERE deleted_at IS NULL;

-- =====================================================
-- DOMAIN 3: HOUSEHOLDS & ADDRESSES
-- =====================================================

-- Physical properties
CREATE TABLE households (
    household_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    household_name VARCHAR(255) NOT NULL,
    household_type VARCHAR(100), -- Primary Residence, Vacation Home, etc.
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_households_org ON households(org_id) WHERE deleted_at IS NULL;

-- Links persons to households
CREATE TABLE household_members (
    household_member_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    household_id UUID NOT NULL REFERENCES households(household_id),
    person_id UUID NOT NULL REFERENCES persons(person_id),
    relationship_to_primary VARCHAR(100), -- owner, spouse, child, staff, etc.
    is_primary BOOLEAN DEFAULT false,
    moved_in_date DATE,
    moved_out_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(household_id, person_id)
);

CREATE INDEX idx_household_members_household ON household_members(household_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_household_members_person ON household_members(person_id) WHERE deleted_at IS NULL;

-- Structured addresses (can belong to households or persons)
CREATE TABLE addresses (
    address_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    household_id UUID REFERENCES households(household_id),
    person_id UUID REFERENCES persons(person_id),
    label VARCHAR(100), -- Primary, Billing, Shipping, etc.
    address_jsonb JSONB NOT NULL, -- {street, city, state, postal_code, country}
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT address_belongs_to_household_or_person CHECK (
        (household_id IS NOT NULL AND person_id IS NULL) OR
        (household_id IS NULL AND person_id IS NOT NULL)
    )
);

CREATE INDEX idx_addresses_household ON addresses(household_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_addresses_person ON addresses(person_id) WHERE deleted_at IS NULL;

-- =====================================================
-- DOMAIN 4: DATES & REMINDERS
-- =====================================================

-- Date categories (types of important dates)
CREATE TABLE date_categories (
    category_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    category_name VARCHAR(255) NOT NULL,
    icon VARCHAR(50),
    color VARCHAR(50),
    schema_jsonb JSONB DEFAULT '{}'::jsonb, -- Category-specific fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(org_id, category_name)
);

-- Important dates
CREATE TABLE date_items (
    date_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    person_id UUID NOT NULL REFERENCES persons(person_id),
    category_id UUID NOT NULL REFERENCES date_categories(category_id),
    title VARCHAR(255) NOT NULL,
    date_value DATE NOT NULL,
    recurrence_rule TEXT, -- iCal RRULE format for recurring dates
    next_occurrence DATE, -- Computed field for efficient querying
    notes TEXT,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_date_items_person ON date_items(person_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_date_items_next_occurrence ON date_items(next_occurrence) WHERE deleted_at IS NULL;

-- Reminder rules (when/how to notify)
CREATE TABLE reminder_rules (
    reminder_rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    date_item_id UUID NOT NULL REFERENCES date_items(date_item_id),
    comm_identity_id UUID NOT NULL REFERENCES comm_identities(comm_identity_id),
    reminder_type VARCHAR(50) NOT NULL CHECK (reminder_type IN ('lead_time', 'scheduled')),
    lead_time_days INTEGER, -- For lead_time type: X days before
    scheduled_datetime TIMESTAMPTZ, -- For scheduled type: specific datetime
    sent_at TIMESTAMPTZ, -- Tracks actual delivery for idempotency
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_reminder_rules_date_item ON reminder_rules(date_item_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_reminder_rules_pending ON reminder_rules(scheduled_datetime) WHERE sent_at IS NULL AND deleted_at IS NULL;

-- =====================================================
-- DOMAIN 5: PROJECTS & TASKS
-- =====================================================

-- High-level concierge requests
CREATE TABLE projects (
    project_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    person_id UUID NOT NULL REFERENCES persons(person_id),
    assigned_to_account_id UUID REFERENCES accounts(account_id),
    source_date_item_id UUID REFERENCES date_items(date_item_id), -- Links projects to triggering dates
    title VARCHAR(500) NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 4), -- 1=highest, 4=lowest
    status VARCHAR(50) DEFAULT 'new' CHECK (status IN ('new', 'in_progress', 'blocked', 'completed', 'cancelled')),
    due_date DATE,
    completed_at TIMESTAMPTZ,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_projects_person ON projects(person_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_assigned ON projects(assigned_to_account_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_status ON projects(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_source_date ON projects(source_date_item_id) WHERE deleted_at IS NULL;

-- Large/flexible project data (separate to avoid bloating main table)
CREATE TABLE project_details (
    project_detail_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    project_id UUID NOT NULL REFERENCES projects(project_id),
    detail_type VARCHAR(100) NOT NULL,
    content_jsonb JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_project_details_project ON project_details(project_id);

-- Subtasks within projects
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    project_id UUID NOT NULL REFERENCES projects(project_id),
    parent_id UUID REFERENCES tasks(task_id), -- For nested subtasks
    assigned_to_account_id UUID REFERENCES accounts(account_id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'todo' CHECK (status IN ('todo', 'doing', 'blocked', 'done', 'cancelled')),
    due_date DATE,
    completed_at TIMESTAMPTZ,
    sort_order INTEGER DEFAULT 0,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_tasks_project ON tasks(project_id, sort_order) WHERE deleted_at IS NULL;
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to_account_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_tasks_parent ON tasks(parent_id) WHERE deleted_at IS NULL;

-- =====================================================
-- DOMAIN 6: RECOMMENDATIONS & VETTED RESOURCES
-- =====================================================

-- Vetted service providers
CREATE TABLE vendors (
    vendor_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    name VARCHAR(255) NOT NULL,
    vendor_type VARCHAR(100) NOT NULL, -- florist, caterer, photographer, etc.
    description TEXT,
    rating DECIMAL(2,1) CHECK (rating BETWEEN 1.0 AND 5.0),
    price_band VARCHAR(10) CHECK (price_band IN ('$', '$$', '$$$', '$$$$')),
    contact_info_jsonb JSONB,
    tags_jsonb JSONB DEFAULT '[]'::jsonb,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_vendors_org ON vendors(org_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_vendors_type ON vendors(vendor_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_vendors_tags ON vendors USING gin(tags_jsonb);

-- Event spaces
CREATE TABLE venues (
    venue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    name VARCHAR(255) NOT NULL,
    venue_type VARCHAR(100), -- restaurant, event_space, hotel, etc.
    description TEXT,
    capacity_min INTEGER,
    capacity_max INTEGER,
    price_band VARCHAR(10) CHECK (price_band IN ('$', '$$', '$$$', '$$$$')),
    location_jsonb JSONB, -- {neighborhood, city, state}
    private_rooms_jsonb JSONB DEFAULT '[]'::jsonb,
    contact_info_jsonb JSONB,
    tags_jsonb JSONB DEFAULT '[]'::jsonb,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_venues_org ON venues(org_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_venues_capacity ON venues(capacity_min, capacity_max) WHERE deleted_at IS NULL;
CREATE INDEX idx_venues_tags ON venues USING gin(tags_jsonb);

-- Dining recommendations
CREATE TABLE restaurants (
    restaurant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    name VARCHAR(255) NOT NULL,
    cuisine VARCHAR(100),
    neighborhood VARCHAR(100),
    description TEXT,
    rating DECIMAL(2,1) CHECK (rating BETWEEN 1.0 AND 5.0),
    price_band VARCHAR(10) CHECK (price_band IN ('$', '$$', '$$$', '$$$$')),
    private_dining_jsonb JSONB, -- {available, capacity, pricing}
    contact_info_jsonb JSONB,
    tags_jsonb JSONB DEFAULT '[]'::jsonb,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_restaurants_org ON restaurants(org_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_restaurants_cuisine ON restaurants(cuisine) WHERE deleted_at IS NULL;
CREATE INDEX idx_restaurants_neighborhood ON restaurants(neighborhood) WHERE deleted_at IS NULL;
CREATE INDEX idx_restaurants_tags ON restaurants USING gin(tags_jsonb);

-- Gift ideas and shopping recommendations
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(100),
    description TEXT,
    price DECIMAL(10,2),
    price_band VARCHAR(10) CHECK (price_band IN ('$', '$$', '$$$', '$$$$')),
    url TEXT,
    image_url TEXT,
    tags_jsonb JSONB DEFAULT '[]'::jsonb,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_products_org ON products(org_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_products_category ON products(category) WHERE deleted_at IS NULL;
CREATE INDEX idx_products_tags ON products USING gin(tags_jsonb);

-- AI-generated recommendations (polymorphic references)
CREATE TABLE recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    project_id UUID NOT NULL REFERENCES projects(project_id),
    item_type VARCHAR(50) NOT NULL CHECK (item_type IN ('vendor', 'venue', 'restaurant', 'product')),
    item_id UUID NOT NULL, -- References vendor_id, venue_id, restaurant_id, or product_id
    rationale_text TEXT, -- Why this was recommended
    score DECIMAL(3,2) CHECK (score BETWEEN 0 AND 1), -- Relevance score 0-1
    shown_at TIMESTAMPTZ,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_recommendations_project ON recommendations(project_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_recommendations_item ON recommendations(item_type, item_id) WHERE deleted_at IS NULL;

-- Client feedback on recommendations
CREATE TABLE interaction_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    recommendation_id UUID NOT NULL REFERENCES recommendations(recommendation_id),
    person_id UUID NOT NULL REFERENCES persons(person_id),
    feedback_type VARCHAR(50) NOT NULL CHECK (feedback_type IN ('liked', 'disliked', 'used', 'ignored')),
    feedback_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_interaction_feedback_recommendation ON interaction_feedback(recommendation_id);
CREATE INDEX idx_interaction_feedback_person ON interaction_feedback(person_id);

-- =====================================================
-- DOMAIN 7: AI AGENT INFRASTRUCTURE
-- =====================================================

-- Configurable agent definitions
CREATE TABLE agent_roster (
    agent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    agent_name VARCHAR(100) NOT NULL,
    agent_kind VARCHAR(50) NOT NULL CHECK (agent_kind IN ('interaction', 'execution')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
    system_prompt TEXT NOT NULL,
    context_jsonb JSONB DEFAULT '{}'::jsonb, -- Agent-specific configuration
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(org_id, agent_name, version)
);

CREATE INDEX idx_agent_roster_org ON agent_roster(org_id, status) WHERE deleted_at IS NULL;

-- Complete audit trail of agent decisions
CREATE TABLE agent_execution_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    agent_id UUID NOT NULL REFERENCES agent_roster(agent_id),
    run_id UUID NOT NULL, -- Groups related messages
    turn_index INTEGER NOT NULL, -- Order within conversation
    conversation_id UUID REFERENCES conversations(conversation_id),
    person_id UUID REFERENCES persons(person_id),
    payload_jsonb JSONB NOT NULL, -- Full request/response for debugging
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_execution_logs_run ON agent_execution_logs(run_id, turn_index);
CREATE INDEX idx_agent_execution_logs_conversation ON agent_execution_logs(conversation_id);
CREATE INDEX idx_agent_execution_logs_created ON agent_execution_logs(created_at DESC);

-- Vector embeddings for semantic search
CREATE TABLE embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('person', 'project', 'message', 'recommendation', 'preference')),
    entity_id UUID NOT NULL,
    embedding_vector vector(1536), -- OpenAI ada-002 dimensions, adjust for other models
    content_text TEXT NOT NULL,
    metadata_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_embeddings_entity ON embeddings(entity_type, entity_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100);

-- Ephemeral agent state storage
CREATE TABLE working_memory (
    memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id),
    memory_key VARCHAR(255) NOT NULL,
    memory_value_jsonb JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(conversation_id, memory_key)
);

CREATE INDEX idx_working_memory_conversation ON working_memory(conversation_id);
CREATE INDEX idx_working_memory_expires ON working_memory(expires_at);

-- =====================================================
-- DOMAIN 8: SYSTEM AUDIT
-- =====================================================

-- Unified audit log
CREATE TABLE event_log (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    actor_type VARCHAR(50) NOT NULL CHECK (actor_type IN ('person', 'agent', 'system')),
    actor_id UUID, -- person_id, agent_id, or NULL for system
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    details_jsonb JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_event_log_org ON event_log(org_id, created_at DESC);
CREATE INDEX idx_event_log_entity ON event_log(entity_type, entity_id);
CREATE INDEX idx_event_log_actor ON event_log(actor_type, actor_id);

-- =====================================================
-- FUNCTIONS & TRIGGERS
-- =====================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to all relevant tables
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'updated_at'
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            CREATE TRIGGER update_%I_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t, t);
    END LOOP;
END;
$$ language 'plpgsql';

-- Function to compute next_occurrence for recurring dates
CREATE OR REPLACE FUNCTION compute_next_occurrence(
    date_value DATE,
    recurrence_rule TEXT,
    from_date DATE DEFAULT CURRENT_DATE
)
RETURNS DATE AS $$
BEGIN
    -- Simplified implementation - production should use proper RRULE parser
    IF recurrence_rule IS NULL THEN
        RETURN date_value;
    ELSIF recurrence_rule LIKE '%FREQ=YEARLY%' THEN
        -- Simple yearly recurrence
        RETURN make_date(
            EXTRACT(YEAR FROM from_date)::int +
            CASE WHEN make_date(EXTRACT(YEAR FROM from_date)::int, EXTRACT(MONTH FROM date_value)::int, EXTRACT(DAY FROM date_value)::int) < from_date THEN 1 ELSE 0 END,
            EXTRACT(MONTH FROM date_value)::int,
            EXTRACT(DAY FROM date_value)::int
        );
    ELSE
        RETURN date_value;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =====================================================
-- ROW LEVEL SECURITY (RLS) - Optional but recommended
-- =====================================================

-- Enable RLS on all tables (uncomment in production with Supabase Auth)
-- ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
-- ... (repeat for all tables)

-- Example RLS policy for multi-tenancy
-- CREATE POLICY tenant_isolation_policy ON persons
--   USING (org_id = current_setting('app.current_org_id')::uuid);

-- =====================================================
-- SEED DATA FOR DEVELOPMENT
-- =====================================================

-- Create default organization
INSERT INTO organizations (org_id, name, domain)
VALUES ('00000000-0000-0000-0000-000000000001', 'Demo Family Office', 'demo.concierge.ai');

-- Create default date categories
INSERT INTO date_categories (org_id, category_name, icon, color) VALUES
('00000000-0000-0000-0000-000000000001', 'Birthday', '🎂', '#FF6B6B'),
('00000000-0000-0000-0000-000000000001', 'Anniversary', '💑', '#FF69B4'),
('00000000-0000-0000-0000-000000000001', 'Club Renewal', '🎾', '#4ECDC4'),
('00000000-0000-0000-0000-000000000001', 'Property Maintenance', '🏠', '#95E1D3'),
('00000000-0000-0000-0000-000000000001', 'School Event', '🎓', '#F38181'),
('00000000-0000-0000-0000-000000000001', 'Travel', '✈️', '#AA96DA');

-- Create default admin account
INSERT INTO accounts (org_id, email, full_name, account_type) VALUES
('00000000-0000-0000-0000-000000000001', 'admin@demo.concierge.ai', 'Admin User', 'admin');

COMMENT ON SCHEMA public IS 'AI Concierge Platform - Production MVP Schema v2.0';
