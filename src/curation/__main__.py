import warnings

# Suppress Pydantic V1 compatibility warning for Python 3.14+
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater."
)

from src.curation.cli import app


if __name__ == "__main__":
    app()
