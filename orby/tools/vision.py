"""Vision tool for Orby using local vision models."""
from ..tools import Tool
from typing import Dict, Any
import base64
from PIL import Image
import io
import os
from pathlib import Path


class VisionTool(Tool):
    """Tool to process images and screenshots with local vision models."""
    
    def __init__(self):
        super().__init__(
            name="vision",
            description="Process images and screenshots with local vision models"
        )
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
    
    async def execute(self, image_path: str = None, image_data: str = None, 
                     operation: str = "describe", **kwargs) -> Dict[str, Any]:
        """Process an image."""
        try:
            # Load image
            if image_data:
                # Image data is base64 encoded
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
            elif image_path:
                # Load from file path
                if not os.path.exists(image_path):
                    return {
                        "status": "error",
                        "error": f"Image file not found: {image_path}",
                        "output": ""
                    }
                
                # Check if file format is supported
                file_ext = Path(image_path).suffix.lower()
                if file_ext not in self.supported_formats:
                    return {
                        "status": "error",
                        "error": f"Unsupported image format: {file_ext}",
                        "output": ""
                    }
                
                image = Image.open(image_path)
            else:
                return {
                    "status": "error",
                    "error": "Either image_path or image_data must be provided",
                    "output": ""
                }
            
            # Process based on operation
            if operation == "describe":
                result = self._describe_image(image)
            elif operation == "ocr":
                result = self._extract_text(image)
            elif operation == "analyze":
                result = self._analyze_image(image)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported operation: {operation}",
                    "output": ""
                }
            
            return {
                "status": "success",
                "analysis": result,
                "image_format": image.format,
                "image_size": image.size,
                "output": f"Image processed successfully: {result}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "output": str(e)
            }
    
    def _describe_image(self, image: Image.Image) -> str:
        """Generate a description of the image."""
        # In a real implementation, this would use a vision model
        # For now, we'll generate a basic description
        
        width, height = image.size
        mode = image.mode
        
        description = f"A {width}x{height} pixel image in {mode} mode."
        
        # Add some basic analysis based on image properties
        if width > height:
            description += " This appears to be a landscape-oriented image."
        elif height > width:
            description += " This appears to be a portrait-oriented image."
        else:
            description += " This appears to be a square image."
        
        # Check for transparency
        if 'transparency' in image.info or 'A' in mode:
            description += " The image contains transparent areas."
        
        return description
    
    def _extract_text(self, image: Image.Image) -> str:
        """Extract text from image (OCR)."""
        # In a real implementation, this would use OCR (like pytesseract)
        # For now, return placeholder
        return "OCR functionality not implemented in this demo version."
    
    def _analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """Perform comprehensive image analysis."""
        width, height = image.size
        mode = image.mode
        
        analysis = {
            "dimensions": f"{width}x{height}",
            "aspect_ratio": round(width / height, 2) if height > 0 else 0,
            "mode": mode,
            "megapixels": round((width * height) / 1_000_000, 2),
            "has_transparency": 'transparency' in image.info or 'A' in mode
        }
        
        return analysis


# Import required modules
try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False