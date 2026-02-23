-- GraphMind Financial Knowledge Graph Schema
-- Neo4j Cypher Schema Definition

-- ============================================
-- CONSTRAINTS & INDEXES
-- ============================================

-- User Node Constraints
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE INDEX user_id_index IF NOT EXISTS
FOR (u:User) ON (u.id);

-- Asset Node Constraints
CREATE CONSTRAINT asset_id_unique IF NOT EXISTS
FOR (a:Asset) REQUIRE a.id IS UNIQUE;

CREATE INDEX asset_name_index IF NOT EXISTS
FOR (a:Asset) ON (a.name);

CREATE INDEX asset_user_index IF NOT EXISTS
FOR (a:Asset) ON (a.user_id);

-- Goal Node Constraints
CREATE CONSTRAINT goal_id_unique IF NOT EXISTS
FOR (g:Goal) REQUIRE g.id IS UNIQUE;

CREATE INDEX goal_user_index IF NOT EXISTS
FOR (g:Goal) ON (g.user_id);

-- Transaction Node Constraints
CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS
FOR (t:Transaction) REQUIRE t.id IS UNIQUE;

CREATE INDEX transaction_date_index IF NOT EXISTS
FOR (t:Transaction) ON (t.date);

CREATE INDEX transaction_user_index IF NOT EXISTS
FOR (t:Transaction) ON (t.user_id);

-- RiskProfile Node Constraints
CREATE CONSTRAINT risk_profile_id_unique IF NOT EXISTS
FOR (r:RiskProfile) REQUIRE r.id IS UNIQUE;

-- Indexes for Reinforcement Learning
CREATE INDEX last_reinforced_index IF NOT EXISTS
FOR (n:Asset) ON (n.last_reinforced);

CREATE INDEX confidence_index IF NOT EXISTS
FOR (n:Asset) ON (n.confidence);

-- ============================================
-- REINFORCEMENT LEARNING MECHANISM
-- ============================================

-- Memory Reinforcement Strategy:
-- 1. ON CREATE: All nodes get confidence=0.8, last_reinforced=now()
-- 2. ON RETRIEVAL: When nodes are accessed, last_reinforced is updated to now()
-- 3. FUTURE: Nodes with recent last_reinforced timestamps get higher priority
-- 4. FUTURE: Frequently accessed nodes can have confidence boosted over time
--
-- Benefits:
-- - Tracks which information is frequently accessed
-- - Enables temporal decay of unused memories
-- - Supports adaptive retrieval based on usage patterns
-- - Qualifies for reinforcement learning memory stretch goal

-- ============================================
-- NODE TYPES SCHEMA
-- ============================================

-- ALL NODES INCLUDE METADATA FOR REINFORCEMENT LEARNING:
-- - timestamp: DateTime of when the node was created
-- - source_type: Source of the information (e.g., "user_input", "inference")
-- - confidence: Confidence score (0.0 to 1.0, default: 0.8)
-- - last_reinforced: DateTime of when the node was last retrieved/accessed
-- - created_at: DateTime of node creation
-- - updated_at: DateTime of last update

-- User
-- Properties: id, name, email, created_at

-- Asset
-- Properties: id, name, asset_type, current_value, user_id, 
--            timestamp, source_type, confidence, last_reinforced, created_at
-- Types: mutual_fund, stock, bond, real_estate, gold, etc.

-- Goal
-- Properties: id, name, goal_type, target_amount, target_date, user_id,
--            timestamp, source_type, confidence, last_reinforced, created_at
-- Types: retirement, education, house, emergency_fund, etc.

-- Transaction
-- Properties: id, amount, transaction_type, date, description, user_id,
--            timestamp, source_type, confidence, last_reinforced, created_at
-- Types: investment, withdrawal, dividend, etc.

-- RiskProfile
-- Properties: id, risk_level, risk_score, user_id,
--            timestamp, source_type, confidence, last_reinforced, created_at
-- Levels: low, moderate, high

-- ============================================
-- RELATIONSHIP TYPES
-- ============================================

-- (User)-[:OWNS]->(Asset)
-- (User)-[:HAS_GOAL]->(Goal)
-- (User)-[:MADE_TRANSACTION]->(Transaction)
-- (User)-[:HAS_RISK_PROFILE]->(RiskProfile)
-- (Transaction)-[:AFFECTS_ASSET]->(Asset)
-- (Asset)-[:CONTRIBUTES_TO]->(Goal)
-- (Asset)-[:HAS_RISK]->(RiskProfile)

-- ============================================
-- SAMPLE DATA STRUCTURE
-- ============================================

-- Example User:
-- (:User {id: "u123", name: "John Doe", created_at: datetime()})

-- Example Asset:
-- (:Asset {
--   id: "a123",
--   name: "HDFC Mutual Fund",
--   asset_type: "mutual_fund",
--   current_value: 50000,
--   user_id: "u123",
--   timestamp: datetime(),
--   source_type: "user_input",
--   confidence: 0.8,
--   last_reinforced: datetime(),
--   created_at: datetime(),
--   updated_at: datetime()
-- })

-- Example Goal:
-- (:Goal {
--   id: "g123",
--   name: "Retirement",
--   goal_type: "retirement",
--   target_amount: 10000000,
--   target_date: date("2050-01-01"),
--   user_id: "u123",
--   timestamp: datetime(),
--   source_type: "user_input",
--   confidence: 0.8,
--   last_reinforced: datetime(),
--   created_at: datetime(),
--   updated_at: datetime()
-- })
