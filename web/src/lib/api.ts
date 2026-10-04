// Base URL of the Python backend (FastAPI). Override with NEXT_PUBLIC_API_URL.
export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
