from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Path, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .ai_utils import get_game_metadata
from .database import engine, get_db
from .models import Base, FamilyMember, Game, GameRating

app = FastAPI(title="GameDex", description="Board Game Collection Manager")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
async def index(
    request: Request, msg: Optional[str] = None, db: Session = Depends(get_db)
):
    """Home page with list of games"""
    games = db.query(Game).all()

    # Get family members and their ratings for all games
    family_members = db.query(FamilyMember).order_by(FamilyMember.name).all()
    family_ratings = {}

    for game in games:
        family_ratings[game.id] = {
            rating.family_member_id: rating.rating for rating in game.family_ratings
        }

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "games": games,
            "msg": msg,
            "family_members": family_members,
            "family_ratings": family_ratings,
        },
    )


@app.get("/settings")
async def settings_page(request: Request, db: Session = Depends(get_db)):
    """Settings page for managing family members"""
    family_members = db.query(FamilyMember).order_by(FamilyMember.name).all()
    return templates.TemplateResponse(
        request, "settings.html", {"family_members": family_members}
    )


@app.post("/settings/family-members")
async def add_family_member(name: str = Form(...), db: Session = Depends(get_db)):
    """Add a new family member"""
    # Check if name already exists
    existing = db.query(FamilyMember).filter(FamilyMember.name == name).first()
    if existing:
        return RedirectResponse(
            url="/settings?error=Family+member+already+exists", status_code=303
        )

    family_member = FamilyMember(name=name)
    db.add(family_member)
    db.commit()
    return RedirectResponse(
        url="/settings?msg=Family+member+added+successfully", status_code=303
    )


@app.delete("/settings/family-members/{member_id}")
async def delete_family_member(
    member_id: int = Path(..., gt=0), db: Session = Depends(get_db)
):
    """Delete a family member and all their ratings"""
    family_member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
    if not family_member:
        raise HTTPException(status_code=404, detail="Family member not found")

    db.delete(family_member)
    db.commit()
    return RedirectResponse(
        url="/settings?msg=Family+member+deleted+successfully", status_code=303
    )


@app.get("/games")
async def list_games(
    request: Request,
    search: Optional[str] = Query(None),
    game_type: Optional[str] = Query(None),
    complexity: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    msg: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all games with optional filtering and sorting"""
    query = db.query(Game)

    # Apply filters
    if search:
        query = query.filter(Game.title.ilike(f"%{search}%"))
    if game_type:
        query = query.filter(Game.game_type == game_type)
    if complexity:
        query = query.filter(Game.complexity == complexity)

    # Apply sorting
    if sort == "title":
        query = query.order_by(Game.title)
    elif sort == "rating":
        # Note: This sorting won't work properly without the old rating field
        # We'll need to implement a different approach for sorting by family ratings
        query = query.order_by(Game.id.desc())
    else:
        query = query.order_by(Game.id.desc())

    games = query.all()

    # Get family members and their ratings for all games
    family_members = db.query(FamilyMember).order_by(FamilyMember.name).all()
    family_ratings = {}

    for game in games:
        family_ratings[game.id] = {
            rating.family_member_id: rating.rating for rating in game.family_ratings
        }

    return templates.TemplateResponse(
        request,
        "games.html",
        {
            "games": games,
            "msg": msg,
            "family_members": family_members,
            "family_ratings": family_ratings,
        },
    )


@app.get("/games/new")
async def new_game_form(request: Request, db: Session = Depends(get_db)):
    """Form to add a new game"""
    family_members = db.query(FamilyMember).order_by(FamilyMember.name).all()
    return templates.TemplateResponse(
        request, "new_game.html", {"family_members": family_members}
    )


@app.post("/games")
async def create_game(
    request: Request,
    title: str = Form(...),
    player_count: Optional[str] = Form(None),
    game_type: Optional[str] = Form(None),
    playtime: Optional[str] = Form(None),
    complexity: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Create a new game"""
    game = Game(
        title=title,
        player_count=player_count or "",
        game_type=game_type or "",
        playtime=playtime or "",
        complexity=complexity or "",
        description=description or "",
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    # Handle family member ratings
    form_data = await request.form()
    family_members = db.query(FamilyMember).all()

    for member in family_members:
        rating_key = f"rating_{member.id}"
        if rating_key in form_data and form_data[rating_key]:
            try:
                rating_value = int(form_data[rating_key])
                if 1 <= rating_value <= 10:
                    game_rating = GameRating(
                        game_id=game.id, family_member_id=member.id, rating=rating_value
                    )
                    db.add(game_rating)
            except ValueError:
                pass  # Skip invalid ratings

    db.commit()
    return RedirectResponse(url="/?msg=Game+added+successfully", status_code=303)


@app.post("/games/autofill")
async def autofill_game_by_title(title: str = Form(...), db: Session = Depends(get_db)):
    """Create a game with just title and use AI to autofill metadata"""
    # Create game with just title
    game = Game(title=title)
    db.add(game)
    db.commit()
    db.refresh(game)

    # Use AI to get metadata
    metadata = await get_game_metadata(game.title)

    # Update game with AI metadata
    for key, value in metadata.items():
        if hasattr(game, key) and value:
            setattr(game, key, value)

    db.commit()
    db.refresh(game)
    return RedirectResponse(url=f"/games/{game.id}", status_code=303)


@app.get("/games/{game_id}")
async def get_game(
    request: Request,
    game_id: int = Path(..., gt=0),
    msg: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get a specific game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get family members and their ratings for this game
    family_members = db.query(FamilyMember).order_by(FamilyMember.name).all()
    family_ratings = {
        rating.family_member_id: rating.rating for rating in game.family_ratings
    }

    return templates.TemplateResponse(
        request,
        "game_detail.html",
        {
            "game": game,
            "msg": msg,
            "family_members": family_members,
            "family_ratings": family_ratings,
        },
    )


@app.get("/games/{game_id}/edit")
async def edit_game_form(
    request: Request,
    game_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """Form to edit an existing game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Get family members and their ratings for this game
    family_members = db.query(FamilyMember).order_by(FamilyMember.name).all()
    family_ratings = {
        rating.family_member_id: rating.rating for rating in game.family_ratings
    }

    return templates.TemplateResponse(
        request,
        "edit_game.html",
        {
            "game": game,
            "family_members": family_members,
            "family_ratings": family_ratings,
        },
    )


@app.get("/games/{game_id}/edit")
async def edit_game_form(
    request: Request,
    game_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """Form to edit an existing game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return templates.TemplateResponse(request, "edit_game.html", {"game": game})


@app.post("/games/{game_id}")
async def update_game(
    request: Request,
    game_id: int = Path(..., gt=0),
    title: str = Form(...),
    player_count: Optional[str] = Form(None),
    game_type: Optional[str] = Form(None),
    playtime: Optional[str] = Form(None),
    complexity: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Update a game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    game.title = title
    game.player_count = player_count or ""
    game.game_type = game_type or ""
    game.playtime = playtime or ""
    game.complexity = complexity or ""
    game.description = description or ""

    # Handle family member ratings
    form_data = await request.form()
    family_members = db.query(FamilyMember).all()

    # Clear existing ratings for this game
    db.query(GameRating).filter(GameRating.game_id == game_id).delete()

    # Add new ratings
    for member in family_members:
        rating_key = f"rating_{member.id}"
        if rating_key in form_data and form_data[rating_key]:
            try:
                rating_value = int(form_data[rating_key])
                if 1 <= rating_value <= 10:
                    game_rating = GameRating(
                        game_id=game.id, family_member_id=member.id, rating=rating_value
                    )
                    db.add(game_rating)
            except ValueError:
                pass  # Skip invalid ratings

    db.commit()
    db.refresh(game)
    return RedirectResponse(
        url=f"/games/{game_id}?msg=Game+updated+successfully", status_code=303
    )


@app.delete("/games/{game_id}")
async def delete_game(game_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Delete a game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    db.delete(game)
    db.commit()
    return RedirectResponse(url="/games?msg=Game+deleted+successfully", status_code=303)


@app.post("/games/{game_id}/autofill")
async def autofill_game(game_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Use AI to autofill game metadata"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Use AI to get metadata
    metadata = await get_game_metadata(game.title)

    # Update game with AI metadata
    for key, value in metadata.items():
        if hasattr(game, key) and value:
            setattr(game, key, value)

    db.commit()
    db.refresh(game)
    return RedirectResponse(url=f"/games/{game_id}", status_code=303)


@app.get("/recommend")
async def recommend_games(request: Request, db: Session = Depends(get_db)):
    """Game recommendation page"""
    return templates.TemplateResponse(request, "recommend.html", {})


@app.post("/recommend")
async def get_recommendations(
    request: Request, query: str = Form(...), db: Session = Depends(get_db)
):
    """Get AI-powered game recommendations"""
    # This would integrate with AI for recommendations
    games = db.query(Game).all()
    return templates.TemplateResponse(
        request, "recommendations.html", {"query": query, "games": games}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
