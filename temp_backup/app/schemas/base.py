"""
기본 스키마 클래스들
"""

from typing import Optional, Any, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class BaseSchema(BaseModel):
    """기본 스키마 클래스"""
    
    class Config:
        orm_mode = True
        use_enum_values = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ResponseSchema(BaseSchema):
    """기본 응답 스키마"""
    
    success: bool = True
    message: str = "성공"
    data: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None


class PaginationSchema(BaseSchema):
    """페이지네이션 스키마"""
    
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(20, ge=1, le=100, description="페이지 크기")
    total: Optional[int] = Field(None, description="전체 항목 수")
    pages: Optional[int] = Field(None, description="전체 페이지 수")
    
    @model_validator(mode='after')
    def calculate_pages(self):
        if self.total is not None and self.size is not None:
            self.pages = (self.total + self.size - 1) // self.size
        return self


class PaginatedResponseSchema(ResponseSchema):
    """페이지네이션 응답 스키마"""
    
    data: List[Any]
    pagination: PaginationSchema


class ErrorSchema(BaseSchema):
    """에러 응답 스키마"""
    
    code: int
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str
    request_id: Optional[str] = None


class ErrorResponseSchema(BaseSchema):
    """에러 응답 래퍼 스키마"""
    
    success: bool = False
    error: ErrorSchema


class FilterSchema(BaseSchema):
    """필터링 스키마"""
    
    search: Optional[str] = Field(None, description="검색어")
    sort_by: Optional[str] = Field(None, description="정렬 기준")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="정렬 순서")
    date_from: Optional[datetime] = Field(None, description="시작 날짜")
    date_to: Optional[datetime] = Field(None, description="종료 날짜")


class BulkOperationSchema(BaseSchema):
    """벌크 작업 스키마"""
    
    ids: List[int] = Field(..., description="대상 ID 목록")
    action: str = Field(..., description="수행할 작업")
    parameters: Optional[Dict[str, Any]] = Field(None, description="작업 매개변수")


class BulkOperationResultSchema(BaseSchema):
    """벌크 작업 결과 스키마"""
    
    total: int = Field(..., description="전체 대상 수")
    success: int = Field(..., description="성공한 작업 수")
    failed: int = Field(..., description="실패한 작업 수")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="오류 목록")


class HealthCheckSchema(BaseSchema):
    """헬스체크 스키마"""
    
    status: str
    timestamp: float
    version: str
    environment: str
    database: Dict[str, Any]
    redis: Dict[str, Any]


class MetricsSchema(BaseSchema):
    """메트릭 스키마"""
    
    name: str
    value: float
    timestamp: datetime
    labels: Optional[Dict[str, str]] = None