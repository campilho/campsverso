import pytest

from campsverso_kernel.core import KernelCore
from campsverso_kernel.testing import make_core


@pytest.fixture
def core() -> KernelCore:
    kernel = make_core()
    kernel.start()
    return kernel
