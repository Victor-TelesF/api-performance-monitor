"""Limites de memória e coordenação das renderizações concorrentes."""

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from threading import Barrier, Event

from matplotlib.figure import Figure

from api_performance_monitor.domain import LatencyDataset
from api_performance_monitor.roots import visualization_root
from api_performance_monitor.visualization.cache import PngCache


def key(name):
    return (name, b"digest", None, True)


def test_cache_evicts_least_recently_used_png_to_respect_byte_budget():
    cache = PngCache(max_bytes=6)
    cache.put(key("a"), b"aaa")
    cache.put(key("b"), b"bbb")
    assert cache.get(key("a")) == b"aaa"
    cache.put(key("c"), b"ccc")
    assert cache.get(key("b")) is None
    assert cache.get(key("a")) == b"aaa"
    assert cache.get(key("c")) == b"ccc"
    cache.put(key("huge"), b"1234567")
    assert cache.get(key("huge")) is None
    assert cache.get(key("a")) == b"aaa"


def test_cache_limits_entries_and_accounts_for_replacements():
    cache = PngCache(max_bytes=6, max_entries=2)
    cache.put(key("a"), b"aaa")
    cache.put(key("a"), b"a")
    cache.put(key("b"), b"bbbbb")
    assert cache.get(key("a")) == b"a"
    cache.put(key("c"), b"c")
    assert cache.get(key("b")) is None
    assert cache.get(key("a")) == b"a"
    cache.put(key("d"), b"d")
    assert cache.get(key("c")) is None
    assert cache.get(key("a")) == b"a"


def test_concurrent_identical_requests_render_once_and_cache_hits_skip_render_lock(monkeypatch):
    monkeypatch.setattr(visualization_root, "_png_cache", PngCache())
    monkeypatch.setattr(visualization_root, "figure_to_png", lambda figure: BytesIO(b"png"))
    dataset = LatencyDataset([100, 200])
    started, release = Event(), Event()
    barrier = Barrier(4)
    rendered = []

    def create_chart(dataset):
        rendered.append(dataset)
        started.set()
        assert release.wait(timeout=5)
        return Figure()

    def request():
        barrier.wait(timeout=5)
        return visualization_root._png_response(dataset, create_chart, chart="test")

    with ThreadPoolExecutor(max_workers=4) as executor:
        pending = [executor.submit(request) for _ in range(4)]
        try:
            assert started.wait(timeout=5)
        finally:
            release.set()
        assert [future.result(timeout=5).body for future in pending] == [b"png"] * 4
        assert len(rendered) == 1
        with visualization_root._render_lock:
            hit = executor.submit(
                visualization_root._png_response, dataset, create_chart, chart="test"
            )
            assert hit.result(timeout=5).body == b"png"
        assert len(rendered) == 1
