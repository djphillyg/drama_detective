# PostgreSQL Architecture for Ethereum Trading System

## The System
Decentralized trading platform on Ethereum:
- Ingested user balance events from smart contracts
- Ingested price data from oracle contracts
- Calculated user collateralization in real-time for trading limits

---

## Problem 1: Deadlocks from Pending/Confirmed Block Logic

### Initial Approach
- Parallel workers processing blocks concurrently
- Updating balance state as blocks transitioned from pending → confirmed
- Lock contention when multiple workers touched same user balances

### Deadlock Pattern
```
Worker A (Block 105):           Worker B (Confirming Block 104):
├─ Update user balance          ├─ Promote pending → confirmed
├─ Lock on balance_updates      ├─ Lock on block metadata
├─ Wait for block lock          ├─ Wait for balance lock
└─ DEADLOCK                     └─ DEADLOCK
```

### Solution
- Sequential block processing via blockchain watcher
- Trade-off: Slower ingestion, but zero deadlocks

---

## Problem 2: Query Performance - Linear Growth

### The Killer Query
```sql
SELECT u.user_id, u.address, bu.asset_id, bu.balance
FROM users u
JOIN balance_updates bu ON u.address = bu.user_address
WHERE bu.block_status = 'confirmed'
```

### Why It Failed
- `balance_updates` table: append-only event log (millions of rows)
- JOIN + aggregation across ALL users, ALL historical events
- O(users × events_per_user) - grew linearly with both dimensions
- RDS CPU → 100%, queries timing out

---

## Solution: Dual-State Denormalized Table

### Rearchitecture

Created `user_current_balances` table:

```sql
CREATE TABLE user_current_balances (
  user_address TEXT,
  asset_id TEXT,
  balance NUMERIC,
  block_number BIGINT,
  block_status TEXT,  -- 'confirmed' or 'pending'
  PRIMARY KEY (user_address, asset_id, block_status)
);
```

### Key Innovation
Separate rows for confirmed vs pending state:

```
| user_address | asset_id | balance | block_number | block_status |
|--------------|----------|---------|--------------|--------------|
| 0xABC...     | USDC     | 1000    | 104          | confirmed    |
| 0xABC...     | USDC     | 1050    | 105          | pending      |
```

### Benefits
1. **No rollback complexity** - Reorgs just delete pending rows
2. **Fast queries** - Direct lookup, no JOIN on massive table
3. **UX flexibility** - Show confirmed + pending delta separately

---

## The Migration

### Strategy: Dual-write → Backfill → Cutover

#### 1. Dual-write Phase
- Blockchain watcher writes to both tables
- Old: `INSERT` into `balance_updates`
- New: `UPSERT` into `user_current_balances`

#### 2. Backfill
- Background job processed historical `balance_updates`
- Populated `user_current_balances` with latest confirmed state per user/asset

#### 3. Cutover
- Switched queries to denormalized table
- Removed expensive JOINs entirely

---

## Reorg Handling (The Sophisticated Part)

### When Blockchain Reorg Detected

```sql
-- 1. Delete invalidated pending blocks
DELETE FROM user_current_balances
WHERE block_number >= $reorg_block AND block_status = 'pending';

-- 2. Re-process new canonical blocks
-- Blockchain watcher inserts new pending state
INSERT INTO user_current_balances
VALUES (..., $block_number, 'pending');
```

### When Pending Block Becomes Confirmed

```sql
-- Promote pending → confirmed
UPDATE user_current_balances
SET block_status = 'confirmed'
WHERE block_number = $block_number AND block_status = 'pending';

-- Delete old confirmed state
DELETE FROM user_current_balances
WHERE block_status = 'confirmed'
  AND block_number < $block_number
  AND user_address = $address
  AND asset_id = $asset;
```

---

## Results

### Before
- **RDS CPU:** 100% constant
- **Query time:** Seconds (and growing)
- **Deadlocks:** Multiple per hour
- **Collateral calculation:** Linear growth with user count

### After
- **RDS CPU:** Normal levels
- **Query time:** Milliseconds (O(1) lookup)
- **Deadlocks:** Zero
- **Collateral calculation:** Fast per-user lookup

---

## Key Technical Talking Points

1. **Blockchain-specific challenges** - Pending/confirmed duality, reorgs
2. **Identifying bottleneck** - JOIN performance, not locking
3. **Denormalization trade-off** - Write complexity for read performance
4. **Migration strategy** - Zero-downtime dual-write approach
5. **Reorg resilience** - Separate rows eliminated rollback complexity

---

## Additional Architecture Details

### Redis Caching Layer
- User balances never stored directly in PostgreSQL for real-time reads
- When balance updates processed, Redis cache updated with: `user_id → {asset: balance × price}`
- PostgreSQL served as source of truth for historical events
- Redis served as fast lookup for current state

### Data Flow
```
Ethereum Events
  → PostgreSQL (balance_updates - historical log)
  → Blockchain Watcher processes events
  → user_current_balances (denormalized current state)
  → Redis Cache (balance × price for fast reads)
```

### Collateral Calculation
```
For each user:
  collateral = SUM(balance_i × price_i × collateral_factor_i)
  FOR ALL assets in user's account
```

- **Before:** Queried all users with expensive JOINs
- **After:** Direct lookup per user from denormalized table
- Changed from O(n × m) batch job to O(1) per-user lookup
