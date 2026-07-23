import redis.asyncio as redis
from app.core.config import settings

# Global Redis client
redis_client = None

async def init_redis():
    global redis_client
    if not redis_client:
        redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return redis_client

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

# Cache helpers
async def get_cached_score(opportunity_id: int):
    if not redis_client:
        await init_redis()
    key = f"opportunity_score:{opportunity_id}"
    cached = await redis_client.get(key)
    if cached:
        import json
        return json.loads(cached)
    return None

async def set_cached_score(opportunity_id: int, score_data: dict, expire: int = 300):
    if not redis_client:
        await init_redis()
    key = f"opportunity_score:{opportunity_id}"
    import json
    await redis_client.setex(key, expire, json.dumps(score_data))

async def get_cached_agent_insights(opportunity_id: int):
    if not redis_client:
        await init_redis()
    key = f"agent_insights:{opportunity_id}"
    cached = await redis_client.get(key)
    if cached:
        import json
        return json.loads(cached)
    return None

async def set_cached_agent_insights(opportunity_id: int, insights_data: dict, expire: int = 300):
    if not redis_client:
        await init_redis()
    key = f"agent_insights:{opportunity_id}"
    import json
    await redis_client.setex(key, expire, json.dumps(insights_data))


async def delete_cached_score(opportunity_id: int):
    if not redis_client:
        await init_redis()
    key = f"opportunity_score:{opportunity_id}"
    await redis_client.delete(key)


async def delete_cached_agent_insights(opportunity_id: int):
    if not redis_client:
        await init_redis()
    key = f"agent_insights:{opportunity_id}"
    await redis_client.delete(key)