
from pathlib import Path
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = ROOT_DIR / "data" / "documents"

DOCUMENTS = {
    "FreshRetailNet-50K paper.pdf":
        "https://arxiv.org/pdf/2505.16319"
}


def download_documents():

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    for filename, url in DOCUMENTS.items():

        destination = DOCUMENTS_DIR / filename

        if destination.exists():
            print(f"Already available: {filename}")
            continue

        print(f"Downloading: {filename}")

        request = Request(
            url,
            headers={"User-Agent": "DemandLens-AI/1.0"}
        )

        with urlopen(request, timeout=60) as response:
            content = response.read()

        if not content.startswith(b"%PDF-"):
            raise ValueError(f"Invalid PDF: {filename}")

        destination.write_bytes(content)

        print(f"Downloaded: {filename}")


if __name__ == "__main__":
    download_documents()
