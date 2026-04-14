"""
graph.py — Supervisor Orchestrator
Sprint 1: Implement AgentState, supervisor_node, route_decision và kết nối graph.

Kiến trúc:
    Input → Supervisor → [retrieval_worker | policy_tool_worker | human_review] → synthesis → Output

Chạy thử:
    python graph.py
"""

import json
import os
import sys
from datetime import datetime
from typing import TypedDict, Literal, Optional, Iterable

# Uncomment nếu dùng LangGraph:
# from langgraph.graph import StateGraph, END

# ─────────────────────────────────────────────
# 1. Shared State — dữ liệu đi xuyên toàn graph
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    # Input
    task: str                           # Câu hỏi đầu vào từ user

    # Supervisor decisions
    route_reason: str                   # Lý do route sang worker nào
    risk_high: bool                     # True → cần HITL hoặc human_review
    needs_tool: bool                    # True → cần gọi external tool qua MCP
    hitl_triggered: bool                # True → đã pause cho human review

    # Worker outputs
    retrieved_chunks: list              # Output từ retrieval_worker
    retrieved_sources: list             # Danh sách nguồn tài liệu
    policy_result: dict                 # Output từ policy_tool_worker
    mcp_tools_used: list                # Danh sách MCP tools đã gọi
    mcp_tool_called: list               # Trace list tên tool MCP đã gọi
    mcp_result: list                    # Trace list output MCP cho mỗi tool call

    # Final output
    final_answer: str                   # Câu trả lời tổng hợp
    sources: list                       # Sources được cite
    confidence: float                   # Mức độ tin cậy (0.0 - 1.0)

    # Trace & history
    history: list                       # Lịch sử các bước đã qua
    workers_called: list                # Danh sách workers đã được gọi
    worker_io_logs: list                # Log input/output của từng worker theo contract
    supervisor_route: str               # Worker được chọn bởi supervisor
    latency_ms: Optional[int]           # Thời gian xử lý (ms)
    run_id: str                         # ID của run này


def make_initial_state(task: str) -> AgentState:
    """Khởi tạo state cho một run mới."""
    return {
        "task": task,
        "route_reason": "",
        "risk_high": False,
        "needs_tool": False,
        "hitl_triggered": False,
        "retrieved_chunks": [],
        "retrieved_sources": [],
        "policy_result": {},
        "mcp_tools_used": [],
        "mcp_tool_called": [],
        "mcp_result": [],
        "final_answer": "",
        "sources": [],
        "confidence": 0.0,
        "history": [],
        "workers_called": [],
        "worker_io_logs": [],
        "supervisor_route": "",
        "latency_ms": None,
        "run_id": f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    }


# ─────────────────────────────────────────────
# 2. Supervisor Node — quyết định route
# ─────────────────────────────────────────────

def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(kw in text for kw in keywords)


def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor phân tích task và quyết định:
    1. Route sang worker nào
    2. Có cần MCP tool không
    3. Có risk cao cần HITL không
    """
    task_raw = state["task"]
    task = task_raw.lower()
    state["history"].append(f"[supervisor] received task: {task_raw[:120]}")

    # --- Routing signals (aligned with contracts/worker_contracts.yaml) ---
    # Supervisor chỉ làm routing/guardrails; toàn bộ "domain answering" nằm ở workers.
    policy_or_access_keywords = (
        "hoàn tiền",
        "refund",
        "flash sale",
        "license",
        "license key",
        "subscription",
        "kỹ thuật số",
        "cấp quyền",
        "access",
        "access level",
        "level 2",
        "level 3",
        "admin access",
    )
    retrieval_keywords = (
        "p1",
        "sla",
        "ticket",
        "escalation",
        "sự cố",
        "incident",
    )
    # Task có "ERR-xxx" thường thiếu context và dễ sai → ưu tiên HITL/human review.
    unknown_error_signals = ("err-", "error code", "mã lỗi")

    # Risk flags: dùng để trigger HITL khi cần (đặc biệt cho emergency access, 2am, v.v.)
    risk_keywords = (
        "emergency",
        "khẩn cấp",
        "2am",
        "02:00",
        "ngoài giờ",
        "không rõ",
    )

    risk_high = _contains_any(task, risk_keywords)
    if _contains_any(task, unknown_error_signals):
        risk_high = True

    # needs_tool là "quyền" để policy/tool worker gọi MCP tools.
    # Với các câu policy/access thường cần check ngoại lệ hoặc tra cứu bổ sung.
    needs_tool = _contains_any(task, policy_or_access_keywords) or _contains_any(task, ("ticket", "p1"))

    # Route selection (order matters)
    if risk_high and _contains_any(task, unknown_error_signals):
        route = "human_review"
        route_reason = "unknown error signal detected with risk_high=True → human_review"
        # Khi human_review, thường chưa chắc cần tool; để False tránh tool call không cần thiết
        needs_tool = False
    elif _contains_any(task, policy_or_access_keywords):
        route = "policy_tool_worker"
        route_reason = "task contains policy/access keyword → policy_tool_worker"
    elif _contains_any(task, retrieval_keywords):
        route = "retrieval_worker"
        route_reason = "task contains SLA/ticket/escalation keyword → retrieval_worker"
    else:
        route = "retrieval_worker"
        route_reason = "default → retrieval_worker (need evidence before answering)"

    if risk_high:
        route_reason = f"{route_reason} | risk_high flagged"

    # Contract guard: route_reason must be meaningful
    if not route_reason.strip() or route_reason.strip().lower() == "unknown":
        route_reason = "default → retrieval_worker (route_reason guardrail applied)"
        route = "retrieval_worker"

    state["supervisor_route"] = route
    state["route_reason"] = route_reason
    state["needs_tool"] = needs_tool
    state["risk_high"] = risk_high
    state["history"].append(f"[supervisor] route={route} needs_tool={needs_tool} reason={route_reason}")

    return state


# ─────────────────────────────────────────────
# 3. Route Decision — conditional edge
# ─────────────────────────────────────────────

def route_decision(state: AgentState) -> Literal["retrieval_worker", "policy_tool_worker", "human_review"]:
    """
    Trả về tên worker tiếp theo dựa vào supervisor_route trong state.
    Đây là conditional edge của graph.
    """
    route = state.get("supervisor_route", "retrieval_worker")
    return route  # type: ignore


# ─────────────────────────────────────────────
# 4. Human Review Node — HITL placeholder
# ─────────────────────────────────────────────

def human_review_node(state: AgentState) -> AgentState:
    """
    HITL node: pause và chờ human approval.
    Trong lab này, implement dưới dạng placeholder (log + auto-approve).

    TODO Sprint 3 (optional): Implement actual HITL với interrupt_before hoặc
    breakpoint nếu dùng LangGraph.
    """
    state["hitl_triggered"] = True
    state["history"].append("[human_review] HITL triggered — awaiting human input")
    state["workers_called"].append("human_review")

    # Placeholder: auto-approve để pipeline tiếp tục trong lab mode.
    print("\n[HITL] human_review triggered (lab mode auto-approve)")
    print(f"  task  : {state['task']}")
    print(f"  reason: {state['route_reason']}\n")

    # Sau khi human approve, route về retrieval để lấy evidence
    state["supervisor_route"] = "retrieval_worker"
    state["route_reason"] += " | human approved → retrieval"

    return state


# ─────────────────────────────────────────────
# 5. Import Workers
# ─────────────────────────────────────────────

from workers.retrieval import run as retrieval_run
from workers.policy_tool import run as policy_tool_run
from workers.synthesis import run as synthesis_run


def retrieval_worker_node(state: AgentState) -> AgentState:
    """Wrapper gọi retrieval worker."""
    return retrieval_run(state)


def policy_tool_worker_node(state: AgentState) -> AgentState:
    """Wrapper gọi policy/tool worker."""
    return policy_tool_run(state)


def synthesis_worker_node(state: AgentState) -> AgentState:
    """Wrapper gọi synthesis worker."""
    return synthesis_run(state)


# ─────────────────────────────────────────────
# 6. Build Graph
# ─────────────────────────────────────────────

def build_graph():
    """
    Xây dựng graph với supervisor-worker pattern.

    Option A (đơn giản — Python thuần): Dùng if/else, không cần LangGraph.
    Option B (nâng cao): Dùng LangGraph StateGraph với conditional edges.

    Lab này implement Option A theo mặc định.
    TODO Sprint 1: Có thể chuyển sang LangGraph nếu muốn.
    """
    # Option A: Simple Python orchestrator
    def run(state: AgentState) -> AgentState:
        import time
        start = time.time()

        # Step 1: Supervisor decides route
        state = supervisor_node(state)

        # Step 2: Route to appropriate worker
        route = route_decision(state)

        if route == "human_review":
            state = human_review_node(state)
            # After human approval, continue with retrieval
            state = retrieval_worker_node(state)
        elif route == "policy_tool_worker":
            # For policy/access questions, retrieval first helps ground policy analysis.
            # Policy worker may still call MCP tools depending on needs_tool.
            state = retrieval_worker_node(state)
            state = policy_tool_worker_node(state)
        else:
            # Default: retrieval_worker
            state = retrieval_worker_node(state)

        # Step 3: Always synthesize
        state = synthesis_worker_node(state)

        state["latency_ms"] = int((time.time() - start) * 1000)
        state["history"].append(f"[graph] completed in {state['latency_ms']}ms")
        return state

    return run


# ─────────────────────────────────────────────
# 7. Public API
# ─────────────────────────────────────────────

_graph = build_graph()


def run_graph(task: str) -> AgentState:
    """
    Entry point: nhận câu hỏi, trả về AgentState với full trace.

    Args:
        task: Câu hỏi từ user

    Returns:
        AgentState với final_answer, trace, routing info, v.v.
    """
    state = make_initial_state(task)
    result = _graph(state)
    return result


def save_trace(state: AgentState, output_dir: str = "./artifacts/traces") -> str:
    """Lưu trace ra file JSON."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{state['run_id']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return filename


# ─────────────────────────────────────────────
# 8. Manual Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Windows console may default to legacy codepage; ensure UTF-8 to avoid print crashes.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # py>=3.7
    except Exception:
        pass

    print("=" * 60)
    print("Day 09 Lab - Supervisor-Worker Graph")
    print("=" * 60)

    test_queries = [
        "SLA xử lý ticket P1 là bao lâu?",
        "Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?",
        "Cần cấp quyền Level 3 để khắc phục P1 khẩn cấp. Quy trình là gì?",
    ]

    for query in test_queries:
        print(f"\n> Query: {query}")
        result = run_graph(query)
        print(f"  Route   : {result['supervisor_route']}")
        print(f"  Reason  : {result['route_reason']}")
        print(f"  Workers : {result['workers_called']}")
        print(f"  Answer  : {result['final_answer'][:100]}...")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Latency : {result['latency_ms']}ms")

        # Lưu trace
        trace_file = save_trace(result)
        print(f"  Trace saved -> {trace_file}")

    print("\nOK: graph.py test complete.")
