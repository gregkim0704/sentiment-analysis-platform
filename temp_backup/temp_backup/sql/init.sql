-- 멀티 스테이크홀더 센티멘트 분석 플랫폼 데이터베이스 초기화 스크립트

-- 확장 기능 설치
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- 한국어 전문 검색을 위한 설정
-- 한국어 사전이 설치되어 있지 않은 경우 기본 사전 사용
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_ts_config WHERE cfgname = 'korean'
    ) THEN
        -- 한국어 설정이 없으면 기본 설정 사용
        RAISE NOTICE '한국어 전문 검색 설정을 찾을 수 없습니다. 기본 설정을 사용합니다.';
    END IF;
END $$;

-- 성능 최적화를 위한 설정
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- 커스텀 함수: 센티멘트 점수를 숫자로 변환
CREATE OR REPLACE FUNCTION sentiment_to_numeric(sentiment_text TEXT)
RETURNS INTEGER AS $$
BEGIN
    CASE sentiment_text
        WHEN 'very_negative' THEN RETURN -2;
        WHEN 'negative' THEN RETURN -1;
        WHEN 'neutral' THEN RETURN 0;
        WHEN 'positive' THEN RETURN 1;
        WHEN 'very_positive' THEN RETURN 2;
        ELSE RETURN 0;
    END CASE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 커스텀 함수: 날짜별 센티멘트 트렌드 계산
CREATE OR REPLACE FUNCTION calculate_sentiment_trend(
    p_company_id INTEGER,
    p_stakeholder_type TEXT,
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE(
    date DATE,
    avg_sentiment NUMERIC,
    article_count INTEGER,
    positive_ratio NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(na.published_date) as date,
        ROUND(AVG(sentiment_to_numeric(na.sentiment_score::TEXT))::NUMERIC, 2) as avg_sentiment,
        COUNT(*)::INTEGER as article_count,
        ROUND(
            (COUNT(*) FILTER (WHERE sentiment_to_numeric(na.sentiment_score::TEXT) > 0)::NUMERIC / 
             COUNT(*)::NUMERIC * 100), 2
        ) as positive_ratio
    FROM news_articles na
    WHERE na.company_id = p_company_id
        AND (p_stakeholder_type IS NULL OR na.stakeholder_type::TEXT = p_stakeholder_type)
        AND DATE(na.published_date) BETWEEN p_start_date AND p_end_date
        AND na.sentiment_score IS NOT NULL
    GROUP BY DATE(na.published_date)
    ORDER BY DATE(na.published_date);
END;
$$ LANGUAGE plpgsql;

-- 커스텀 함수: 키워드 빈도 분석
CREATE OR REPLACE FUNCTION analyze_keyword_frequency(
    p_company_id INTEGER,
    p_start_date DATE,
    p_end_date DATE,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE(
    keyword TEXT,
    frequency INTEGER,
    avg_sentiment NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        keyword_item.value::TEXT as keyword,
        COUNT(*)::INTEGER as frequency,
        ROUND(AVG(sentiment_to_numeric(na.sentiment_score::TEXT))::NUMERIC, 2) as avg_sentiment
    FROM news_articles na,
         jsonb_array_elements_text(na.keywords) as keyword_item
    WHERE na.company_id = p_company_id
        AND DATE(na.published_date) BETWEEN p_start_date AND p_end_date
        AND na.keywords IS NOT NULL
        AND na.sentiment_score IS NOT NULL
    GROUP BY keyword_item.value::TEXT
    HAVING COUNT(*) >= 2  -- 최소 2번 이상 언급된 키워드만
    ORDER BY frequency DESC, avg_sentiment DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 뷰: 회사별 최신 센티멘트 요약
CREATE OR REPLACE VIEW company_sentiment_summary AS
SELECT 
    c.id as company_id,
    c.name as company_name,
    c.stock_code,
    COUNT(na.id) as total_articles,
    COUNT(na.id) FILTER (WHERE na.published_date >= CURRENT_DATE - INTERVAL '7 days') as articles_last_7days,
    COUNT(na.id) FILTER (WHERE na.published_date >= CURRENT_DATE - INTERVAL '30 days') as articles_last_30days,
    ROUND(AVG(sentiment_to_numeric(na.sentiment_score::TEXT))::NUMERIC, 2) as avg_sentiment_all_time,
    ROUND(AVG(sentiment_to_numeric(na.sentiment_score::TEXT)) FILTER (
        WHERE na.published_date >= CURRENT_DATE - INTERVAL '7 days'
    )::NUMERIC, 2) as avg_sentiment_7days,
    ROUND(AVG(sentiment_to_numeric(na.sentiment_score::TEXT)) FILTER (
        WHERE na.published_date >= CURRENT_DATE - INTERVAL '30 days'
    )::NUMERIC, 2) as avg_sentiment_30days,
    MAX(na.published_date) as latest_article_date
FROM companies c
LEFT JOIN news_articles na ON c.id = na.company_id
WHERE c.is_active = true
GROUP BY c.id, c.name, c.stock_code;

-- 뷰: 스테이크홀더별 센티멘트 분포
CREATE OR REPLACE VIEW stakeholder_sentiment_distribution AS
SELECT 
    c.name as company_name,
    na.stakeholder_type,
    COUNT(*) as total_articles,
    COUNT(*) FILTER (WHERE sentiment_to_numeric(na.sentiment_score::TEXT) = -2) as very_negative_count,
    COUNT(*) FILTER (WHERE sentiment_to_numeric(na.sentiment_score::TEXT) = -1) as negative_count,
    COUNT(*) FILTER (WHERE sentiment_to_numeric(na.sentiment_score::TEXT) = 0) as neutral_count,
    COUNT(*) FILTER (WHERE sentiment_to_numeric(na.sentiment_score::TEXT) = 1) as positive_count,
    COUNT(*) FILTER (WHERE sentiment_to_numeric(na.sentiment_score::TEXT) = 2) as very_positive_count,
    ROUND(AVG(sentiment_to_numeric(na.sentiment_score::TEXT))::NUMERIC, 2) as avg_sentiment
FROM companies c
JOIN news_articles na ON c.id = na.company_id
WHERE na.sentiment_score IS NOT NULL
    AND na.stakeholder_type IS NOT NULL
    AND na.published_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY c.name, na.stakeholder_type
ORDER BY c.name, na.stakeholder_type;

-- 트리거: 뉴스 기사 삽입/업데이트시 센티멘트 트렌드 자동 업데이트
CREATE OR REPLACE FUNCTION update_sentiment_trends()
RETURNS TRIGGER AS $$
BEGIN
    -- 해당 날짜의 센티멘트 트렌드 업데이트
    INSERT INTO sentiment_trends (
        company_id, 
        stakeholder_type, 
        date,
        total_articles,
        positive_count,
        negative_count,
        neutral_count,
        avg_sentiment_score
    )
    SELECT 
        NEW.company_id,
        NEW.stakeholder_type,
        DATE(NEW.published_date),
        COUNT(*),
        COUNT(*) FILTER (WHERE sentiment_to_numeric(sentiment_score::TEXT) > 0),
        COUNT(*) FILTER (WHERE sentiment_to_numeric(sentiment_score::TEXT) < 0),
        COUNT(*) FILTER (WHERE sentiment_to_numeric(sentiment_score::TEXT) = 0),
        AVG(sentiment_to_numeric(sentiment_score::TEXT))
    FROM news_articles
    WHERE company_id = NEW.company_id
        AND stakeholder_type = NEW.stakeholder_type
        AND DATE(published_date) = DATE(NEW.published_date)
        AND sentiment_score IS NOT NULL
    GROUP BY company_id, stakeholder_type, DATE(published_date)
    ON CONFLICT (company_id, stakeholder_type, date)
    DO UPDATE SET
        total_articles = EXCLUDED.total_articles,
        positive_count = EXCLUDED.positive_count,
        negative_count = EXCLUDED.negative_count,
        neutral_count = EXCLUDED.neutral_count,
        avg_sentiment_score = EXCLUDED.avg_sentiment_score;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성 (뉴스 기사에 센티멘트가 추가/업데이트될 때)
DROP TRIGGER IF EXISTS trigger_update_sentiment_trends ON news_articles;
CREATE TRIGGER trigger_update_sentiment_trends
    AFTER INSERT OR UPDATE OF sentiment_score, stakeholder_type
    ON news_articles
    FOR EACH ROW
    WHEN (NEW.sentiment_score IS NOT NULL AND NEW.stakeholder_type IS NOT NULL)
    EXECUTE FUNCTION update_sentiment_trends();

-- 파티셔닝을 위한 함수 (대용량 데이터 처리용)
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, year INTEGER, month INTEGER)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_name := table_name || '_y' || year || 'm' || LPAD(month::TEXT, 2, '0');
    start_date := DATE(year || '-' || month || '-01');
    end_date := start_date + INTERVAL '1 month';
    
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
        FOR VALUES FROM (%L) TO (%L)',
        partition_name, table_name, start_date, end_date
    );
    
    RAISE NOTICE '파티션 테이블 % 생성 완료', partition_name;
END;
$$ LANGUAGE plpgsql;

-- 성능 모니터링을 위한 뷰
CREATE OR REPLACE VIEW database_performance_stats AS
SELECT 
    schemaname,
    tablename,
    attname as column_name,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY tablename, attname;

-- 인덱스 사용률 모니터링 뷰
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        ELSE 'ACTIVE'
    END as usage_status
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 초기 관리자 계정 생성 (비밀번호: admin123)
-- 해시된 비밀번호: bcrypt로 생성된 해시값
INSERT INTO users (email, password_hash, full_name, role, is_active) 
VALUES (
    'admin@sentiment-analysis.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewEyD7TDdlgmWj9W', 
    'System Administrator', 
    'admin',
    true
) ON CONFLICT (email) DO NOTHING;

-- 샘플 회사 데이터 삽입
INSERT INTO companies (name, stock_code, industry, description, website_url, is_active) VALUES
('삼성전자', '005930', '전자/IT', '글로벌 전자 및 IT 기업', 'https://www.samsung.com', true),
('SK하이닉스', '000660', '반도체', '메모리 반도체 전문 기업', 'https://www.skhynix.com', true),
('NAVER', '035420', '인터넷/플랫폼', '국내 최대 검색 포털 및 IT 서비스 기업', 'https://www.navercorp.com', true),
('카카오', '035720', '인터넷/플랫폼', '모바일 메신저 및 플랫폼 서비스 기업', 'https://www.kakaocorp.com', true),
('LG전자', '066570', '전자/가전', '글로벌 가전 및 전자 제품 제조업체', 'https://www.lge.co.kr', true)
ON CONFLICT (name) DO NOTHING;

-- 시스템 설정 초기값
INSERT INTO system_configs (key, value, description) VALUES
('crawling_interval_hours', '6', '뉴스 크롤링 주기 (시간)'),
('sentiment_analysis_model', 'klue/bert-base', '사용할 센티멘트 분석 모델'),
('max_articles_per_crawling', '1000', '한 번의 크롤링에서 수집할 최대 기사 수'),
('alert_email_enabled', 'true', '이메일 알림 활성화 여부'),
('data_retention_days', '365', '데이터 보관 기간 (일)'),
('api_rate_limit_per_minute', '1000', '분당 API 호출 제한'),
('sentiment_confidence_threshold', '0.7', '센티멘트 분석 신뢰도 임계값')
ON CONFLICT (key) DO NOTHING;

-- 성능 최적화를 위한 VACUUM 및 ANALYZE
VACUUM ANALYZE;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '=================================================';
    RAISE NOTICE '멀티 스테이크홀더 센티멘트 분석 플랫폼 DB 초기화 완료';
    RAISE NOTICE '=================================================';
    RAISE NOTICE '관리자 계정: admin@sentiment-analysis.com';
    RAISE NOTICE '비밀번호: admin123';
    RAISE NOTICE '샘플 회사 데이터: 5개 회사 등록됨';
    RAISE NOTICE '=================================================';
END $$;