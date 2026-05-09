# 📚 Limkokwing Library Management API

**Name – Francian Strasser King **  
Class – DIT1101F  
ID: 905005053
Semester 04 | March 2026 – July 2026

---

## Project Description

A RESTful API built with **Python FastAPI** that provides a digital library management system for Limkokwing University. The system allows users to search for books, borrow and return books, and track overdue records and fines — all while supporting concurrent multi-user access through asynchronous programming.

---

---

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Async**: asyncio (built-in)

---

## Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/limkokwing-library-api.git
cd limkokwing-library-api

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn main:app --reload
```

Open your browser at: **http://127.0.0.1:8000/docs** (Swagger UI)

---

## API Endpoints

### `GET /books`
Search for books by optional filters.

**Query Parameters:**
- `title` – partial title match
- `author` – partial author match
- `category` – partial category match

**Example:**
```
GET /books?category=Programming
```

---

### `POST /borrow`
Borrow an available book. Returns a borrow record with a 14-day due date.

**Request Body:**
```json
{ "user_id": 102, "book_id": 4 }
```

---

### `POST /return`
Return a borrowed book. Calculates overdue fine (NLe 0.50/day).

**Request Body:**
```json
{ "borrow_id": 1 }
```

---

### `GET /overdue`
List all active overdue borrow records with fines.

---

### `GET /simulate`
Runs an async simulation of multiple users borrowing books concurrently using `asyncio.gather()`.

---

## Project Structure

```
limkokwing-library-api/
├── main.py             # FastAPI application (all endpoints)
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
└── .gitignore          # Git ignore rules
```

---

## SDG Alignment

This project aligns with **SDG 4 – Quality Education** by digitising library services to improve access to learning resources for students and staff at Limkokwing University Sierra Leone.

---

## License

This project is submitted as academic coursework. All rights reserved by the author.
