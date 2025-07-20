from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import uuid
import requests
import asyncio
from datetime import datetime
import aiofiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Interactive Storytelling API",
    description="FastAPI application for interactive storytelling with Gemini AI integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL")
STORIES_DIR = os.getenv("STORIES_DIR", "./stories")
DATA_DIR = os.getenv("DATA_DIR", "./data")
PREVIOUS_ANSWERS_FILE = os.path.join(DATA_DIR, "previous_answers.json")

# Pydantic models
class StartStoryRequest(BaseModel):
    story_name: str
    max_choices: Optional[int] = 15  # Max story progression choices (10-50)

class ContinueStoryRequest(BaseModel):
    story_name: str
    session_id: str
    choice_text: str

class StoryResponse(BaseModel):
    introduction: Optional[str] = None
    text: str
    mood: str
    choices: Optional[List[str]] = None
    cultural_info: Optional[str] = None  # Cultural/traditional information
    story_similarity: Optional[float] = None  # How similar user's path was to original (0-1)
    session_id: Optional[str] = None
    choices_remaining: Optional[int] = None

class ErrorResponse(BaseModel):
    error: str
    message: str

# Available stories mapping
AVAILABLE_STORIES = {
    "koroghlu": "koroghlu.txt",
    "khoroglu": "koroghlu.txt",  # Alternative spelling
    "dedegorgud": "dedegorgud.txt",
    "dede_gorgud": "dedegorgud.txt"  # Alternative spelling
}

class StoryManager:
    def __init__(self):
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory and files exist"""
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(PREVIOUS_ANSWERS_FILE):
            with open(PREVIOUS_ANSWERS_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)
    
    async def read_story_file(self, story_name: str) -> str:
        """Read story content from file"""
        if story_name.lower() not in AVAILABLE_STORIES:
            raise HTTPException(
                status_code=404, 
                detail=f"Story '{story_name}' not found. Available stories: {list(AVAILABLE_STORIES.keys())}"
            )
        
        filename = AVAILABLE_STORIES[story_name.lower()]
        filepath = os.path.join(STORIES_DIR, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=404,
                detail=f"Story file '{filename}' not found"
            )
        
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                content = await f.read()
                return content
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error reading story file: {str(e)}"
            )
    
    async def load_previous_answers(self) -> Dict[str, Any]:
        """Load previous answers from JSON file"""
        try:
            async with aiofiles.open(PREVIOUS_ANSWERS_FILE, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content) if content.strip() else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    async def save_previous_answers(self, data: Dict[str, Any]):
        """Save previous answers to JSON file"""
        try:
            async with aiofiles.open(PREVIOUS_ANSWERS_FILE, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error saving data: {str(e)}"
            )
    
    async def call_gemini_api(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API with the given prompt"""
        if not GEMINI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Gemini API key not configured"
            )
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        try:
            url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract text from Gemini response
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text = candidate["content"]["parts"][0]["text"]
                    return self.parse_gemini_response(text)
            
            raise HTTPException(
                status_code=500,
                detail="Invalid response from Gemini API"
            )
            
        except requests.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error calling Gemini API: {str(e)}"
            )
    
    def parse_gemini_response(self, text: str) -> Dict[str, Any]:
        """Parse Gemini API response text into structured data"""
        try:
            # Try to parse as JSON first
            if text.strip().startswith('{'):
                return json.loads(text)
            
            # If not JSON, parse structured text response
            lines = text.strip().split('\n')
            result = {}
            current_key = None
            current_value = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for key indicators
                if line.lower().startswith('introduction:'):
                    if current_key:
                        result[current_key] = '\n'.join(current_value).strip()
                    current_key = 'introduction'
                    current_value = [line.split(':', 1)[1].strip()]
                elif line.lower().startswith('text:') or line.lower().startswith('story:'):
                    if current_key:
                        result[current_key] = '\n'.join(current_value).strip()
                    current_key = 'text'
                    current_value = [line.split(':', 1)[1].strip()]
                elif line.lower().startswith('mood:'):
                    if current_key:
                        result[current_key] = '\n'.join(current_value).strip()
                    current_key = 'mood'
                    current_value = [line.split(':', 1)[1].strip()]
                elif line.lower().startswith('choices:'):
                    if current_key:
                        result[current_key] = '\n'.join(current_value).strip()
                    current_key = 'choices'
                    current_value = []
                elif line.lower().startswith('cultural_info:') or line.lower().startswith('cultural info:'):
                    if current_key:
                        result[current_key] = '\n'.join(current_value).strip()
                    current_key = 'cultural_info'
                    current_value = [line.split(':', 1)[1].strip()]
                elif line.lower().startswith('similarity:') or line.lower().startswith('story_similarity:'):
                    if current_key:
                        result[current_key] = '\n'.join(current_value).strip()
                    # Parse similarity score
                    similarity_text = line.split(':', 1)[1].strip()
                    try:
                        # Extract number from text like "0.75" or "75%" or "7.5/10"
                        import re
                        numbers = re.findall(r'(\d+\.?\d*)', similarity_text)
                        if numbers:
                            score = float(numbers[0])
                            if score > 1:  # Handle percentage or /10 scale
                                score = score / 100 if score <= 100 else score / 10
                            result['story_similarity'] = min(max(score, 0), 1)  # Clamp 0-1
                    except:
                        result['story_similarity'] = 0.5  # Default
                    current_key = None
                    current_value = []
                elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    # Choice item
                    if current_key == 'choices':
                        choice = line[1:].strip()
                        current_value.append(choice)
                elif current_key:
                    current_value.append(line)
            
            # Add the last key-value pair
            if current_key:
                if current_key == 'choices':
                    result[current_key] = current_value
                else:
                    result[current_key] = '\n'.join(current_value).strip()

            # --- Ensure choices is always a list ---
            if 'choices' in result:
                if isinstance(result['choices'], str):
                    # Split by newlines, semicolons, or periods
                    import re
                    split_choices = [c.strip('-•* 	') for c in re.split(r'[\n;\.]', result['choices']) if c.strip()]
                    result['choices'] = [c for c in split_choices if len(c) > 0]
                elif not isinstance(result['choices'], list):
                    result['choices'] = []

            return result
        except Exception as e:
            # Fallback: return basic structure with the raw text
            return {
                "text": text,
                "mood": "neutral",
                "choices": []
            }
    
    def create_start_prompt(self, story_content: str, story_name: str, max_choices: int = 15) -> str:
        """Create prompt for starting a story (English only, no summary/lesson required)"""
        mood_options = "neutral, tense, happy"
        return f"""You are a master storyteller creating an interactive adventure based on the epic tale of {story_name}.

Story Content:
{story_content[:3000]}...

The user has selected a total of {max_choices} steps for the story. Plan the story arc so that it feels complete, meaningful, and satisfying within exactly {max_choices} steps (including the ending). The story should have a clear beginning, middle, and end.

1. INTRODUCTION: A captivating opening that sets the scene (2-3 sentences)
2. TEXT: The current story situation that presents the protagonist at a decision point (4-6 sentences)
3. MOOD: One word describing the emotional tone (choose ONLY from: {mood_options})
4. CHOICES: Exactly 5 compelling choices that the protagonist can make (each choice should be 8-15 words)
5. CULTURAL_INFO: If there are cultural, traditional, or historical elements in this part of the story that might need explanation, provide a brief informative note (2-3 sentences). If no special cultural context is needed, omit this field.

Format your response as:
Introduction: [Your introduction here]
Text: [Your story text here]
Mood: [mood word - ONLY neutral, tense, or happy]
Choices:
- [Choice 1]
- [Choice 2]
- [Choice 3]
- [Choice 4]
- [Choice 5]
Cultural_Info: [Brief cultural explanation if needed, otherwise omit]

Make the story immersive and true to the epic's themes while allowing for player agency."""
    
    def create_continue_prompt(self, story_content: str, story_name: str, choice_text: str, history: List[Dict], choices_made: int = 0, max_choices: int = 15) -> str:
        """Create prompt for continuing a story (English only, no summary/lesson required)"""
        history_text = ""
        if history:
            history_text = "Previous story progression:\n"
            for i, entry in enumerate(history[-3:], 1):  # Last 3 entries for context
                history_text += f"{i}. {entry.get('node_text', '')} -> Choice: {entry.get('choice_text', '')}\n"
        choices_remaining = max_choices - choices_made
        should_end = choices_remaining <= 0
        mood_options = "neutral, tense, happy"
        ending_instruction = ""
        if should_end:
            ending_instruction = f"""
This should be the ENDING of the story. Provide a satisfying conclusion. The ending should feel complete and meaningful, not abrupt. Rate the similarity to the original epic."""
        return f"""Continue this interactive story based on the epic of {story_name}.

Original Story Context:
{story_content[:2000]}...

{history_text}

The protagonist chose: "{choice_text}"
Choices made so far: {choices_made}/{max_choices}
{ending_instruction}

Based on this choice, continue the story. Plan the story arc so that the narrative fits exactly {max_choices} steps, with a clear ending. {'' if should_end else f'You have {choices_remaining} choices remaining before the story must end.'}

For CONTINUATION (if choices remain), provide:
Text: [4-6 sentences describing what happens next and the new situation]
Mood: [one word - ONLY: {mood_options}]
Choices:
- [Choice 1: 8-15 words]
- [Choice 2: 8-15 words]
- [Choice 3: 8-15 words]
- [Choice 4: 8-15 words]
- [Choice 5: 8-15 words]
Cultural_Info: [Brief cultural explanation if needed for this part, otherwise omit]

For ENDING (when no choices remain OR natural story conclusion), provide:
Text: [4-6 sentences describing the conclusion]
Mood: [one word - ONLY: {mood_options}]
Similarity: [Rate 0.0-1.0 how closely the user's choices followed the original epic story. 1.0 = exactly like original, 0.5 = some similarities, 0.0 = completely different path]
Cultural_Info: [Brief cultural explanation if needed, otherwise omit]

Choose the format based on choices remaining and natural story progression. Make it engaging and true to the epic's spirit."""
    
# Initialize story manager
story_manager = StoryManager()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Interactive Storytelling API",
        "version": "1.0.0",
        "available_stories": list(AVAILABLE_STORIES.keys()),
        "endpoints": {
            "start_story": "/stories/start",
            "continue_story": "/stories/continue",
            "available_stories": "/stories/list"
        }
    }

@app.get("/stories/list")
async def list_stories():
    """Get list of available stories"""
    return {
        "available_stories": list(AVAILABLE_STORIES.keys()),
        "story_files": {name: filename for name, filename in AVAILABLE_STORIES.items()}
    }

@app.post("/stories/start", response_model=StoryResponse)
async def start_story(request: StartStoryRequest):
    """Start a new interactive story session"""
    try:
        # Validate max_choices
        if request.max_choices < 10 or request.max_choices > 50:
            raise HTTPException(
                status_code=400,
                detail="max_choices must be between 10 and 50"
            )
        
        # Read story content
        story_content = await story_manager.read_story_file(request.story_name)
        
        # Create prompt for Gemini API
        prompt = story_manager.create_start_prompt(story_content, request.story_name, request.max_choices)
        
        # Call Gemini API
        gemini_response = await story_manager.call_gemini_api(prompt)
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Load previous answers
        previous_answers = await story_manager.load_previous_answers()
        
        # Save initial session data
        session_data = {
            "story_name": request.story_name,
            "max_choices": request.max_choices,
            "choices_made": 0,
            "history": [],
            "current_node": gemini_response,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        previous_answers[session_id] = session_data
        await story_manager.save_previous_answers(previous_answers)
        
        # Prepare response
        response_data = {
            "session_id": session_id,
            "introduction": gemini_response.get("introduction", ""),
            "text": gemini_response.get("text", ""),
            "mood": gemini_response.get("mood", "neutral"),
            "choices": gemini_response.get("choices", []),
            "cultural_info": gemini_response.get("cultural_info"),
            "choices_remaining": request.max_choices
        }
        
        return StoryResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting story: {str(e)}"
        )

@app.post("/stories/continue", response_model=StoryResponse)
async def continue_story(request: ContinueStoryRequest):
    """Continue an existing story session"""
    try:
        # Load previous answers
        previous_answers = await story_manager.load_previous_answers()
        
        # Check if session exists
        if request.session_id not in previous_answers:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        session_data = previous_answers[request.session_id]
        
        # Verify story name matches
        if session_data["story_name"] != request.story_name:
            raise HTTPException(
                status_code=400,
                detail="Story name mismatch with session"
            )
        
        # Check if story is already completed
        current_choices = session_data.get("choices_made", 0)
        max_choices = session_data.get("max_choices", 15)
        
        if current_choices >= max_choices:
            raise HTTPException(
                status_code=400,
                detail="Story has already reached maximum choices limit"
            )
        
        # Read story content
        story_content = await story_manager.read_story_file(request.story_name)
        
        # Create continue prompt
        prompt = story_manager.create_continue_prompt(
            story_content,
            request.story_name,
            request.choice_text,
            session_data["history"],
            current_choices,
            max_choices
        )
        
        # Call Gemini API
        gemini_response = await story_manager.call_gemini_api(prompt)
        
        # Update session history
        history_entry = {
            "node_text": session_data["current_node"].get("text", ""),
            "choice_text": request.choice_text,
            "mood": session_data["current_node"].get("mood", "neutral"),
            "timestamp": datetime.now().isoformat()
        }
        
        session_data["history"].append(history_entry)
        session_data["current_node"] = gemini_response
        session_data["choices_made"] = current_choices + 1
        session_data["updated_at"] = datetime.now().isoformat()
        
        # Save updated session data
        previous_answers[request.session_id] = session_data
        await story_manager.save_previous_answers(previous_answers)
        
        # Prepare response
        choices_remaining = max_choices - (current_choices + 1)
        response_data = {
            "text": gemini_response.get("text", ""),
            "mood": gemini_response.get("mood", "neutral"),
            "cultural_info": gemini_response.get("cultural_info"),
            "choices_remaining": choices_remaining
        }
        
        # Add choices if this is a continuation (not an ending)
        if "choices" in gemini_response and gemini_response["choices"] and choices_remaining > 0:
            response_data["choices"] = gemini_response["choices"]
        
        # Add similarity if this is an ending
        if "story_similarity" in gemini_response:
            response_data["story_similarity"] = gemini_response["story_similarity"]
        
        return StoryResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error continuing story: {str(e)}"
        )

@app.get("/stories/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    try:
        previous_answers = await story_manager.load_previous_answers()
        
        if session_id not in previous_answers:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        return previous_answers[session_id]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving session: {str(e)}"
        )

@app.delete("/stories/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a story session"""
    try:
        previous_answers = await story_manager.load_previous_answers()
        
        if session_id not in previous_answers:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        del previous_answers[session_id]
        await story_manager.save_previous_answers(previous_answers)
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting session: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gemini_api_configured": bool(GEMINI_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn  
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )
