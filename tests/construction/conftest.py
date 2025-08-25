import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def sample_project(tmp_path_factory) -> Path:
    """A pytest fixture that creates a temporary, representative Python project structure."""
    root = tmp_path_factory.mktemp("sample_project")
    
    # Root package
    (root / "my_app").mkdir()
    (root / "my_app" / "__init__.py").touch()

    # Models sub-package
    (root / "my_app" / "models").mkdir()
    (root / "my_app" / "models" / "__init__.py").touch()
    (root / "my_app" / "models" / "base.py").write_text(
        "class ModelBase:\n    pass\n"
    )
    (root / "my_app" / "models" / "user.py").write_text(
        "from .base import ModelBase\n\n"
        "class User(ModelBase):\n    pass\n"
    )

    # Services sub-package with composition and more complex imports
    (root / "my_app" / "services").mkdir()
    (root / "my_app" / "services" / "__init__.py").touch()
    (root / "my_app" / "services" / "repository.py").write_text(
        "from my_app.models.user import User\n\n"
        "class UserRepository:\n"
        "    def get_user(self) -> User:\n"
        "        return User()\n"
    )
    
    # Main application file with composition
    (root / "my_app" / "app.py").write_text(
        "import os\n" # Should be ignored
        "from .services.repository import UserRepository\n"
        "from my_app.models import user\n\n"
        "class Application:\n"
        "    def __init__(self):\n"
        "        self.repo = UserRepository()\n"
        "        self.user_model = user.User()\n" # Composition via alias
    )
    
    # A non-python file to be ignored
    (root / "README.md").touch()
    
    return root