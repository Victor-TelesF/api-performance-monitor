"""Conversão de uma figura do Matplotlib para bytes PNG em memória."""

from io import BytesIO

from matplotlib.figure import Figure


def figure_to_png(figure: Figure) -> BytesIO:
    """Converte ``figure`` em PNG e devolve um ``io.BytesIO``.

    ``BytesIO`` é um arquivo em memória: ``getvalue()`` devolve os bytes do
    PNG e ``read()`` também pode lê-los. O cursor é reposicionado no início
    para que ``read()`` funcione logo após a conversão.

    A função não fecha a ``Figure`` recebida. Quem usa o buffer deve fechá-lo
    quando terminar; por exemplo, com ``buffer.close()``. Se a renderização
    falhar, fecha o buffer e propaga a exceção original.
    """
    buffer = BytesIO()
    try:
        figure.savefig(buffer, format="png")
        buffer.seek(0)
    except BaseException:
        buffer.close()
        raise
    return buffer
