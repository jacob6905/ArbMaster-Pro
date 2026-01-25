# RAILGUN Remotion Video

A terminal-style ASCII typewriter animation video built with Remotion.

## Features

- Dark terminal background with monospace font
- Typewriter effect for ASCII art "RAILGUN" text
- Cyan/teal accent colors (#00D9FF)
- Sequential subtitle animations
- Scanline and vignette effects for terminal aesthetic
- Grid background with radial glow

## Compositions

- **RailgunVideo** - Main 12-second video (1920x1080)
- **RailgunVideoShort** - 10-second version (1920x1080)
- **RailgunVideoSquare** - Square format for social (1080x1080)

## Getting Started

```bash
# Install dependencies
npm install

# Start Remotion Studio (preview)
npm start

# Render final video
npm run build
```

## Customization

Edit `src/components/RailgunVideo.tsx` to customize:
- Colors (CYAN, DARK_BG constants)
- Timing (ASCII_START, TAGLINE_START, etc.)
- Text content
- Animation speeds

Edit `src/components/AsciiArt.tsx` to change the ASCII art design.

## Output

The rendered video will be saved to `out/railgun-video.mp4`
