from asyncwhois import aio_whois
from loguru import logger
from typing import Dict, Any, Optional


class WhoisService:
    async def lookup(self, domain: str, exclude_empty: bool = True) -> Dict[str, Any]:
        """
        Perform a WHOIS lookup for the given domain
        
        Args:
            domain: Domain to lookup
            exclude_empty: Whether to exclude fields with None values
        """
        try:
            whois_data = await aio_whois(domain)
            
            # The response is a tuple, with raw text at index 0 and parsed data at index 1
            raw_text = whois_data[0]
            parsed_data = whois_data[1]
            
            # Filter out empty values if requested
            if exclude_empty:
                parsed_data = {key: value for key, value in parsed_data.items() if value is not None}
            
            # Create a simplified response structure
            whois_info = {
                "domain": domain,
                "registrar": parsed_data.get("registrar"),
                "creation_date": parsed_data.get("creation_date"),
                "expiration_date": parsed_data.get("expiration_date"),
                "name_servers": parsed_data.get("name_servers"),
                "status": "success",
                "raw_text": raw_text,
                "parsed_data": parsed_data
            }
            
            return whois_info
        except Exception as e:
            logger.error(f"WHOIS lookup error for {domain}: {str(e)}")
            return {
                "domain": domain,
                "status": "error",
                "error": str(e)
            } 