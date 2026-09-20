"""Erros da aplicação que não representam regras matemáticas do domínio."""


class DatasetNotFoundError(Exception):
    """Indica que a busca por um dataset não encontrou registro no banco.

    O handler HTTP converte este erro em uma resposta 404. ``dataset_id`` é
    opcional para permitir seu uso quando o mapper recebe apenas ``None``.
    """

    def __init__(self, dataset_id: int | None = None) -> None:
        self.dataset_id = dataset_id
        detail = "Dataset não encontrado."
        if dataset_id is not None:
            detail = f"Dataset {dataset_id} não encontrado."
        super().__init__(detail)
