"""
Redis 연결 및 캐시 관리
"""

import redis
import json
from typing import Any, Optional
from app.core.config import settings
from app.core.logging import logger


class RedisClient:
    """Redis 클라이언트 래퍼"""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
    
    def get(self, key: str) -> Optional[Any]:
        """키로 값 조회"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET 오류 - key: {key}, error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """키-값 저장"""
        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
            if ttl:
                return self.redis_client.setex(key, ttl, serialized_value)
            else:
                return self.redis_client.set(key, serialized_value)
        except Exception as e:
            logger.error(f"Redis SET 오류 - key: {key}, error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """키 삭제"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE 오류 - key: {key}, error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS 오류 - key: {key}, error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """카운터 증가"""
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR 오류 - key: {key}, error: {e}")
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """키에 TTL 설정"""
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Redis EXPIRE 오류 - key: {key}, error: {e}")
            return False
    
    def get_keys(self, pattern: str) -> list:
        """패턴으로 키 검색"""
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS 오류 - pattern: {pattern}, error: {e}")
            return []
    
    def flush_db(self) -> bool:
        """데이터베이스 전체 삭제 (개발용)"""
        try:
            return bool(self.redis_client.flushdb())
        except Exception as e:
            logger.error(f"Redis FLUSHDB 오류: {e}")
            return False


# Redis 클라이언트 인스턴스
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Redis 클라이언트 의존성 주입"""
    return redis_client


def check_redis_health() -> dict:
    """Redis 상태 확인"""
    try:
        # 연결 테스트
        redis_client.redis_client.ping()
        
        # 정보 조회
        info = redis_client.redis_client.info()
        
        return {
            "status": "healthy",
            "version": info.get("redis_version", "unknown"),
            "used_memory": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


class CacheManager:
    """캐시 관리자"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.default_ttl = settings.CACHE_TTL_SECONDS
    
    def cache_key(self, prefix: str, *args) -> str:
        """캐시 키 생성"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)
    
    def get_or_set(self, key: str, func, ttl: int = None) -> Any:
        """캐시에서 조회하거나 함수 실행 후 저장"""
        # 캐시에서 조회
        cached_value = self.redis.get(key)
        if cached_value is not None:
            return cached_value
        
        # 함수 실행
        value = func()
        
        # 캐시에 저장
        if value is not None:
            self.redis.set(key, value, ttl or self.default_ttl)
        
        return value
    
    def invalidate_pattern(self, pattern: str) -> int:
        """패턴에 맞는 캐시 무효화"""
        keys = self.redis.get_keys(pattern)
        if keys:
            return sum(self.redis.delete(key) for key in keys)
        return 0
    
    def get_user_cache_key(self, user_id: int, resource: str) -> str:
        """사용자별 캐시 키 생성"""
        return self.cache_key("user", user_id, resource)
    
    def get_company_cache_key(self, company_id: int, resource: str) -> str:
        """회사별 캐시 키 생성"""
        return self.cache_key("company", company_id, resource)
    
    def get_sentiment_cache_key(self, company_id: int, stakeholder_type: str, date: str) -> str:
        """센티멘트 캐시 키 생성"""
        return self.cache_key("sentiment", company_id, stakeholder_type, date)


# 캐시 매니저 인스턴스
cache_manager = CacheManager(redis_client)


def get_cache_manager() -> CacheManager:
    """캐시 매니저 의존성 주입"""
    return cache_manager