import sys
import pytest

@pytest.fixture(autouse=True)
def clean_sys_modules():
    yield
    # Xóa các module bắt đầu bằng app để không ảnh hưởng sang service khác trong monorepo
    to_delete = [mod for mod in sys.modules if mod == "app" or mod.startswith("app.")]
    for mod in to_delete:
        del sys.modules[mod]
