import time
import json
from typing import Callable, Dict, Any
from fastapi import Request, Response
from loguru import logger


async def log_request_middleware(request: Request, call_next: Callable):
    """Log request and response information"""
    start_time = time.time()
    
    # Get request info
    method = request.method
    path = request.url.path
    query_params = dict(request.query_params)
    client_ip = request.client.host if request.client else "unknown"
    
    # Extract API key from header if available
    api_key = request.headers.get("X-API-Key", "unknown")
    
    # Log request info
    logger.info(f"Request: {method} {path} from {client_ip} API Key: {api_key}")
    
    # Get response
    response = await call_next(request)
    
    # Calculate process time
    process_time = time.time() - start_time
    
    # Log response info
    logger.info(
        f"Response: {method} {path} status={response.status_code} "
        f"took={process_time:.4f}s API Key: {api_key}"
    )
    
    return response


async def log_dns_query(api_key: str, api_key_name: str, query_type: str, query: str, result: Dict[str, Any]):
    """Log DNS query information"""
    status = result.get("status", "unknown")
    
    # Check if DNSSEC was used and the result
    dnssec_info = result.get("dnssec", {})
    dnssec_validated = "validated" if dnssec_info.get("validated") else "not validated"
    dnssec_str = f" [DNSSEC: {dnssec_validated}]" if dnssec_info else ""
    
    if status == "success":
        if query_type in ["lookup", "reverse_lookup", "ptr"]:
            targets = result.get("results", []) if query_type == "lookup" else result.get("domains", [])
            target_str = ", ".join(targets) if targets else "no results"
            logger.info(f"DNS {query_type}: API Key '{api_key}' (name: {api_key_name}) queried '{query}' -> {target_str}{dnssec_str}")
        else:
            logger.info(f"DNS {query_type}: API Key '{api_key}' (name: {api_key_name}) queried '{query}' -> success{dnssec_str}")
    else:
        error = result.get("error", "unknown error")
        logger.warning(f"DNS {query_type}: API Key '{api_key}' (name: {api_key_name}) queried '{query}' -> error: {error}{dnssec_str}")


async def log_whois_query(api_key: str, api_key_name: str, domain: str, result: Dict[str, Any]):
    """Log WHOIS query information"""
    status = result.get("status", "unknown")
    
    if status == "success":
        registrar = result.get("registrar", "unknown")
        creation_date = result.get("creation_date", "unknown")
        logger.info(f"WHOIS: API Key '{api_key}' (name: {api_key_name}) queried '{domain}' -> Registrar: {registrar}, Created: {creation_date}")
    else:
        error = result.get("error", "unknown error")
        logger.warning(f"WHOIS: API Key '{api_key}' (name: {api_key_name}) queried '{domain}' -> error: {error}") 