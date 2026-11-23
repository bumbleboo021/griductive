"""Launch the Griductive application."""
import sys

if __name__ == '__main__':
    if sys.platform == 'emscripten':
        # Pygbag scans this entry point to preload its pygame WebAssembly wheel.
        import pygame
        import asyncio
        from griductive.web_app import main
        asyncio.run(main())
    else:
        from griductive.app import main
        raise SystemExit(main())
