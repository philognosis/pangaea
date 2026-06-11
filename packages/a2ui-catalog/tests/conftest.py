import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
CATALOG_PKG = os.path.join(ROOT, "packages", "a2ui-catalog")
sys.path.insert(0, CATALOG_PKG)

import pytest
