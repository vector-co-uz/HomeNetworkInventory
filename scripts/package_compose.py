"""Build a source-free deployment bundle referencing an immutable GHCR image."""
import argparse
from pathlib import Path
import re
import zipfile


PACKAGE_README = """# Home Network Inventory - Docker Compose

1. Copy `.env.example` to `.env`.
2. Generate a random `SESSION_SECRET` containing at least 32 characters.
3. Set `SESSION_HTTPS_ONLY=false` for plain HTTP or `true` behind HTTPS.
4. Start the application:

   docker compose pull
   docker compose up -d

The SQLite database is stored in the named `hni_data` volume.
Do not run `docker compose down -v` unless you intend to delete that data.

The exact immutable image used by this package is recorded in `IMAGE.txt`.
"""


def build(image: str, output: Path) -> Path:
    if not re.fullmatch(r'ghcr\.io/[a-z0-9._/-]+@sha256:[a-f0-9]{64}', image):
        raise ValueError('Expected a lowercase GHCR image with a sha256 digest')
    root = Path(__file__).resolve().parents[1]
    compose = (root / 'compose.yaml').read_text(encoding='utf-8')
    # Source compose files may either build the checkout with a local image
    # tag, or already point at the published mutable tag. Normalize both to
    # the immutable image supplied by the release workflow.
    compose, build_count = re.subn(r'^    build: \.\r?\n', '', compose, flags=re.MULTILINE)
    compose, image_count = re.subn(
        r'^    image: (?:home-network-inventory:local|ghcr\.io/vector-co-uz/homenetworkinventory:latest)\r?$',
        f'    image: {image}', compose, flags=re.MULTILINE)
    if ('    build:' in compose or image_count != 1 or
            re.search(r'^    image: ', compose, flags=re.MULTILINE) is None):
        raise ValueError('Unexpected source Compose layout; update the packager')
    files = {
        'compose.yaml': compose,
        '.env.example': (root / '.env.example').read_text(encoding='utf-8'),
        'README.md': PACKAGE_README,
        'LICENSE': (root / 'LICENSE').read_text(encoding='utf-8'),
        'IMAGE.txt': image + '\n',
    }
    output.mkdir(parents=True, exist_ok=True)
    archive = output / 'home-network-inventory-compose.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for name, content in files.items():
            (output / name).write_text(content, encoding='utf-8', newline='\n')
            bundle.writestr(name, content.encode('utf-8'))
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', type=Path, default=Path('dist'))
    args = parser.parse_args()
    print(build(args.image, args.output))
