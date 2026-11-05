"""PNG real, posição do buffer e liberação de recursos quando a escrita falha."""

from io import BytesIO

import pytest
from matplotlib.figure import Figure
from matplotlib.image import imread

from api_performance_monitor.visualization import export


def test_export_returns_readable_png_and_preserves_the_figure():
    figure = Figure(figsize=(6.4, 4.8), dpi=100)
    axes = figure.subplots()
    axes.plot([1, 2], [100, 200])
    try:
        with export.figure_to_png(figure) as buffer:
            assert buffer.tell() == 0
            assert buffer.read(8) == b"\x89PNG\r\n\x1a\n"
            buffer.seek(0)
            assert imread(buffer, format="png").shape[:2] == (480, 640)
        assert figure.axes == [axes]
        assert list(axes.lines[0].get_ydata()) == [100, 200]
    finally:
        figure.clear()


def test_export_closes_buffer_and_propagates_the_original_rendering_error(monkeypatch):
    buffer = BytesIO()
    figure = Figure()
    failure = OSError("Falha simulada ao escrever PNG.")

    def fail_savefig(*args, **kwargs):
        buffer.write(b"partial png")
        raise failure

    monkeypatch.setattr(export, "BytesIO", lambda: buffer)
    monkeypatch.setattr(figure, "savefig", fail_savefig)

    with pytest.raises(OSError) as caught:
        export.figure_to_png(figure)

    assert caught.value is failure
    assert buffer.closed
