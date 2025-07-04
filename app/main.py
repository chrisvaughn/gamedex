import os
from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Path, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from .ai_utils import get_game_metadata, get_game_recommendations
from .auth import check_family_password, create_session_token, require_auth
from .database import engine, get_db
from .models import FamilyMember, Game, GameRating

app = FastAPI(title="GameDex", description="Board Game Collection Manager")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")


@app.head("/healthz")
@app.get("/healthz")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint that verifies database connectivity"""
    try:
        # Test database connection by executing a simple query
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "environment": (
                "production"
                if os.getenv("IS_PRODUCTION", "false").lower() == "true"
                else "development"
            ),
        }
    except Exception as e:
        import logging

        logging.error("Health check failed", exc_info=True)
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": "An internal error occurred.",
            "environment": (
                "production"
                if os.getenv("IS_PRODUCTION", "false").lower() == "true"
                else "development"
            ),
        }


@app.get("/login")
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(request, "login.html", {})


@app.post("/login")
async def login(
    request: Request,
    password: str = Form(...),
):
    """Handle login"""
    if check_family_password(password):
        session_token = create_session_token()
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="session",
            value=session_token,
            httponly=True,
            secure=os.getenv("IS_PRODUCTION", "false").lower() == "true",
            samesite="lax",
            max_age=86400,  # 24 hours
        )
        return response
    else:
        return templates.TemplateResponse(
            request, "login.html", {"error": "Invalid password"}
        )


@app.get("/logout")
async def logout():
    """Handle logout"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response


@app.get("/")
async def index(
    request: Request, msg: Optional[str] = None, db: Session = Depends(get_db)
):
    """Home page with list of games"""
    # Require authentication
    require_auth(request)

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


@app.get("/games")
async def list_games(
    request: Request,
    search: Optional[str] = Query(None),
    game_type: Optional[str] = Query(None),
    complexity: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    game_elements: Optional[str] = Query(None),
    setup_time: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Games list page with filtering and sorting"""
    # Require authentication
    require_auth(request)

    # Start with base query
    query = db.query(Game)

    # Apply search filter
    if search:
        query = query.filter(
            Game.title.ilike(f"%{search}%") | Game.description.ilike(f"%{search}%")
        )

    # Apply game type filter (LIKE for comma-separated values)
    if game_type:
        query = query.filter(Game.game_type.ilike(f"%{game_type}%"))

    # Apply game elements filter (LIKE for comma-separated values)
    if game_elements:
        query = query.filter(Game.game_elements.ilike(f"%{game_elements}%"))

    # Apply setup time filter (exact match or LIKE)
    if setup_time:
        query = query.filter(Game.setup_time.ilike(f"%{setup_time}%"))

    # Apply complexity filter
    if complexity:
        query = query.filter(Game.complexity == complexity)

    # Apply sorting
    if sort_by:
        if sort_by == "title":
            query = query.order_by(Game.title)
        elif sort_by == "created_at":
            query = query.order_by(Game.created_at.desc())
        elif sort_by == "updated_at":
            query = query.order_by(Game.updated_at.desc())
    else:
        # Default sorting by title
        query = query.order_by(Game.title)

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
        "index.html",
        {
            "games": games,
            "family_members": family_members,
            "family_ratings": family_ratings,
        },
    )


@app.get("/settings")
async def settings_page(request: Request, db: Session = Depends(get_db)):
    """Settings page for managing family members"""
    # Require authentication
    require_auth(request)

    family_members = db.query(FamilyMember).order_by(FamilyMember.name).all()
    return templates.TemplateResponse(
        request, "settings.html", {"family_members": family_members}
    )


@app.post("/settings/family-members")
async def add_family_member(
    request: Request, name: str = Form(...), db: Session = Depends(get_db)
):
    """Add a new family member"""
    # Require authentication
    require_auth(request)

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
    request: Request, member_id: int = Path(..., gt=0), db: Session = Depends(get_db)
):
    """Delete a family member and all their ratings"""
    # Require authentication
    require_auth(request)

    family_member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
    if not family_member:
        raise HTTPException(status_code=404, detail="Family member not found")

    db.delete(family_member)
    db.commit()
    return RedirectResponse(
        url="/settings?msg=Family+member+deleted+successfully", status_code=303
    )


@app.get("/games/new")
async def new_game_form(request: Request, db: Session = Depends(get_db)):
    """Form to add a new game"""
    # Require authentication
    require_auth(request)

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
    setup_time: Optional[str] = Form(None),
    game_elements: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Create a new game"""
    # Require authentication
    require_auth(request)

    game = Game(
        title=title,
        player_count=player_count or "",
        game_type=game_type or "",
        playtime=playtime or "",
        complexity=complexity or "",
        description=description or "",
        setup_time=setup_time or "",
        game_elements=game_elements or "",
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
async def autofill_game_by_title(
    request: Request, title: str = Form(...), db: Session = Depends(get_db)
):
    """Create a game with just title and use AI to autofill metadata"""
    # Require authentication
    require_auth(request)

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
            # Ensure game_type and game_elements are strings, not lists
            if key in ["game_type", "game_elements"] and isinstance(value, list):
                value = ", ".join(value)
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
    # Require authentication
    require_auth(request)

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
    # Require authentication
    require_auth(request)

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
    setup_time: Optional[str] = Form(None),
    game_elements: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Update a game"""
    # Require authentication
    require_auth(request)

    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    game.title = title
    game.player_count = player_count or ""
    game.game_type = game_type or ""
    game.playtime = playtime or ""
    game.complexity = complexity or ""
    game.description = description or ""
    game.setup_time = setup_time or ""
    game.game_elements = game_elements or ""

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
    return RedirectResponse(
        url=f"/games/{game_id}?msg=Game+updated+successfully", status_code=303
    )


@app.delete("/games/{game_id}")
async def delete_game(
    request: Request, game_id: int = Path(..., gt=0), db: Session = Depends(get_db)
):
    """Delete a game"""
    # Require authentication
    require_auth(request)

    # Validate game_id exists before deletion (security fix)
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        # If game doesn't exist, return 404 (original behavior)
        raise HTTPException(status_code=404, detail="Game not found")

    db.delete(game)
    db.commit()
    return RedirectResponse(url="/?msg=Game+deleted+successfully", status_code=303)


@app.post("/games/{game_id}/autofill")
async def autofill_game(
    request: Request, game_id: int = Path(..., gt=0), db: Session = Depends(get_db)
):
    """Autofill game metadata using AI"""
    # Require authentication
    require_auth(request)

    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Use AI to get metadata
    metadata = await get_game_metadata(game.title)

    # Update game with AI metadata
    for key, value in metadata.items():
        if hasattr(game, key) and value:
            # Ensure game_type and game_elements are strings, not lists
            if key in ["game_type", "game_elements"] and isinstance(value, list):
                value = ", ".join(value)
            setattr(game, key, value)

    db.commit()
    return RedirectResponse(
        url=f"/games/{game_id}?msg=Game+metadata+updated+with+AI", status_code=303
    )


@app.get("/recommend")
async def recommend_games(request: Request, db: Session = Depends(get_db)):
    """Recommendation page"""
    # Require authentication
    require_auth(request)

    return templates.TemplateResponse(request, "recommend.html", {})


@app.post("/recommend")
async def get_recommendations(
    request: Request, query: str = Form(...), db: Session = Depends(get_db)
):
    """Get AI recommendations"""
    # Require authentication
    require_auth(request)

    # Get all games from the database
    games = db.query(Game).all()

    if not games:
        return templates.TemplateResponse(
            request,
            "recommendations.html",
            {
                "error": "No games in your collection. Add some games first to get recommendations!",
                "games": [],
            },
        )

    # Convert games to the format expected by get_game_recommendations
    available_games = []
    for game in games:
        available_games.append(
            {
                "title": game.title,
                "player_count": game.player_count or "N/A",
                "game_type": game.game_type or "N/A",
                "playtime": game.playtime or "N/A",
                "complexity": game.complexity or "N/A",
                "description": game.description or "",
            }
        )

    # Get AI recommendations
    recommendations = await get_game_recommendations(
        query, available_games, max_recommendations=5
    )

    # Get family members and ratings for displaying in recommendations
    family_members = db.query(FamilyMember).order_by(FamilyMember.name).all()
    family_ratings = {}

    for game in games:
        family_ratings[game.id] = {
            rating.family_member_id: rating.rating for rating in game.family_ratings
        }

    return templates.TemplateResponse(
        request,
        "recommendations.html",
        {
            "query": query,
            "recommendations": recommendations,
            "games": games,
            "family_members": family_members,
            "family_ratings": family_ratings,
            "total_games": len(games),
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
