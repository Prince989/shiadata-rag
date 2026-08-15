from fastapi import APIRouter, HTTPException
from schemas.requests import StoryStepRequest
from schemas.responses import StoryStepResponse
from services.storyteller_service import StorytellerService

router = APIRouter(prefix="/api/v1/story", tags=["Interactive Storyteller"])
story_service = StorytellerService()

@router.post("/generate-step", response_model=StoryStepResponse)
def generate_story_step(request: StoryStepRequest):
    try:
        result = story_service.generate_next_step(
            topic=request.topic,
            previous_context=request.previous_context,
            user_prompt=request.user_prompt
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))