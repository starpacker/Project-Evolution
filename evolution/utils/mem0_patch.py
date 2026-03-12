"""
Mem0 Monkey Patch for Aliyun Embedding Compatibility

This module patches Mem0's OpenAI embedding implementation to support
embedding models that don't accept the 'dimensions' parameter, such as
Aliyun's text-embedding-v4 model.

The patch conditionally passes the dimensions parameter only when it's
explicitly set and the model supports it.
"""

import logging
from typing import Literal, Optional

logger = logging.getLogger(__name__)


def patch_mem0_embedding():
    """
    Monkey patch Mem0's OpenAI embedding to handle models that don't support dimensions parameter.
    
    This patch modifies the embed() method to:
    1. Check if embedding_dims is explicitly set
    2. Only pass dimensions parameter if it's set and not None
    3. Otherwise, let the API use its default dimensions
    """
    try:
        from mem0.embeddings.openai import OpenAIEmbedding
        
        # Store original embed method
        original_embed = OpenAIEmbedding.embed
        
        def patched_embed(self, text, memory_action: Optional[Literal["add", "search", "update"]] = None):
            """
            Patched embed method that conditionally passes dimensions parameter.
            
            Args:
                text (str): The text to embed.
                memory_action (optional): The type of embedding to use.
                
            Returns:
                list: The embedding vector.
            """
            text = text.replace("\n", " ")
            
            # Build embedding request parameters
            embed_params = {
                "input": [text],
                "model": self.config.model,
            }
            
            # Check if model supports dimensions parameter
            # Aliyun models don't support dimensions parameter
            model_lower = self.config.model.lower()
            skip_dimensions = any(x in model_lower for x in ['aliyun', 'qwen', 'dashscope'])
            
            if not skip_dimensions and self.config.embedding_dims is not None:
                embed_params["dimensions"] = self.config.embedding_dims
                logger.debug(f"Using dimensions={self.config.embedding_dims} for model: {self.config.model}")
            else:
                logger.debug(f"Skipping dimensions parameter for model: {self.config.model}")
            
            return (
                self.client.embeddings.create(**embed_params)
                .data[0]
                .embedding
            )
        
        # Apply the patch
        OpenAIEmbedding.embed = patched_embed
        logger.info("✅ Successfully patched Mem0 OpenAI embedding for Aliyun compatibility")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ Could not patch Mem0: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error patching Mem0: {e}")
        return False


def apply_all_patches():
    """Apply all Mem0 compatibility patches."""
    success = patch_mem0_embedding()
    if success:
        logger.info("🎉 All Mem0 patches applied successfully")
    else:
        logger.warning("⚠️ Some Mem0 patches failed to apply")
    return success


# Auto-apply patches when module is imported
if __name__ != "__main__":
    apply_all_patches()
