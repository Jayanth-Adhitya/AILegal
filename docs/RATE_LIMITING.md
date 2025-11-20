# Rate Limiting Guide - Gemini Embedding API

This guide explains how the system handles Gemini API rate limits and how to configure it for your use case.

## Overview

The Gemini embedding API has **rate limits** that you need to account for when embedding large numbers of documents:

| Tier | RPM (Requests/Min) | RPD (Requests/Day) | TPM (Tokens/Min) | Cost |
|------|--------------------|--------------------|------------------|------|
| **Free** | **100** | **1,000** ⚠️ | **30,000** | $0 |
| **Tier 1 (Paid)** | **3,000** | **Unlimited** | **1,000,000** | $0.15/1M tokens |
| **Tier 2** | **5,000** | **Unlimited** | **5,000,000** | (>$250 spend) |
| **Tier 3** | **10,000** | **Unlimited** | **10,000,000** | (>$1,000 spend) |

**Important:**
- Each chunk (piece of text) requires **one API request**
- **Free tier:** Limited to **1,000 requests per day** (resets midnight Pacific)
- **Paid tier:** No daily limit, only per-minute limits
- If embedding 2,000 chunks on free tier: **requires 2 days**
- If embedding 2,000 chunks on paid tier: **completes in ~1 minute** (cost: ~$0.15)

---

## How Rate Limiting is Handled

The system has **three layers of protection**:

### 1. **Automatic Batching**
Documents are embedded in **small batches** with delays between batches:

```python
# Default configuration
embedding_batch_size = 50       # Process 50 chunks per batch
embedding_delay_seconds = 1.0   # Wait 1 second between batches
```

**Example:** 300 chunks = 6 batches = ~6 seconds total

### 2. **Exponential Backoff Retry**
If rate limits are hit, the system automatically retries with increasing delays:

```
Attempt 1: Immediate
Attempt 2: Wait 4 seconds
Attempt 3: Wait 8 seconds
Attempt 4: Wait 16 seconds
Attempt 5: Wait 32 seconds
Attempt 6: Wait 60 seconds (max)
```

**Total retries:** 5 attempts

### 3. **Progress Logging**
You can see exactly what's happening:

```
[INFO] Embedding 342 texts in 7 batch(es) (batch_size=50, delay=1.0s)
[INFO] Processing batch 1/7 (50 texts)...
[INFO] Waiting 1.0s before next batch...
[INFO] Processing batch 2/7 (50 texts)...
...
[INFO] ✅ Successfully embedded 342 texts
```

---

## Configuration Options

### Via Environment Variables (.env)

```bash
# Embedding API Rate Limiting
EMBEDDING_BATCH_SIZE=50           # Chunks per batch
EMBEDDING_DELAY_SECONDS=1.0       # Delay between batches (seconds)
EMBEDDING_REQUESTS_PER_MINUTE=1500 # Your API tier limit
```

### Via Command Line (Build Script)

```bash
# Default settings (50 chunks/batch, 1s delay)
python scripts/build_regional_db.py

# Conservative settings (25 chunks/batch, 2s delay) - for rate limit issues
python scripts/build_regional_db.py --batch-size 25 --delay 2.0

# Aggressive settings (100 chunks/batch, 0.5s delay) - for paid tiers
python scripts/build_regional_db.py --batch-size 100 --delay 0.5
```

---

## Recommended Settings by Tier

### Free Tier (100 RPM, 1,000 RPD) ⚠️
```bash
EMBEDDING_BATCH_SIZE=50
EMBEDDING_DELAY_SECONDS=0.5
```

**Throughput:** ~100 chunks/minute (respects 100 RPM limit)
**Daily capacity:** 1,000 chunks/day
**Risk:** Low

**Important:** You'll hit the **daily quota (1,000 RPD)** before hitting the minute limit. For large datasets (>1,000 chunks), you need either:
- Multiple days (free tier resets at midnight Pacific)
- Paid tier upgrade

---

### Paid Tier 1 (3,000 RPM, Unlimited RPD)
```bash
EMBEDDING_BATCH_SIZE=100
EMBEDDING_DELAY_SECONDS=0.1
```

**Throughput:** ~600-1,000 chunks/minute
**Daily capacity:** Unlimited
**Cost:** $0.15 per 1M tokens (~$0.15 per 2,000 chunks)
**Risk:** Very low

---

### Conservative (If Hitting Rate Limits on Free Tier)
```bash
EMBEDDING_BATCH_SIZE=20
EMBEDDING_DELAY_SECONDS=1.0
```

**Throughput:** ~20 chunks/minute (well below 100 RPM)
**Risk:** None (extremely safe)

---

## Troubleshooting Rate Limits

### Symptom: `ResourceExhausted` - Daily Quota Exceeded

**Error Message:**
```
429 Quota exceeded for metric: generativelanguage.googleapis.com/embed_content_free_tier_requests, limit: 0
```

**Cause:** You've hit the **1,000 requests per day (RPD)** limit on the free tier.

**Solutions (Choose One):**

1. **Wait for quota reset (Free):**
   - Quotas reset at **midnight Pacific Time**
   - Continue building tomorrow:
     ```bash
     python scripts/build_regional_db.py
     ```
   - System will skip already-embedded documents
   - For 2,000 chunks: takes 2-3 days total

2. **Enable billing (Recommended - ~$0.15 total):**
   - Go to: [Google Cloud Console Billing](https://console.cloud.google.com/billing)
   - Enable billing for your project
   - Get **unlimited daily quota** + **3,000 RPM**
   - Complete entire database in ~2 minutes
   - Cost: ~$0.15 per 1M tokens (one-time)

   ```bash
   # After enabling billing
   python scripts/build_regional_db.py
   ```

3. **Use different API key (Free, temporary):**
   - Create new API key: https://aistudio.google.com/apikey
   - Update `.env` with new key
   - Get fresh 1,000 RPD quota

4. **Check current quota usage:**
   - Go to: https://ai.dev/usage?tab=rate-limit
   - See when your quota resets

---

### Symptom: Build Takes Too Long

**Cause:** Very conservative rate limiting settings

**Solutions:**

1. **Increase batch size:**
   ```bash
   python scripts/build_regional_db.py --batch-size 100 --delay 0.5
   ```

2. **Verify you're not hitting limits:**
   - Check logs for retry messages
   - If no retries, you can be more aggressive

3. **Estimate build time:**
   ```
   Time = (Total Chunks / Batch Size) × Delay

   Example:
   - 300 chunks, batch_size=50, delay=1s
   - Time = (300 / 50) × 1 = 6 seconds

   - 300 chunks, batch_size=25, delay=2s
   - Time = (300 / 25) × 2 = 24 seconds
   ```

---

### Symptom: Intermittent Failures

**Cause:** Network issues or temporary API unavailability

**Solution:**
- The system automatically retries (5 attempts)
- Check your internet connection
- Check [Google Cloud Status](https://status.cloud.google.com/)

---

## Rate Limit Math

### Free Tier (100 RPM, 1,000 RPD) ⚠️

**The real bottleneck is RPD (Requests Per Day), not RPM:**

**RPM Limit:**
```
Free tier: 100 RPM
Maximum in 1 minute = 100 requests
Maximum in 1 hour = 100 × 60 = 6,000 requests
```

**RPD Limit (The Real Problem):**
```
Free tier: 1,000 RPD (Requests Per Day)
Maximum per day = 1,000 requests = 1,000 chunks

If you have 2,000 chunks:
- Day 1: 1,000 chunks ✓
- Day 2: 1,000 chunks ✓
Total: 2 days needed
```

**For your 79 Dubai documents (~1,500-2,000 chunks):**
```
Total chunks: ~2,000
Free tier quota: 1,000 per day
Days needed: 2-3 days

OR

Enable billing:
Cost: 2,000 chunks × 500 tokens/chunk = 1M tokens
Price: $0.15 per 1M tokens = $0.15 total
Time: ~2 minutes
```

**Paid Tier 1 (3,000 RPM, Unlimited RPD):**
```
No daily limit!
Maximum throughput: 3,000 requests/minute
For 2,000 chunks: ~1 minute
Cost: ~$0.15 (one-time)
```

---

## Best Practices

### 1. **Start Conservative, Then Optimize**
```bash
# First run (safe)
python scripts/build_regional_db.py --batch-size 25 --delay 2.0

# If successful with no retries, increase
python scripts/build_regional_db.py --batch-size 50 --delay 1.0

# If still no retries, increase more
python scripts/build_regional_db.py --batch-size 100 --delay 0.5
```

### 2. **Monitor Logs for Retries**
```
[INFO] Embedding 342 texts...
[WARNING] Rate limit hit, retrying... (attempt 1/5)  ← INCREASE DELAY
[INFO] ✅ Successfully embedded 342 texts            ← NO RETRIES = CAN INCREASE
```

### 3. **Set Environment Variables for Production**
Don't rely on defaults. Set explicit values in `.env`:

```bash
# Production settings (tested and verified)
EMBEDDING_BATCH_SIZE=50
EMBEDDING_DELAY_SECONDS=1.0
EMBEDDING_REQUESTS_PER_MINUTE=1500
```

### 4. **Pre-Build Database for Deployment**
Build once locally, package in Docker (no embedding during deployment):

```bash
# Local build (once)
python scripts/build_regional_db.py

# Docker (no embedding, instant startup)
COPY chroma_db/ ./chroma_db/
```

### 5. **Use Progress Logging During Builds**
Enable progress logging to see batching in action:

```python
# In PolicyEmbeddings.ingest_regional_directory()
embeddings_list = self.embed_documents_batched(texts, show_progress=True)
```

---

## FAQ

### Q: How many chunks can I embed per day?
**A:** Depends on your tier:
- **Free tier:** 1,000 chunks/day maximum (1,000 RPD limit)
- **Paid tier (Tier 1):** Unlimited chunks/day

### Q: How long to embed 2,000 Dubai document chunks?
**A:** Depends on your tier:

**Free tier:**
```
Day 1: 1,000 chunks (hit daily quota)
Day 2: 1,000 chunks (hit daily quota)
Total: 2 days
Cost: $0
```

**Paid tier:**
```
Time: ~2 minutes (3,000 RPM)
Cost: ~$0.15 (one-time)
```

### Q: What happens if I hit the daily quota?
**A:** You get a `429 Quota exceeded` error. Solutions:
1. Wait until midnight Pacific Time for quota reset
2. Enable billing (~$0.15 for entire database)
3. Use a different API key

### Q: Is the $0.15 cost monthly or one-time?
**A:** **One-time!** Once you build the database, it persists to disk. You never need to re-embed the same documents. The $0.15 is only for the initial embedding.

### Q: Do retries count against my quota?
**A:** Yes. Each retry attempt counts as a new request. That's why the system uses exponential backoff to minimize wasted quota.

### Q: Can I check my current quota usage?
**A:** Yes:
- Go to: https://ai.dev/usage?tab=rate-limit
- Shows: Current usage, remaining quota, when it resets

### Q: Can I disable rate limiting?
**A:** Not recommended. The **daily quota (1,000 RPD)** is a hard limit. Rate limiting only helps you stay within the **per-minute limit (100 RPM)**.

### Q: I only embedded 134 chunks, why did I hit the quota?
**A:** You likely embedded more documents earlier today from other scripts/testing. Check your usage at: https://ai.dev/usage

---

## Summary

### Key Insights

✅ **Free tier limit:** 1,000 requests/day (RPD) - the real bottleneck
✅ **Large datasets (>1,000 chunks):** Need 2-3 days OR paid tier (~$0.15 one-time)
✅ **Rate limiting is automatic:** Batching + exponential backoff retry
✅ **Database persists:** Once built, never need to re-embed (one-time cost)
✅ **Paid tier recommended for production:** Unlimited daily quota, completes in minutes

### Recommended Approach

**For testing (small datasets <1,000 chunks):**
```bash
# Free tier is fine
python scripts/build_regional_db.py
```

**For production (large datasets >1,000 chunks):**
```bash
# Enable billing: https://console.cloud.google.com/billing
# Cost: ~$0.15 per 1M tokens (one-time)
# Time: ~2 minutes

python scripts/build_regional_db.py

# Then package in Docker (no more embedding needed)
docker build -t legal-agent .
```

**If you hit quota:**
- ⏰ **Wait:** Quota resets at midnight Pacific Time
- 💰 **Upgrade:** Enable billing (~$0.15 total, unlimited daily quota)
- 🔑 **Switch:** Use different API key (fresh 1,000 quota)

### Bottom Line

🚀 **For $0.15, you can build the entire database in 2 minutes and never worry about embeddings again!**

The database persists to disk and can be packaged in Docker. The $0.15 is a **one-time cost**, not monthly. 🎉
