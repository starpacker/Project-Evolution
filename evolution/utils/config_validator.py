"""
Configuration validator for Evolution system.
Validates environment variables and settings at startup.

v0.2.1: Initial implementation.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger("evolution.config_validator")


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


def validate_config() -> Tuple[bool, List[str], List[str]]:
    """Validate all configuration settings.
    
    Returns:
        (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # ── LLM Configuration ──
    llm_api_key = os.environ.get("LLM_API_KEY")
    if not llm_api_key:
        errors.append("LLM_API_KEY is not set")
    elif len(llm_api_key) < 10:
        warnings.append("LLM_API_KEY seems too short, may be invalid")
    
    llm_base_url = os.environ.get("LLM_BASE_URL")
    if llm_base_url and not (llm_base_url.startswith("http://") or llm_base_url.startswith("https://")):
        errors.append(f"LLM_BASE_URL must start with http:// or https://, got: {llm_base_url}")
    
    llm_model = os.environ.get("LLM_MODEL")
    if not llm_model:
        warnings.append("LLM_MODEL not set, will use default")
    
    # ── Database Configuration ──
    evolution_root = os.environ.get("EVOLUTION_ROOT", "/data/evolution")
    root_path = Path(evolution_root)
    
    if not root_path.exists():
        try:
            root_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"[Config] Created EVOLUTION_ROOT directory: {evolution_root}")
        except Exception as e:
            errors.append(f"Cannot create EVOLUTION_ROOT directory {evolution_root}: {e}")
    elif not root_path.is_dir():
        errors.append(f"EVOLUTION_ROOT exists but is not a directory: {evolution_root}")
    
    # Check write permissions
    if root_path.exists():
        test_file = root_path / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            errors.append(f"EVOLUTION_ROOT is not writable: {e}")
    
    # ── Embedding Configuration ──
    embedding_provider = os.environ.get("EMBEDDING_PROVIDER", "openai")
    if embedding_provider not in ("openai", "huggingface", "ollama"):
        warnings.append(f"Unknown EMBEDDING_PROVIDER: {embedding_provider}")
    
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if embedding_provider == "openai" and not openai_api_key:
        warnings.append("EMBEDDING_PROVIDER is 'openai' but OPENAI_API_KEY is not set")
    
    # ── Notification Channels ──
    email_enabled = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
    if email_enabled:
        required_email_vars = ["EMAIL_SMTP_SERVER", "EMAIL_USERNAME", "EMAIL_PASSWORD", "EMAIL_TO"]
        for var in required_email_vars:
            if not os.environ.get(var):
                warnings.append(f"EMAIL_ENABLED=true but {var} is not set")
    
    tg_enabled = os.environ.get("TG_ENABLED", "false").lower() == "true"
    if tg_enabled:
        if not os.environ.get("TG_BOT_TOKEN"):
            warnings.append("TG_ENABLED=true but TG_BOT_TOKEN is not set")
        if not os.environ.get("TG_CHAT_ID"):
            warnings.append("TG_ENABLED=true but TG_CHAT_ID is not set")
    
    notion_enabled = os.environ.get("NOTION_ENABLED", "false").lower() == "true"
    if notion_enabled:
        if not os.environ.get("NOTION_TOKEN"):
            warnings.append("NOTION_ENABLED=true but NOTION_TOKEN is not set")
    
    # ── Numeric Configuration ──
    try:
        max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "8192"))
        if max_tokens < 100 or max_tokens > 200000:
            warnings.append(f"LLM_MAX_TOKENS={max_tokens} is outside reasonable range (100-200000)")
    except ValueError:
        errors.append("LLM_MAX_TOKENS must be an integer")
    
    try:
        temperature = float(os.environ.get("LLM_TEMPERATURE", "0.3"))
        if temperature < 0 or temperature > 2:
            warnings.append(f"LLM_TEMPERATURE={temperature} is outside valid range (0-2)")
    except ValueError:
        errors.append("LLM_TEMPERATURE must be a number")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_and_report() -> bool:
    """Validate config and log results. Returns True if valid."""
    is_valid, errors, warnings = validate_config()
    
    if errors:
        logger.error("=" * 60)
        logger.error("Configuration Validation FAILED")
        logger.error("=" * 60)
        for err in errors:
            logger.error(f"  ❌ {err}")
        logger.error("=" * 60)
    
    if warnings:
        logger.warning("Configuration Warnings:")
        for warn in warnings:
            logger.warning(f"  ⚠️  {warn}")
    
    if is_valid and not warnings:
        logger.info("✅ Configuration validation passed")
    elif is_valid:
        logger.info("✅ Configuration validation passed (with warnings)")
    
    return is_valid


def get_config_summary() -> Dict[str, any]:
    """Get a summary of current configuration (safe for display)."""
    def mask_secret(value: str) -> str:
        """Mask sensitive values for display."""
        if not value or len(value) < 8:
            return "***"
        return value[:4] + "***" + value[-4:]
    
    llm_api_key = os.environ.get("LLM_API_KEY", "")
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    
    return {
        "llm": {
            "api_key": mask_secret(llm_api_key) if llm_api_key else "NOT_SET",
            "base_url": os.environ.get("LLM_BASE_URL", "NOT_SET"),
            "model": os.environ.get("LLM_MODEL", "NOT_SET"),
            "max_tokens": os.environ.get("LLM_MAX_TOKENS", "8192"),
            "temperature": os.environ.get("LLM_TEMPERATURE", "0.3"),
        },
        "database": {
            "root": os.environ.get("EVOLUTION_ROOT", "/data/evolution"),
        },
        "embedding": {
            "provider": os.environ.get("EMBEDDING_PROVIDER", "openai"),
            "model": os.environ.get("EMBEDDING_MODEL", "aliyun/text-embedding-v4"),
            "api_key": mask_secret(openai_api_key) if openai_api_key else "NOT_SET",
        },
        "notifications": {
            "email_enabled": os.environ.get("EMAIL_ENABLED", "false"),
            "telegram_enabled": os.environ.get("TG_ENABLED", "false"),
            "notion_enabled": os.environ.get("NOTION_ENABLED", "false"),
        },
    }
