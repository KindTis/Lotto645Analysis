import sys
import types
import importlib.util
import xml.etree.ElementTree as ET

# Provide fallback implementations when dependencies are missing
try:
    from bs4 import BeautifulSoup  # type: ignore
except ModuleNotFoundError:
    class _ElemWrapper:
        def __init__(self, elem):
            self.elem = elem
        def find_all(self, names):
            if isinstance(names, list):
                return [_ElemWrapper(e) for e in self.elem.iter() if e.tag in names and e is not self.elem]
            return [_ElemWrapper(e) for e in self.elem.iter() if e.tag == names and e is not self.elem]
        def get(self, key, default=None):
            return self.elem.attrib.get(key, default)
        def get_text(self, strip=False):
            text = ''.join(self.elem.itertext())
            return text.strip() if strip else text
    class BeautifulSoup:  # type: ignore
        def __init__(self, html, parser='html.parser'):
            self.root = ET.fromstring(html)
        def find(self, name, attrs=None):
            if self.root.tag == name:
                return _ElemWrapper(self.root)
            for el in self.root.iter(name):
                return _ElemWrapper(el)
            return None
    sys.modules['bs4'] = types.ModuleType('bs4')
    sys.modules['bs4'].BeautifulSoup = BeautifulSoup

# Stub modules that may be missing when importing Lotto645Analysis
for mod_name in ['numpy', 'requests']:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)

# Load Lotto645Analysis module from file path to avoid import issues
spec = importlib.util.spec_from_file_location('Lotto645Analysis', 'Lotto645Analysis.py')
Lotto645Analysis = importlib.util.module_from_spec(spec)
sys.modules['Lotto645Analysis'] = Lotto645Analysis
spec.loader.exec_module(Lotto645Analysis)

parse_int = Lotto645Analysis.parse_int
parse_table_with_rowspan = Lotto645Analysis.parse_table_with_rowspan


def test_parse_int_variations():
    assert parse_int("1,234") == 1234
    assert parse_int("5,678원") == 5678
    assert parse_int("당첨금액 9,876,543원") == 9876543
    assert parse_int("abc") == 0
    assert parse_int(None) == 0


def test_parse_table_with_rowspan_basic():
    html = """
    <table>
        <tr>
            <td rowspan='2'>R1C1</td>
            <td>R1C2</td>
            <td>R1C3</td>
        </tr>
        <tr>
            <td colspan='2'>R2C2-3</td>
        </tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    result = parse_table_with_rowspan(table)
    assert result == [
        ["R1C1", "R1C2", "R1C3"],
        ["R1C1", "R2C2-3", "R2C2-3"],
    ]
