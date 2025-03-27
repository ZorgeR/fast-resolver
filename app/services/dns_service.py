import dns.resolver
from dns.asyncresolver import Resolver
import dns.reversename
from loguru import logger
import socket
import asyncio
from typing import Dict, Any, List, Optional
import dns.dnssec


class DNSService:
    def __init__(self):
        self.resolver = Resolver()
        # Use default DNS servers
        self.resolver.nameservers = ['8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1']
    
    async def lookup(self, domain: str, record_type: str = 'A', dnssec: bool = False) -> Dict[str, Any]:
        """
        Perform a DNS lookup for the given domain and record type
        
        Args:
            domain: Domain name to resolve
            record_type: DNS record type (A, AAAA, MX, TXT, etc.)
            dnssec: Whether to perform DNSSEC validation
        """
        try:
            # Configure DNSSEC validation if requested
            if dnssec:
                self.resolver.use_dnssec = True
                self.resolver.want_dnssec = True
            else:
                self.resolver.use_dnssec = False
                self.resolver.want_dnssec = False
            
            answers = await self.resolver.resolve(domain, record_type)
            results = [str(answer) for answer in answers]
            
            # Include DNSSEC information if requested and available
            dnssec_info = {}
            if dnssec:
                dnssec_info = self._get_dnssec_info(answers)
            
            response = {
                "domain": domain,
                "record_type": record_type,
                "results": results,
                "status": "success"
            }
            
            # Add DNSSEC info if available
            if dnssec and dnssec_info:
                response["dnssec"] = dnssec_info
            
            return response
        except dns.resolver.NXDOMAIN:
            return {
                "domain": domain,
                "record_type": record_type,
                "results": [],
                "status": "error",
                "error": "Domain does not exist"
            }
        except dns.resolver.NoAnswer:
            return {
                "domain": domain,
                "record_type": record_type,
                "results": [],
                "status": "error",
                "error": "No records of the requested type"
            }
        except Exception as e:
            return {
                "domain": domain,
                "record_type": record_type,
                "results": [],
                "status": "error",
                "error": str(e)
            }
    
    def _get_dnssec_info(self, answers) -> Dict[str, Any]:
        """
        Extract DNSSEC information from DNS answers
        """
        try:
            dnssec_info = {
                "validated": answers.response.flags & dns.flags.AD,  # Authenticated Data flag
                "secure": answers.response.flags & dns.flags.CD,    # Checking Disabled flag
                "has_signatures": False
            }
            
            # Check for RRSIG records
            if hasattr(answers, 'response') and answers.response.additional:
                for rrset in answers.response.additional:
                    if rrset.rdtype == dns.rdatatype.RRSIG:
                        dnssec_info["has_signatures"] = True
                        break
            
            return dnssec_info
        except Exception as e:
            logger.error(f"Error getting DNSSEC info: {e}")
            return {"error": str(e)}
    
    async def reverse_lookup(self, ip: str, dnssec: bool = False) -> Dict[str, Any]:
        """
        Perform a reverse DNS lookup for the given IP address
        
        Args:
            ip: IP address to lookup
            dnssec: Whether to perform DNSSEC validation
        """
        try:
            # Configure DNSSEC validation if requested
            if dnssec:
                self.resolver.use_dnssec = True
                self.resolver.want_dnssec = True
            else:
                self.resolver.use_dnssec = False
                self.resolver.want_dnssec = False
                
            reverse_name = dns.reversename.from_address(ip)
            answers = await self.resolver.resolve(reverse_name, 'PTR')
            results = [str(answer) for answer in answers]
            
            # Include DNSSEC information if requested and available
            dnssec_info = {}
            if dnssec:
                dnssec_info = self._get_dnssec_info(answers)
            
            response = {
                "ip": ip,
                "domains": results,
                "status": "success"
            }
            
            # Add DNSSEC info if available
            if dnssec and dnssec_info:
                response["dnssec"] = dnssec_info
                
            return response
        except dns.resolver.NXDOMAIN:
            return {
                "ip": ip,
                "domains": [],
                "status": "error",
                "error": "No reverse DNS records found"
            }
        except Exception as e:
            return {
                "ip": ip,
                "domains": [],
                "status": "error",
                "error": str(e)
            }
    
    async def resolve_ptr(self, ip: str, dnssec: bool = False) -> Dict[str, Any]:
        """
        Resolve PTR record for the given IP address
        
        Args:
            ip: IP address to resolve PTR record for
            dnssec: Whether to perform DNSSEC validation
        """
        # This is essentially the same as reverse_lookup
        return await self.reverse_lookup(ip, dnssec) 