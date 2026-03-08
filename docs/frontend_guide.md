# Frontend Guide

## Tech Stack

| Package          | Version | Purpose                                          |
| ---------------- | ------- | ------------------------------------------------ |
| React            | 19.2    | UI framework (functional components + hooks)     |
| Vite             | 6.2     | Bundler & dev server                             |
| React Router DOM | 7.13    | Client-side SPA routing                          |
| Axios            | 1.13    | HTTP requests to the backend API                 |
| Lucide React     | 0.575   | Beautiful SVG icons                              |
| React Markdown   | 10.1    | Render AI markdown responses in chat             |
| Remark GFM       | 4.0     | GitHub-Flavored Markdown support (tables, lists) |

## Project Structure

```
frontend/
├── index.html              # Entry HTML
├── package.json            # Dependencies & scripts
├── vite.config.js          # Vite configuration
└── src/
    ├── main.jsx            # React DOM root mount
    ├── index.css           # Global styles (dark theme, glassmorphism)
    ├── App.jsx             # Root component: routing, auth state, layout
    └── components/
        ├── Login.jsx       # Registration & Login forms
        ├── Upload.jsx      # Document upload with drag-and-drop
        └── Chat.jsx        # AI conversation interface
```

## Components

### App.jsx — Root Layout & Routing

- Manages auth state via `useState` with `localStorage` persistence
- Protects `/dashboard` route — redirects to `/login` if no token
- Renders top navbar with RAGBot logo and Logout button
- Contains tab switcher between "Manage Documents" and "AI Chat"

### Login.jsx — Authentication

- Toggle between **Sign In** and **Sign Up** modes
- Registration: sends `{ username, email, password }` to `POST /auth/register`
- Login: sends form-data to `POST /auth/login`, stores JWT in `localStorage`
- Calls `setToken()` on success to navigate to dashboard

### Upload.jsx — Document Management

- File input with drag-and-drop zone
- Sends file as multipart/form-data to `POST /documents/upload`
- Shows upload states: idle → uploading → success/error
- Displays animated status messages with icons

### Chat.jsx — AI Conversation

- Maintains `messages` array with `role` (user/assistant) and `text`
- Sends queries to `POST /chat` with JWT authorization
- Loading state shows animated spinner with "Searching your documents..."
- AI responses rendered as rich Markdown (supports code blocks, lists, tables)
- Displays "Sources" section below AI messages showing which files were used
- **Error handling**: Shows clean, friendly messages instead of raw API errors:
  - Rate limit → "⏳ The AI service is temporarily rate-limited..."
  - Network error → "🔌 Cannot connect to the backend server..."
  - Model error → "⚠️ The AI model could not be found..."

## Design System

The UI uses a **dark theme** with these key design elements:

- Dark navy background (`#0a0f1c`)
- Glassmorphism cards with subtle borders
- Blue accent gradient for primary buttons
- Smooth `fade-in` and `slide-up` CSS animations
- Responsive layout centered on desktop
