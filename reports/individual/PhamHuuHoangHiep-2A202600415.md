# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Phạm Hữu Hoàng Hiệp  
**Vai trò trong nhóm:** Supervisor Owner  
**Ngày nộp:** 2026-04-14  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Tôi phụ trách lớp điều phối (orchestration) theo Supervisor–Worker pattern, tập trung làm cho luồng chạy end-to-end rõ ràng và trace được. Module/file tôi chịu trách nhiệm chính là `graph.py`, nơi định nghĩa `AgentState`, implement `supervisor_node()` và `route_decision()`, và kết nối pipeline: supervisor → route → worker phù hợp → synthesis.

Phần của tôi kết nối trực tiếp với các worker ở `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py`: supervisor chỉ quyết định route và set cờ `needs_tool`/`risk_high`, còn workers thực thi nghiệp vụ và ghi `worker_io_logs` để phục vụ trace. Tôi đảm bảo state field đồng nhất để các worker append log mà không lỗi key.

**Module/file tôi chịu trách nhiệm:**
- File chính: `graph.py`
- Functions tôi implement/chỉnh: `AgentState`, `make_initial_state()`, `supervisor_node()`, `route_decision()`, các node wrappers và flow trong `build_graph()`

**Bằng chứng:** thay đổi nằm trực tiếp trong `graph.py` (routing + state + gọi worker thật).

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Tôi chọn **keyword-based routing + guardrail cho `route_reason`** trong `supervisor_node()` thay vì dùng LLM để phân loại câu hỏi.

**Lý do:** Trong lab này, các nhóm câu hỏi khá rõ (policy/access vs SLA/ticket vs unknown error). Keyword routing giúp điều phối đơn giản, dễ giải thích, và quan trọng nhất là **trace minh bạch** (rubric trừ điểm nếu thiếu `route_reason`). Tôi thêm guardrail để đảm bảo `route_reason` không rỗng/không phải “unknown” theo `contracts/worker_contracts.yaml`.

**Trade-off đã chấp nhận:** Keyword routing có thể miss câu diễn đạt lạ; LLM classifier có thể “thông minh” hơn nhưng khó kiểm soát khi route sai. Để giảm rủi ro, tôi dùng `risk_high` flag (khẩn cấp/2am/err-) và route sang `human_review` khi gặp tín hiệu mã lỗi không rõ.

**Bằng chứng từ code:**
https://github.com/andydyan20/C401-C4-Lab09/commit/b9fc3f94772719dc4c56af31d90a36272674ca06
https://github.com/andydyan20/C401-C4-Lab09/commit/7e59aaa5aa0e234299cd71d521062a84d975fef9

```
route_reason = "task contains policy/access keyword → policy_tool_worker"
route_reason = "task contains SLA/ticket/escalation keyword → retrieval_worker"
route_reason = "unknown error signal detected with risk_high=True → human_review"
if not route_reason.strip() or route_reason.strip().lower() == "unknown":
    route_reason = "default → retrieval_worker (route_reason guardrail applied)"
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Chạy `python graph.py` bị crash trên Windows do lỗi encoding khi in tiếng Việt/ký tự Unicode.

**Symptom (pipeline làm gì sai?):** Chương trình dừng với lỗi `UnicodeEncodeError: 'charmap' codec can't encode character ...` khi `print()` tiếng Việt/ký tự Unicode, nên chưa tạo được trace.

**Root cause:** Windows console có thể dùng codepage legacy, không hỗ trợ đầy đủ tiếng Việt/symbol; phần manual test trong `graph.py` in Unicode nên crash.

**Cách sửa:** Tôi cấu hình stdout UTF-8 bằng `sys.stdout.reconfigure(encoding="utf-8")` và thay một số symbol bằng ASCII trong output test để chạy ổn định.

**Bằng chứng trước/sau:** Sau sửa, `python graph.py` chạy hết các test queries và lưu trace vào `artifacts/traces/…json` thay vì crash ngay khi print.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?** Tôi làm rõ ranh giới supervisor/workers (supervisor chỉ route + flag), và đảm bảo trace có đủ trường quan trọng (`supervisor_route`, `route_reason`, `workers_called`, `worker_io_logs`) để debug được.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?** Routing còn thiên về keyword nên có thể miss câu đa nghĩa; tôi cũng chưa tối ưu latency (ví dụ load embedding model lặp).

**Nhóm phụ thuộc vào tôi ở đâu?** Nếu `graph.py` không chạy end-to-end hoặc trace thiếu `route_reason`, nhóm sẽ mất điểm và không tạo được `grading_run.jsonl`.

**Phần tôi phụ thuộc vào thành viên khác:** Tôi phụ thuộc vào worker owners để retrieval/policy/synthesis trả đúng field theo contract (citation/abstain/exception) nhằm tránh hallucination.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ bổ sung một lớp **routing cho câu multi-hop** (ví dụ dạng gq09: vừa “P1 escalation” vừa “emergency access”) để supervisor gọi **cả retrieval và policy_tool** có chủ đích hơn, thay vì dựa vào keyword đơn lẻ. Lý do: các câu multi-hop cần cross-reference nhiều tài liệu; trace sẽ cho thấy câu nào chỉ gọi 1 nhánh dẫn đến thiếu ý và confidence thấp.

