import pandas as pd
import pyarrow as pa
import pytest
from lancedb.rerankers.base import Reranker

from aww.config import Settings
from aww.huggingface import load_cross_encoder, load_sentence_transformer
from aww.rag import Index, LocalCrossEncoderReranker, LocalSentenceTransformerEmbeddings


def test_settings_enable_offline_hf_env(monkeypatch):
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    monkeypatch.delenv("TRANSFORMERS_OFFLINE", raising=False)

    Settings(rag={"local_files_only": True})

    assert "1" == __import__("os").environ["HF_HUB_OFFLINE"]
    assert "1" == __import__("os").environ["TRANSFORMERS_OFFLINE"]


def test_load_sentence_transformer_uses_local_only(monkeypatch):
    calls = []

    class FakeSentenceTransformer:
        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))

    monkeypatch.setattr(
        "aww.huggingface.SentenceTransformer",
        FakeSentenceTransformer,
    )

    load_sentence_transformer(
        "all-MiniLM-L6-v2",
        local_files_only=True,
        token=False,
        cache_folder="/tmp/hf-cache",
    )

    _, kwargs = calls[0]
    assert kwargs["local_files_only"] is True
    assert kwargs["token"] is False
    assert kwargs["cache_folder"] == "/tmp/hf-cache"


def test_load_sentence_transformer_reports_missing_local_model(monkeypatch):
    class MissingModel:
        def __init__(self, *args, **kwargs):
            raise OSError("missing model")

    monkeypatch.setattr("aww.huggingface.SentenceTransformer", MissingModel)

    with pytest.raises(RuntimeError, match="local-only mode"):
        load_sentence_transformer("all-MiniLM-L6-v2", local_files_only=True)


def test_load_cross_encoder_uses_local_only(monkeypatch):
    calls = []

    class FakeCrossEncoder:
        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))

    monkeypatch.setattr("aww.huggingface.CrossEncoder", FakeCrossEncoder)

    load_cross_encoder(
        "cross-encoder/ms-marco-TinyBERT-L-6",
        local_files_only=True,
        token=False,
        cache_folder="/tmp/hf-cache",
    )

    _, kwargs = calls[0]
    assert kwargs["local_files_only"] is True
    assert kwargs["token"] is False
    assert kwargs["cache_folder"] == "/tmp/hf-cache"


def test_local_sentence_transformer_embeddings_use_local_cache(monkeypatch):
    calls = []

    class FakeModel:
        def encode(self, texts, convert_to_numpy, normalize_embeddings):
            return [[1.0, 0.0, float(len(texts[0]))]]

    def fake_loader(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeModel()

    monkeypatch.setattr("aww.rag.load_sentence_transformer", fake_loader)

    embedding = LocalSentenceTransformerEmbeddings.create(
        name="all-MiniLM-L6-v2",
        local_files_only=True,
        token=False,
        cache_folder="/tmp/hf-cache",
    )

    vectors = embedding.generate_embeddings(["hello"])

    assert vectors == [[1.0, 0.0, 5.0]]
    _, kwargs = calls[0]
    assert kwargs["local_files_only"] is True
    assert kwargs["token"] is False
    assert kwargs["cache_folder"] == "/tmp/hf-cache"


def test_index_construction_is_lazy(tmp_path, monkeypatch):
    def fail_build(self):
        raise AssertionError("embedding model should not be created in __init__")

    monkeypatch.setattr(Index, "_build_embedding_model", fail_build)

    idx = Index(data_path=tmp_path)

    assert idx.model is None
    assert idx.tbl is None


def test_fts_search_does_not_initialize_embedding_model(tmp_path, monkeypatch):
    def fail_build(self):
        raise AssertionError("FTS search should not initialize embeddings")

    class FakeReranker(Reranker):
        def rerank_vector(self, query, vector_results):
            return vector_results

        def rerank_fts(self, query, fts_results):
            return fts_results.append_column(
                "_relevance_score",
                pa.array([1.0] * len(fts_results), type=pa.float32()),
            )

        def rerank_hybrid(self, query, vector_results, fts_results):
            return fts_results

    class FakeResults:
        def __init__(self):
            self._table = pa.Table.from_pylist(
                [{"id": "index", "text": "frontmatter", "_score": 1.0}]
            )

        def limit(self, limit):
            return self

        def rerank(self, reranker, query_string=None):
            self._table = reranker.rerank_fts(query_string or "", self._table)
            return self

        def to_pandas(self):
            return self._table.to_pandas()

    class FakeTable:
        def search(self, query, query_type=None):
            assert query_type == "fts"
            return FakeResults()

    monkeypatch.setattr(Index, "_build_embedding_model", fail_build)
    monkeypatch.setattr("aww.rag.CrossEncoderReranker", FakeReranker)

    idx = Index(data_path=tmp_path)
    idx.tbl = FakeTable()

    results = idx.search("frontmatter", rag=False)

    assert isinstance(results, pd.DataFrame)
    assert results["id"].tolist() == ["index"]


def test_local_cross_encoder_reranker_uses_local_cache(monkeypatch):
    calls = []

    class FakeCrossEncoder:
        def predict(self, pairs):
            return [1.0 for _ in pairs]

    def fake_loader(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeCrossEncoder()

    monkeypatch.setattr("aww.rag.load_cross_encoder", fake_loader)

    reranker = LocalCrossEncoderReranker(
        local_files_only=True,
        token=False,
        cache_folder="/tmp/hf-cache",
    )
    table = pa.Table.from_pylist([{"text": "hello", "_score": 1.0}])
    ranked = reranker.rerank_fts("hi", table)

    assert "_relevance_score" in ranked.column_names
    _, kwargs = calls[0]
    assert kwargs["local_files_only"] is True
    assert kwargs["token"] is False
    assert kwargs["cache_folder"] == "/tmp/hf-cache"
