"""
Contract loader for SURA healthcare eligibility contracts.

This module handles loading, caching, and validation of contract configurations
from JSON files.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache

from .models import ContractInfo

logger = logging.getLogger(__name__)

# Path to contracts directory
CONTRACTS_DIR = Path(__file__).parent.parent.parent.parent / "config" / "contracts"


class ContractLoadError(Exception):
    """Exception raised when a contract cannot be loaded."""
    pass


class Contract:
    """Represents a loaded healthcare contract."""
    
    def __init__(self, data: Dict):
        """Initialize contract from JSON data."""
        self.contract_id: str = data["contract_id"]
        self.contract_name: str = data["contract_name"]
        self.description: str = data["description"]
        self.version: str = data["version"]
        self.active: bool = data.get("active", True)
        self.default: bool = data.get("default", False)
        self.eligibility_instructions: str = data["eligibility_instructions"]
        self.response_schema: Dict = data["response_schema"]
        
        logger.info(f"Loaded contract: {self.contract_id} v{self.version}")
    
    def to_info(self) -> ContractInfo:
        """Convert to ContractInfo model."""
        return ContractInfo(
            contract_id=self.contract_id,
            contract_name=self.contract_name,
            description=self.description,
            version=self.version,
            active=self.active,
            default=self.default
        )
    
    def validate(self) -> bool:
        """Validate contract structure."""
        required_fields = [
            "contract_id",
            "contract_name",
            "description",
            "version",
            "eligibility_instructions",
            "response_schema"
        ]
        
        for field in required_fields:
            if not hasattr(self, field) or getattr(self, field) is None:
                logger.error(f"Contract validation failed: missing {field}")
                return False
        
        if not self.eligibility_instructions.strip():
            logger.error("Contract validation failed: empty eligibility_instructions")
            return False
        
        if not isinstance(self.response_schema, dict):
            logger.error("Contract validation failed: invalid response_schema")
            return False
        
        return True


def _load_contract_file(contract_id: str) -> Dict:
    """
    Load contract JSON file.
    
    Args:
        contract_id: Contract identifier
        
    Returns:
        Contract data as dictionary
        
    Raises:
        ContractLoadError: If contract file cannot be loaded
    """
    contract_path = CONTRACTS_DIR / f"{contract_id}.json"
    
    if not contract_path.exists():
        raise ContractLoadError(f"Contract file not found: {contract_path}")
    
    try:
        with open(contract_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise ContractLoadError(f"Invalid JSON in contract file {contract_path}: {e}")
    except Exception as e:
        raise ContractLoadError(f"Error loading contract file {contract_path}: {e}")


@lru_cache(maxsize=32)
def load_contract(contract_id: str) -> Contract:
    """
    Load a contract by ID with caching.
    
    Args:
        contract_id: Contract identifier
        
    Returns:
        Loaded and validated Contract
        
    Raises:
        ContractLoadError: If contract cannot be loaded or is invalid
    """
    logger.info(f"Loading contract: {contract_id}")
    
    try:
        data = _load_contract_file(contract_id)
        contract = Contract(data)
        
        if not contract.validate():
            raise ContractLoadError(f"Contract validation failed: {contract_id}")
        
        return contract
        
    except ContractLoadError:
        raise
    except Exception as e:
        raise ContractLoadError(f"Unexpected error loading contract {contract_id}: {e}")


def list_contracts() -> List[ContractInfo]:
    """
    List all available contracts.
    
    Returns:
        List of ContractInfo objects for all available contracts
    """
    logger.info("Listing all available contracts")
    
    if not CONTRACTS_DIR.exists():
        logger.warning(f"Contracts directory not found: {CONTRACTS_DIR}")
        return []
    
    contracts = []
    
    for contract_file in CONTRACTS_DIR.glob("*.json"):
        contract_id = contract_file.stem
        
        try:
            contract = load_contract(contract_id)
            if contract.active:
                contracts.append(contract.to_info())
        except ContractLoadError as e:
            logger.error(f"Failed to load contract {contract_id}: {e}")
            continue
    
    # Sort contracts: default first, then by name
    contracts.sort(key=lambda c: (not c.default, c.contract_name))
    
    logger.info(f"Found {len(contracts)} active contracts")
    return contracts


def get_default_contract() -> Contract:
    """
    Get the default contract.
    
    Returns:
        Default Contract
        
    Raises:
        ContractLoadError: If no default contract is found
    """
    logger.info("Getting default contract")
    
    # First, try to find contract marked as default
    for contract_file in CONTRACTS_DIR.glob("*.json"):
        contract_id = contract_file.stem
        try:
            contract = load_contract(contract_id)
            if contract.default and contract.active:
                logger.info(f"Found default contract: {contract_id}")
                return contract
        except ContractLoadError:
            continue
    
    # Fallback: try litotripsia_ureteral
    try:
        contract = load_contract("litotripsia_ureteral")
        logger.info("Using litotripsia_ureteral as default contract")
        return contract
    except ContractLoadError:
        pass
    
    # Last resort: return first available contract
    contracts = list_contracts()
    if contracts:
        first_contract_id = contracts[0].contract_id
        logger.warning(f"No explicit default found, using first available: {first_contract_id}")
        return load_contract(first_contract_id)
    
    raise ContractLoadError("No contracts available")


def clear_contract_cache():
    """Clear the contract cache. Useful for reloading after updates."""
    load_contract.cache_clear()
    logger.info("Contract cache cleared")
