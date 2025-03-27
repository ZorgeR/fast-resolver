from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Tuple
from loguru import logger

from app.models.api_key import ApiKey, ApiKeyCreate
from app.middleware.auth import get_api_key, get_admin_secret
from app.middleware.rate_limit import rate_limit_middleware
from app.middleware.logger import log_dns_query, log_whois_query
from app.services.dns_service import DNSService
from app.services.whois_service import WhoisService
from app.services.api_key_service import ApiKeyService

router = APIRouter()

# Initialize services
dns_service = DNSService()
whois_service = WhoisService()
api_key_service = ApiKeyService()


@router.get("/dns/lookup", response_model=Dict[str, Any])
async def dns_lookup(
    domain: str = Query(..., description="Domain to lookup"),
    record_type: str = Query("A", description="DNS record type (A, AAAA, MX, TXT, etc.)"),
    dnssec: bool = Query(False, description="Whether to perform DNSSEC validation"),
    api_key_info: Tuple[str, ApiKey] = Depends(get_api_key)
):
    """
    Perform a DNS lookup for the given domain and record type
    """
    api_key, api_key_obj = api_key_info
    
    # Apply rate limiting
    await rate_limit_middleware(None, api_key, api_key_obj)
    
    # Perform DNS lookup
    result = await dns_service.lookup(domain, record_type, dnssec)
    
    # Log the query
    await log_dns_query(api_key, api_key_obj.name, "lookup", domain, result)
    
    return result


@router.get("/dns/reverse", response_model=Dict[str, Any])
async def reverse_dns_lookup(
    ip: str = Query(..., description="IP address to lookup"),
    dnssec: bool = Query(False, description="Whether to perform DNSSEC validation"),
    api_key_info: Tuple[str, ApiKey] = Depends(get_api_key)
):
    """
    Perform a reverse DNS lookup for the given IP address
    """
    api_key, api_key_obj = api_key_info
    
    # Apply rate limiting
    await rate_limit_middleware(None, api_key, api_key_obj)
    
    # Perform reverse DNS lookup
    result = await dns_service.reverse_lookup(ip, dnssec)
    
    # Log the query
    await log_dns_query(api_key, api_key_obj.name, "reverse_lookup", ip, result)
    
    return result


@router.get("/dns/ptr", response_model=Dict[str, Any])
async def resolve_ptr(
    ip: str = Query(..., description="IP address to resolve PTR record for"),
    dnssec: bool = Query(False, description="Whether to perform DNSSEC validation"),
    api_key_info: Tuple[str, ApiKey] = Depends(get_api_key)
):
    """
    Resolve PTR record for the given IP address
    """
    api_key, api_key_obj = api_key_info
    
    # Apply rate limiting
    await rate_limit_middleware(None, api_key, api_key_obj)
    
    # Resolve PTR record
    result = await dns_service.resolve_ptr(ip, dnssec)
    
    # Log the query
    await log_dns_query(api_key, api_key_obj.name, "ptr", ip, result)
    
    return result


@router.get("/whois", response_model=Dict[str, Any])
async def whois_lookup(
    domain: str = Query(..., description="Domain to lookup WHOIS information for"),
    exclude_empty: bool = Query(True, description="Whether to exclude empty fields from the response"),
    api_key_info: Tuple[str, ApiKey] = Depends(get_api_key)
):
    """
    Perform a WHOIS lookup for the given domain
    """
    api_key, api_key_obj = api_key_info
    
    # Apply rate limiting
    await rate_limit_middleware(None, api_key, api_key_obj)
    
    # Perform WHOIS lookup
    result = await whois_service.lookup(domain, exclude_empty)
    
    # Log the query
    await log_whois_query(api_key, api_key_obj.name, domain, result)
    
    return result


# API Key management endpoints
@router.post("/admin/api-keys", response_model=ApiKey)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    _: str = Depends(get_admin_secret)  # Require admin secret
):
    """
    Create a new API key
    """
    return await api_key_service.create_api_key(api_key_data)


@router.get("/admin/api-keys", response_model=List[ApiKey])
async def get_api_keys(
    _: str = Depends(get_admin_secret)  # Require admin secret
):
    """
    Get all API keys
    """
    return await api_key_service.get_all_api_keys()


@router.delete("/admin/api-keys/{api_key}", response_model=Dict[str, bool])
async def deactivate_api_key(
    api_key: str,
    _: str = Depends(get_admin_secret)  # Require admin secret
):
    """
    Deactivate an API key
    """
    success = await api_key_service.deactivate_api_key(api_key)
    return {"success": success} 