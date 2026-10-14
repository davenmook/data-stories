# Tools

Shared helpers used across the stories:

- `fetch_ookla.py`: downloads one year of Ookla open data fixed tiles for Texas straight from S3 (`python3 tools/fetch_ookla.py 2025`)
- `style.py`: one matplotlib chart style in the site's look (carbon, sage, teal), with `credit()` for the source line and `save()` for SVG + PNG
