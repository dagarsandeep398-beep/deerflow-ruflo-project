from app import app

# Compatibility wrapper for the recovered V3 trading agent file name.
# This keeps the existing working app intact while presenting the same
# historical file name requested for the project.

if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
