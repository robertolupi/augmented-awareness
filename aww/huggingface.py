from __future__ import annotations

from sentence_transformers import CrossEncoder
from sentence_transformers import SentenceTransformer


def local_model_error_message(model_name: str) -> str:
    return (
        f"Hugging Face model '{model_name}' is not available in the local cache. "
        "AWW is running in local-only mode, so it will not download models. "
        "Pre-download the model or set `[rag].local_files_only = false` in `aww.toml`."
    )


def load_sentence_transformer(
    model_name: str,
    *,
    device: str | None = None,
    trust_remote_code: bool = True,
    local_files_only: bool = True,
    token: bool | str | None = False,
    cache_folder: str | None = None,
) -> SentenceTransformer:
    try:
        return SentenceTransformer(
            model_name,
            device=device,
            trust_remote_code=trust_remote_code,
            local_files_only=local_files_only,
            token=token,
            cache_folder=cache_folder,
        )
    except Exception as exc:
        if local_files_only:
            raise RuntimeError(local_model_error_message(model_name)) from exc
        raise


def load_cross_encoder(
    model_name: str,
    *,
    device: str | None = None,
    trust_remote_code: bool = True,
    local_files_only: bool = True,
    token: bool | str | None = False,
    cache_folder: str | None = None,
) -> CrossEncoder:
    try:
        return CrossEncoder(
            model_name,
            device=device,
            trust_remote_code=trust_remote_code,
            local_files_only=local_files_only,
            token=token,
            cache_folder=cache_folder,
        )
    except Exception as exc:
        if local_files_only:
            raise RuntimeError(local_model_error_message(model_name)) from exc
        raise
