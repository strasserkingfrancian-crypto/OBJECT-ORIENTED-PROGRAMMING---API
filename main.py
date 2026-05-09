"""
Limkokwing University Library Management API
PROG315 - Object-Oriented Programming 2
Assignment: Basic API structure with open-software
Student: [Your Name]
"""

import asyncio
from datetime import date, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# ── App instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Limkokwing Library API",
    description="A RESTful API for managing the Limkokwing University Sierra Leone library system.",
    version="1.0.0",
)

# ── In-memory "database" ─────────────────────────────────────────────────────
books_db: dict[int, dict] = {
    1: {"id": 1, "title": "Clean Code", "author": "Robert C. Martin", "category": "Programming", "available": True},
    2: {"id": 2, "title": "Introduction to Algorithms", "author": "Cormen et al.", "category": "Computer Science", "available": True},
    3: {"id": 3, "title": "The Pragmatic Programmer", "author": "Hunt & Thomas", "category": "Programming", "available": False},
    4: {"id": 4, "title": "Design Patterns", "author": "Gang of Four", "category": "Software Engineering", "available": True},
    5: {"id": 5, "title": "Python Crash Course", "author": "Eric Matthes", "category": "Programming", "available": True},
}

users_db: dict[int, dict] = {
    101: {"id": 101, "name": "Aminata Koroma", "email": "aminata@limkokwing.edu.sl"},
    102: {"id": 102, "name": "Mohamed Bangura", "email": "mohamed@limkokwing.edu.sl"},
    103: {"id": 103, "name": "Fatima Sesay",   "email": "fatima@limkokwing.edu.sl"},
}

borrows_db: dict[int, dict] = {
    1: {
        "borrow_id": 1,
        "user_id": 101,
        "book_id": 3,
        "borrow_date": str(date.today() - timedelta(days=20)),
        "due_date":    str(date.today() - timedelta(days=6)),   # overdue
        "return_date": None,
        "fine": 0.0,
    }
}
_next_borrow_id = 2

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class BorrowRequest(BaseModel):
    user_id: int
    book_id: int

class ReturnRequest(BaseModel):
    borrow_id: int

# ── Helper ────────────────────────────────────────────────────────────────────

def calculate_fine(due_date_str: str) -> float:
    """Return fine amount (0.50 NLe per overdue day)."""
    due = date.fromisoformat(due_date_str)
    overdue_days = (date.today() - due).days
    return round(max(overdue_days, 0) * 0.50, 2)

# ── Endpoints ─────────────────────────────────────────────────────────────────

# --------------------------------------------------------------------------- #
# ENDPOINT 1 – GET /books                                                     #
# Purpose : Search / list books by title, author, or category                 #
# --------------------------------------------------------------------------- #
@app.get("/books", summary="Search for books")
async def get_books(
    title:    Optional[str] = Query(None, description="Filter by book title (case-insensitive)"),
    author:   Optional[str] = Query(None, description="Filter by author name (case-insensitive)"),
    category: Optional[str] = Query(None, description="Filter by category (case-insensitive)"),
) -> dict:
    """
    Returns a list of books. Optionally filter by title, author, or category.

    - **Input**  : Optional query parameters: title, author, category
    - **Output** : JSON list of matching books with availability status
    - **Example**: GET /books?category=Programming
    """
    results = list(books_db.values())

    if title:
        results = [b for b in results if title.lower() in b["title"].lower()]
    if author:
        results = [b for b in results if author.lower() in b["author"].lower()]
    if category:
        results = [b for b in results if category.lower() in b["category"].lower()]

    return {"count": len(results), "books": results}


# --------------------------------------------------------------------------- #
# ENDPOINT 2 – POST /borrow                                                   #
# Purpose : A user borrows an available book                                  #
# --------------------------------------------------------------------------- #
@app.post("/borrow", summary="Borrow a book", status_code=201)
async def borrow_book(request: BorrowRequest) -> dict:
    """
    Creates a borrow record for a user and marks the book as unavailable.

    - **Input**  : JSON body with user_id and book_id
    - **Output** : Borrow confirmation with due date (14 days from today)
    - **Example**: POST /borrow  { "user_id": 102, "book_id": 4 }
    """
    global _next_borrow_id

    # Validate user
    if request.user_id not in users_db:
        raise HTTPException(status_code=404, detail=f"User {request.user_id} not found.")

    # Validate book
    book = books_db.get(request.book_id)
    if not book:
        raise HTTPException(status_code=404, detail=f"Book {request.book_id} not found.")
    if not book["available"]:
        raise HTTPException(status_code=409, detail="Book is currently unavailable.")

    # Create borrow record
    borrow_record = {
        "borrow_id":   _next_borrow_id,
        "user_id":     request.user_id,
        "book_id":     request.book_id,
        "borrow_date": str(date.today()),
        "due_date":    str(date.today() + timedelta(days=14)),
        "return_date": None,
        "fine":        0.0,
    }
    borrows_db[_next_borrow_id] = borrow_record
    _next_borrow_id += 1

    # Mark book unavailable
    books_db[request.book_id]["available"] = False

    return {"message": "Book borrowed successfully.", "borrow": borrow_record}


# --------------------------------------------------------------------------- #
# ENDPOINT 3 – POST /return                                                   #
# Purpose : A user returns a borrowed book; fine is calculated if overdue     #
# --------------------------------------------------------------------------- #
@app.post("/return", summary="Return a borrowed book")
async def return_book(request: ReturnRequest) -> dict:
    """
    Processes a book return and calculates any overdue fine.

    - **Input**  : JSON body with borrow_id
    - **Output** : Return confirmation including fine amount (if any)
    - **Example**: POST /return  { "borrow_id": 1 }
    """
    record = borrows_db.get(request.borrow_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Borrow record {request.borrow_id} not found.")
    if record["return_date"]:
        raise HTTPException(status_code=409, detail="This book has already been returned.")

    fine = calculate_fine(record["due_date"])
    record["return_date"] = str(date.today())
    record["fine"] = fine

    # Mark book available again
    books_db[record["book_id"]]["available"] = True

    return {
        "message": "Book returned successfully.",
        "borrow_id": request.borrow_id,
        "fine_amount": fine,
        "fine_message": f"Fine of NLe {fine} charged." if fine > 0 else "No fine — returned on time!",
    }


# --------------------------------------------------------------------------- #
# ENDPOINT 4 – GET /overdue                                                   #
# Purpose : List all overdue borrows with calculated fines                    #
# --------------------------------------------------------------------------- #
@app.get("/overdue", summary="List overdue books and fines")
async def get_overdue() -> dict:
    """
    Returns all active (not yet returned) borrow records where due_date has passed.

    - **Input**  : None
    - **Output** : List of overdue borrow records with user info, book info, and fine
    - **Example**: GET /overdue
    """
    overdue_list = []
    for record in borrows_db.values():
        if record["return_date"]:          # already returned
            continue
        fine = calculate_fine(record["due_date"])
        if fine > 0:
            user = users_db.get(record["user_id"], {})
            book = books_db.get(record["book_id"], {})
            overdue_list.append({
                "borrow_id":  record["borrow_id"],
                "user_name":  user.get("name", "Unknown"),
                "book_title": book.get("title", "Unknown"),
                "due_date":   record["due_date"],
                "days_overdue": (date.today() - date.fromisoformat(record["due_date"])).days,
                "fine":       fine,
            })

    return {"overdue_count": len(overdue_list), "overdue_records": overdue_list}


# ── Async simulation (Part B requirement) ────────────────────────────────────

async def simulate_user_borrow(user_id: int, book_id: int) -> str:
    """Simulates a single user borrowing a book asynchronously."""
    await asyncio.sleep(0.1)   # simulate network/DB latency
    user = users_db.get(user_id, {})
    book = books_db.get(book_id, {})
    return (
        f"User '{user.get('name', user_id)}' attempted to borrow "
        f"'{book.get('title', book_id)}' — "
        f"{'SUCCESS' if book.get('available') else 'FAILED (unavailable)'}"
    )


async def simulate_concurrent_borrows() -> list[str]:
    """
    Demonstrates async/await: multiple users try to borrow books simultaneously.
    Uses asyncio.gather() to run all requests concurrently.
    """
    tasks = [
        simulate_user_borrow(101, 1),
        simulate_user_borrow(102, 2),
        simulate_user_borrow(103, 3),   # book 3 is currently unavailable
        simulate_user_borrow(101, 5),
    ]
    results = await asyncio.gather(*tasks)
    return list(results)


@app.get("/simulate", summary="Async concurrent borrow simulation")
async def run_simulation() -> dict:
    """
    Demonstrates asynchronous programming by simulating multiple users
    borrowing books at the same time using asyncio.gather().

    - **Input**  : None
    - **Output** : List of results showing each concurrent borrow attempt
    """
    results = await simulate_concurrent_borrows()
    return {"simulation": "Concurrent borrow requests", "results": results}


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
