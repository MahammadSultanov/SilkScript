
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import requests
import urllib.parse

app = FastAPI()

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model for carpet design data from frontend
class CarpetDesignRequest(BaseModel):
    design_style: str
    colors: List[str]  # List of colors (Color1, Color2, Color3, Color4)
    motifs: List[str]  # List of motifs
    aspect_ratio: Optional[str] = "4:3"  # Default aspect ratio
    additional_details: Optional[str] = ""  # Any additional design details

# Response model for API response
class GenerationResponse(BaseModel):
    success: bool
    message: str
    image_url: Optional[str] = None
    error: Optional[str] = None

def create_detailed_prompt(request: CarpetDesignRequest) -> str:
    """
    Create a detailed prompt for Azerbaijan Persian carpet generation
    based on frontend data
    """
    # Colors text
    colors_text = ", ".join(request.colors)
    
    # Motifs text with cultural details
    motifs_descriptions = []
    for motif in request.motifs:
        if motif.lower() == "palmette":
            motifs_descriptions.append("Palmette (traditional palm leaf motif)")
        elif motif.lower() == "rosette":
            motifs_descriptions.append("Rosette (circular floral design)")
        elif motif.lower() == "dragon":
            motifs_descriptions.append("Dragon (powerful symbolic motif)")
        elif motif.lower() == "bird":
            motifs_descriptions.append("Bird (freedom and nature symbol)")
        elif "geometric" in motif.lower():
            motifs_descriptions.append("intricate geometric patterns")
        elif "floral" in motif.lower():
            motifs_descriptions.append("traditional floral designs")
        elif "star" in motif.lower():
            motifs_descriptions.append("star medallions")
        elif "vine" in motif.lower():
            motifs_descriptions.append("vine scrolls")
        else:
            motifs_descriptions.append(f"{motif} motif")
    
    motifs_text = ", ".join(motifs_descriptions)
    
    # Create detailed prompt
    prompt = (
        f"A highly detailed, traditional Persian and Azerbaijan carpet design in the style of {request.design_style}, "
        f"featuring {motifs_text}, clearly visible in the carpet design. "
        f"Intricate floral and geometric patterns, rich textures, and authentic weaving. "
        f"Color palette: {colors_text}. "
        f"Ornate, symmetrical, museum-quality, high-resolution, vibrant, "
        f"inspired by historical carpets from Shirvan, Karabagh, and the Caucasus region."
    )
    
    # Add additional details if provided
    if request.additional_details:
        prompt += f" {request.additional_details}."
    
    return prompt

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Azerbaijan Carpet Design Generator API",
        "version": "1.0.0",
        "endpoints": {
            "/generate": "POST - Generate carpet design",
            "/options": "GET - Get available options",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "carpet-design-generator"}

@app.post("/generate", response_model=GenerationResponse)
async def generate_carpet_design(request: CarpetDesignRequest):
    """
    Generate Azerbaijan carpet design from frontend data
    
    Expected JSON format:
    {
      "design_style": "Tabriz",
      "colors": ["Deep Red", "Navy Blue", "Golden Yellow"],
      "motifs": ["Palmette", "Rosette", "Dragon"],
      "aspect_ratio": "4:3",
      "additional_details": "optional details"
    }
    """
    try:
        # Validate input
        if not request.design_style:
            raise HTTPException(status_code=400, detail="Design style is required")
        
        if not request.colors or len(request.colors) == 0:
            raise HTTPException(status_code=400, detail="At least one color is required")
        
        if not request.motifs or len(request.motifs) == 0:
            raise HTTPException(status_code=400, detail="At least one motif is required")
        
        # Create detailed prompt from frontend data
        prompt = create_detailed_prompt(request)
        
        # URL encode the prompt for Pollinations API
        encoded_prompt = urllib.parse.quote(prompt)
        api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        
        # Call Pollinations API
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            return GenerationResponse(
                success=True,
                message="Carpet design generated successfully",
                image_url=api_url
            )
        else:
            return GenerationResponse(
                success=False,
                message="Failed to generate carpet design",
                error=f"API returned status code {response.status_code}"
            )
            
    except requests.RequestException as e:
        return GenerationResponse(
            success=False,
            message="Failed to generate carpet design",
            error=f"Network error: {str(e)}"
        )
    except Exception as e:
        return GenerationResponse(
            success=False,
            message="Failed to generate carpet design",
            error=f"Internal error: {str(e)}"
        )

@app.get("/options")
def get_options():
    """
    Get available design options for the frontend
    """
    return {
        "design_patterns": [
            "Tabriz",
            "Ganja", 
            "Shirvan",
            "Baku",
            "Karabagh",
            "Gazakh",
            "Kubba"
        ],
        "motifs": [
            "Palmette",
            "Rosette", 
            "Dragon",
            "Bird",
            "Geometric patterns",
            "Floral designs",
            "Star medallions",
            "Vine scrolls"
        ],
        "color_suggestions": [
            "Deep Red",
            "Navy Blue", 
            "Golden Yellow",
            "Dark Slate Gray",
            "Emerald Green",
            "Royal Purple",
            "Crimson",
            "Sapphire Blue"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)