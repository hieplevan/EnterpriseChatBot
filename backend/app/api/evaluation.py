from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from backend.app.services.evaluator_service import RAGEvaluatorService
from backend.app.services.rag_engine import AdvancedRAGEngine
from backend.app.api.chat import get_retriever, get_reranker
from backend.app.services.hybrid_retriever import HybridRetrieverService
from backend.app.services.reranker_service import RerankerService

router = APIRouter(prefix="/api/eval", tags=["Evaluation & Benchmarks"])

_evaluator = RAGEvaluatorService()


@router.post("/benchmark")
def run_rag_benchmark(
    retriever: HybridRetrieverService = Depends(get_retriever),
    reranker: RerankerService = Depends(get_reranker),
):
    """
    Chay bo kiem thu benchmark dinh luong so sanh giua Naive RAG va Advanced RAG (Hybrid + Rerank).
    Xuat chi so RAG Triad Metrics: Faithfulness, Context Relevance, Overall Quality.
    """
    test_queries = [
        "11 quyen co ban cua chu the du lieu ca nhan theo Nghi dinh 13/2023/ND-CP la gi?",
        "Tien luong lam them gio vao ngay nghi le tet theo Bo luat Lao dong 2019 tinh the nao?",
        "Xe may vuot den do bi phat bao nhieu tien theo Nghi dinh 100/2019/ND-CP?",
    ]


    engine = AdvancedRAGEngine(
        retriever_service=retriever,
        reranker_service=reranker,
        top_k=3,
    )

    results = []

    for query in test_queries:
        # 1. Chay Advanced RAG (Hybrid + Rerank)
        ans_adv, cits_adv, metrics_adv = engine.generate_response(
            query=query, use_rag=True, use_hybrid=True, use_rerank=True
        )
        score_adv = _evaluator.evaluate_pipeline(query, ans_adv, cits_adv)

        # 2. Chay Naive RAG (Vector-only, no rerank)
        ans_naive, cits_naive, metrics_naive = engine.generate_response(
            query=query, use_rag=True, use_hybrid=False, use_rerank=False
        )
        score_naive = _evaluator.evaluate_pipeline(query, ans_naive, cits_naive)

        results.append(
            {
                "query": query,
                "advanced_rag": {
                    "metrics": score_adv,
                    "retrieval_ms": metrics_adv["retrieval_ms"],
                    "citations_count": len(cits_adv),
                },
                "naive_rag": {
                    "metrics": score_naive,
                    "retrieval_ms": metrics_naive["retrieval_ms"],
                    "citations_count": len(cits_naive),
                },
            }
        )

    # Tinh toan trung binh
    avg_adv_quality = sum(r["advanced_rag"]["metrics"]["rag_overall_quality"] for r in results) / len(results)
    avg_naive_quality = sum(r["naive_rag"]["metrics"]["rag_overall_quality"] for r in results) / len(results)

    improvement_pct = round(((avg_adv_quality - avg_naive_quality) / max(1.0, avg_naive_quality)) * 100, 1)

    return {
        "status": "completed",
        "benchmark_summary": {
            "total_test_cases": len(test_queries),
            "advanced_rag_avg_quality": round(avg_adv_quality, 1),
            "naive_rag_avg_quality": round(avg_naive_quality, 1),
            "quality_improvement_pct": f"+{improvement_pct}%",
        },
        "detailed_results": results,
    }
