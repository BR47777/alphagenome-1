#!/usr/bin/env python3
"""
Enhanced API client for AlphaGenome with support for both SDK and REST API.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from alphagenome.data import genome
from alphagenome.models import dna_client
from utils.logging_config import get_logger, get_performance_monitor

logger = get_logger()
performance_monitor = get_performance_monitor()


class APIEndpoint(Enum):
    """Available API endpoints."""
    PREDICT_VARIANT = "/v1/predict/variant"
    PREDICT_INTERVAL = "/v1/predict/interval"
    PREDICT_SEQUENCE = "/v1/predict/sequence"
    GET_METADATA = "/v1/metadata"


@dataclass
class APIResponse:
    """Standardized API response."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None


class EnhancedAlphaGenomeClient:
    """Enhanced AlphaGenome client with REST API and SDK support."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.alphagenome.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.sdk_client = None
        self.session = None
        
        # Initialize SDK client as fallback
        try:
            self.sdk_client = dna_client.create(api_key)
            logger.info("SDK client initialized successfully")
        except Exception as e:
            logger.warning(f"SDK client initialization failed: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AlphaGenome-UI/1.0"
            },
            timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: APIEndpoint, data: Dict[str, Any]) -> APIResponse:
        """Make a REST API request."""
        if not self.session:
            return APIResponse(
                success=False,
                error="Session not initialized. Use async context manager."
            )
        
        url = f"{self.base_url}{endpoint.value}"
        start_time = time.time()
        
        try:
            logger.info(f"Making API request to {endpoint.value}")
            performance_monitor.start_timer(f"api_request_{endpoint.value}")
            
            async with self.session.post(url, json=data) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                
                performance_monitor.end_timer(
                    f"api_request_{endpoint.value}",
                    {"status_code": response.status, "response_time": response_time}
                )
                
                if response.status == 200:
                    logger.info(f"API request successful: {endpoint.value}")
                    return APIResponse(
                        success=True,
                        data=response_data,
                        status_code=response.status,
                        response_time=response_time
                    )
                else:
                    error_msg = response_data.get("error", f"HTTP {response.status}")
                    logger.error(f"API request failed: {endpoint.value} - {error_msg}")
                    return APIResponse(
                        success=False,
                        error=error_msg,
                        status_code=response.status,
                        response_time=response_time
                    )
                    
        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            logger.error(f"Network error for {endpoint.value}: {e}")
            return APIResponse(
                success=False,
                error=f"Network error: {str(e)}",
                response_time=response_time
            )
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Unexpected error for {endpoint.value}: {e}")
            return APIResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
                response_time=response_time
            )
    
    async def predict_variant_rest(self, chromosome: str, position: int, 
                                 ref: str, alt: str, organism: str = "human") -> APIResponse:
        """Predict variant effects using REST API."""
        data = {
            "chromosome": chromosome,
            "position": position,
            "ref": ref,
            "alt": alt,
            "organism": organism
        }
        
        return await self._make_request(APIEndpoint.PREDICT_VARIANT, data)
    
    async def predict_interval_rest(self, chromosome: str, start: int, end: int,
                                  organism: str = "human", 
                                  output_types: List[str] = None) -> APIResponse:
        """Predict interval effects using REST API."""
        data = {
            "chromosome": chromosome,
            "start": start,
            "end": end,
            "organism": organism
        }
        
        if output_types:
            data["output_types"] = output_types
            
        return await self._make_request(APIEndpoint.PREDICT_INTERVAL, data)
    
    async def predict_sequence_rest(self, sequence: str, organism: str = "human",
                                  output_types: List[str] = None) -> APIResponse:
        """Predict sequence effects using REST API."""
        data = {
            "sequence": sequence,
            "organism": organism
        }
        
        if output_types:
            data["output_types"] = output_types
            
        return await self._make_request(APIEndpoint.PREDICT_SEQUENCE, data)
    
    def predict_variant_sdk(self, interval: genome.Interval, variant: genome.Variant,
                           ontology_terms: List[str], requested_outputs: List[str]):
        """Predict variant effects using SDK (fallback)."""
        if not self.sdk_client:
            raise RuntimeError("SDK client not available")
        
        logger.info("Using SDK client for variant prediction")
        performance_monitor.start_timer("sdk_variant_prediction")
        
        try:
            result = self.sdk_client.predict_variant(
                interval=interval,
                variant=variant,
                ontology_terms=ontology_terms,
                requested_outputs=requested_outputs
            )
            
            performance_monitor.end_timer("sdk_variant_prediction")
            return result
            
        except Exception as e:
            performance_monitor.end_timer("sdk_variant_prediction")
            logger.error(f"SDK variant prediction failed: {e}")
            raise
    
    async def predict_variant_hybrid(self, chromosome: str, position: int,
                                   ref: str, alt: str, organism: str = "human",
                                   interval_size: int = 100000) -> APIResponse:
        """Hybrid prediction: try REST API first, fallback to SDK."""
        
        # Try REST API first
        rest_response = await self.predict_variant_rest(chromosome, position, ref, alt, organism)
        
        if rest_response.success:
            logger.info("Used REST API for variant prediction")
            return rest_response
        
        # Fallback to SDK
        if self.sdk_client:
            try:
                logger.info("Falling back to SDK for variant prediction")
                
                # Create genomic objects for SDK
                start_pos = max(1, position - interval_size // 2)
                end_pos = position + interval_size // 2
                
                interval = genome.Interval(
                    chromosome=chromosome,
                    start=start_pos,
                    end=end_pos
                )
                
                variant = genome.Variant(
                    chromosome=chromosome,
                    position=position,
                    reference_bases=ref,
                    alternate_bases=alt
                )
                
                # Use SDK
                result = self.predict_variant_sdk(
                    interval=interval,
                    variant=variant,
                    ontology_terms=["UBERON:0001157"],  # Default tissue
                    requested_outputs=["RNA_SEQ"]  # Default output
                )
                
                # Convert SDK result to APIResponse format
                return APIResponse(
                    success=True,
                    data={
                        "prediction": "SDK_RESULT",
                        "reference": str(result.reference) if hasattr(result, 'reference') else None,
                        "alternate": str(result.alternate) if hasattr(result, 'alternate') else None,
                        "method": "SDK"
                    }
                )
                
            except Exception as e:
                logger.error(f"SDK fallback failed: {e}")
                return APIResponse(
                    success=False,
                    error=f"Both REST API and SDK failed. REST: {rest_response.error}, SDK: {str(e)}"
                )
        
        return rest_response
    
    async def get_metadata(self) -> APIResponse:
        """Get API metadata."""
        try:
            # Try REST API first
            response = await self._make_request(APIEndpoint.GET_METADATA, {})
            
            if response.success:
                return response
            
            # Fallback to SDK
            if self.sdk_client:
                metadata = self.sdk_client.output_metadata()
                return APIResponse(
                    success=True,
                    data={
                        "output_types": list(metadata.__dataclass_fields__.keys()),
                        "method": "SDK"
                    }
                )
            
            return response
            
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Failed to get metadata: {str(e)}"
            )


# Convenience functions for backward compatibility
async def create_enhanced_client(api_key: str) -> EnhancedAlphaGenomeClient:
    """Create and initialize enhanced client."""
    client = EnhancedAlphaGenomeClient(api_key)
    return client


# Example usage
async def example_usage():
    """Example of how to use the enhanced client."""
    api_key = "your_api_key_here"
    
    async with EnhancedAlphaGenomeClient(api_key) as client:
        # Test variant prediction
        response = await client.predict_variant_hybrid(
            chromosome="chr12",
            position=11223344,
            ref="G",
            alt="C",
            organism="human"
        )
        
        if response.success:
            print("Prediction successful!")
            print(f"Response time: {response.response_time:.2f}s")
            print(f"Data: {response.data}")
        else:
            print(f"Prediction failed: {response.error}")


if __name__ == "__main__":
    asyncio.run(example_usage())
