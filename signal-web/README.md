# The Signal - Web Frontend

A React web application for generating AI-powered podcast episodes from articles. This is the desktop/laptop companion to the iOS app.

## Overview

```mermaid
graph TB
    subgraph Frontend["signal-web (React + Vite)"]
        UI[User Interface]
        API[API Client]
        State[App State]
    end

    subgraph Backend["signal-backend (FastAPI)"]
        Routes[API Routes]
        Pipeline[Generation Pipeline]
        Store[Data Store]
    end

    subgraph External["External Services"]
        Claude[Anthropic Claude]
        ElevenLabs[ElevenLabs TTS]
    end

    UI --> State
    State --> API
    API -->|HTTP| Routes
    Routes --> Pipeline
    Pipeline --> Store
    Pipeline -->|Script Generation| Claude
    Pipeline -->|Voice Synthesis| ElevenLabs
```

## Features

### Article Queue
Add articles via URL or paste content directly. Select articles to include in your podcast episode.

### Style Configuration
Customize your podcast with 8 independent dimensions:

```mermaid
mindmap
  root((Style Config))
    Core Voice
      Depth
        Briefing
        Deep Dive
        Synthesis
      Tone
        Casual
        Polished
        Debate
        Technical
      Lens
        Investor
        Engineer
        Macro
        General
    Delivery
      Pacing
        Rapid
        Measured
        Variable
      Humor
        Serious
        Dry
        Playful
        Roast
      Audience
        Insider
        Informed
        Curious
    Structure
      Structure
        Narrative
        Ranked
        Thematic
        Contrarian
      Closer
        Actionable
        Philosophical
        Prediction
        Question
```

### Voice Customization
Select from 9 ElevenLabs voices and adjust per-speaker settings:

| Setting | Range | Description |
|---------|-------|-------------|
| Stability | 0-100% | Higher = more consistent delivery |
| Clarity | 0-100% | Higher = clearer voice reproduction |
| Style | 0-100% | Higher = more expressive performance |

### Audio Production
Fine-tune the final output:

- **Gap Duration**: 100-1000ms between segments
- **Fade In/Out**: 0-500ms smooth transitions
- **Normalize**: Even out volume levels across speakers

## Architecture

### Component Structure

```mermaid
graph TD
    App[App.tsx]
    App --> Header[Header]
    App --> TabNav[Tab Navigation]
    App --> Content[Main Content]
    App --> Player[Player Overlay]

    Content --> Queue[ArticleQueue]
    Content --> Generate[GeneratePanel]
    Content --> Episodes[EpisodeList]

    Generate --> StylePicker
    Generate --> VoicePicker
    Generate --> AudioSettings

    Queue --> AddModal[Add Article Modal]

    Player --> Controls[Playback Controls]
    Player --> ScriptPanel[Script Panel]
    Player --> SegmentViz[Segment Visualization]
```

### Data Flow

```mermaid
sequenceDiagram
    participant User
    participant App
    participant API
    participant Backend
    participant Claude
    participant ElevenLabs

    User->>App: Select articles
    User->>App: Configure style
    User->>App: Click Generate

    App->>API: POST /api/episodes/generate
    API->>Backend: Create episode
    Backend-->>API: Episode (queued)
    API-->>App: Episode ID

    loop Poll every 2s
        App->>API: GET /api/episodes/{id}
        API->>Backend: Get status
        Backend-->>API: Episode status
        API-->>App: Update UI
    end

    Note over Backend: Pipeline runs async
    Backend->>Claude: Summarize articles
    Claude-->>Backend: Summaries
    Backend->>Claude: Generate script
    Claude-->>Backend: Script text
    Backend->>ElevenLabs: Synthesize segments
    ElevenLabs-->>Backend: Audio chunks
    Backend->>Backend: Mix & normalize

    App->>API: Episode ready!
    App->>User: Open player
```

### Generation Pipeline

```mermaid
stateDiagram-v2
    [*] --> Queued
    Queued --> Summarizing: Start pipeline
    Summarizing --> Scripting: Articles summarized
    Scripting --> Synthesizing: Script generated
    Synthesizing --> Mixing: Audio synthesized
    Mixing --> Ready: Audio mixed

    Summarizing --> Failed: Error
    Scripting --> Failed: Error
    Synthesizing --> Failed: Error
    Mixing --> Failed: Error

    Ready --> [*]
    Failed --> [*]
```

## Getting Started

### Prerequisites

- Node.js 18+
- Backend running on `localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Development

```bash
# Run dev server with hot reload
npm run dev

# Type check
npm run build

# Preview production build
npm run preview
```

### Environment

The Vite dev server proxies API requests to the backend:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/data': 'http://localhost:8000',
  },
}
```

## Project Structure

```
signal-web/
├── src/
│   ├── components/
│   │   ├── ArticleQueue.tsx    # Article management
│   │   ├── AudioSettings.tsx   # Audio production controls
│   │   ├── EpisodeList.tsx     # Episode history
│   │   ├── GeneratePanel.tsx   # Generation workflow
│   │   ├── Player.tsx          # Audio player
│   │   ├── StylePicker.tsx     # Style configuration
│   │   └── VoicePicker.tsx     # Voice selection
│   ├── api.ts                  # Backend API client
│   ├── types.ts                # TypeScript definitions
│   ├── App.tsx                 # Root component
│   ├── App.css                 # (empty - using Tailwind)
│   ├── index.css               # Tailwind + theme
│   └── main.tsx                # Entry point
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## API Endpoints

```mermaid
graph LR
    subgraph Articles
        A1[GET /api/articles]
        A2[POST /api/articles]
        A3[DELETE /api/articles/:id]
    end

    subgraph Episodes
        E1[GET /api/episodes/voices]
        E2[POST /api/episodes/generate]
        E3[GET /api/episodes/:id]
        E4[GET /api/episodes/:id/script]
        E5[GET /api/episodes/:id/audio]
        E6[GET /api/episodes]
    end
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/articles` | GET | List all articles |
| `/api/articles` | POST | Add article (URL or manual) |
| `/api/articles/:id` | DELETE | Remove article |
| `/api/episodes/voices` | GET | List available voices |
| `/api/episodes/generate` | POST | Start generation |
| `/api/episodes/:id` | GET | Get episode status |
| `/api/episodes/:id/script` | GET | Get parsed script |
| `/api/episodes/:id/audio` | GET | Download MP3 |
| `/api/episodes` | GET | List all episodes |

## Tech Stack

| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool & dev server |
| Tailwind CSS | Styling |

## Theme

The app uses a dark theme matching the iOS app:

```css
--color-background: #09090b;
--color-surface: #111113;
--color-border: #27272a;
--color-text-primary: #fafafa;
--color-text-secondary: #a1a1aa;
--color-text-muted: #52525b;
--color-accent-blue: #0a84ff;
--color-accent-purple: #bf5af2;
```

## User Interface

### Queue Tab
```mermaid
graph TD
    subgraph Queue["Queue Tab"]
        Header[Header + Add Button]
        List[Article List]
        Item1[Article Card]
        Item2[Article Card]
        Item3[Article Card]
    end

    Header --> Modal[Add Article Modal]
    Modal --> URLInput[URL Input]
    Modal --> ManualInput[Manual Entry]

    List --> Item1
    List --> Item2
    List --> Item3

    Item1 --> Checkbox[Select Checkbox]
    Item1 --> Title[Title + Source]
    Item1 --> Delete[Delete Button]
```

### Generate Tab
```mermaid
graph TD
    subgraph Generate["Generate Tab"]
        Summary[Summary Card]
        Presets[Preset Cards]
        Duration[Duration Slider]
        Dims[Style Dimensions]
        Voice[Voice Section]
        Audio[Audio Section]
        Button[Generate Button]
    end

    Summary --> ArticleCount
    Summary --> WordCount
    Summary --> EstCost

    Presets --> Morning[Morning Brief]
    Presets --> Deep[Deep Cut]
    Presets --> Hot[Hot Take]
    Presets --> Explain[Explain It]

    Dims --> Depth
    Dims --> Tone
    Dims --> Lens
    Dims --> Pacing
    Dims --> Humor
    Dims --> Audience
    Dims --> Structure
    Dims --> Closer
```

### Player
```mermaid
graph LR
    subgraph Player["Full-Screen Player"]
        subgraph Left["Playback Area"]
            Art[Episode Art]
            Info[Episode Info]
            Segments[Segment Visualization]
            Progress[Progress Bar]
            Controls[Play/Skip Controls]
        end

        subgraph Right["Script Panel"]
            ScriptHeader[Script Header]
            ScriptContent[Speaker Segments]
        end
    end
```

## License

MIT
