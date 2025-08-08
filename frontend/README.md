# MCP React Frontend (Vite)

## Setup

1. Install dependencies:
   ```
   npm install
   ```

2. Start development server:
   ```
   npm run dev
   ```
   The app will open at http://localhost:5173

3. Build for production:
   ```
   npm run build
   ```

4. Preview production build:
   ```
   npm run preview
   ```

## Notes
- The Vite dev server proxies `/stream` requests to your FastAPI backend at `http://localhost:8000`.
- React 19 and Vite 5 are used.
- Main entry: `index.html`.
