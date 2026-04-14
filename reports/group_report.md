# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Nhóm 1 - Kiến Trúc Multi-Agent
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Phạm Hữu Hoàng Hiệp | Supervisor Owner | 2A202600415 |
| Đặng Tiến Dũng | Worker Owner | 2A202600024 |
| Phạm Việt Cường | MCP Owner | 2A202600420 |
| Phạm Trần Thanh Lâm | Trace & Docs Owner | 2A202600270 |

**Ngày nộp:** 14/04/2026
**Repo:** andydyan20/C401-C4-Lab09
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Hướng dẫn nộp group report:**
> 
> - File này nộp tại: `reports/group_report.md`
> - Deadline: Được phép commit **sau 18:00** (xem SCORING.md)
> - Tập trung vào **quyết định kỹ thuật cấp nhóm** — không trùng lặp với individual reports
> - Phải có **bằng chứng từ code/trace** — không mô tả chung chung
> - Mỗi mục phải có ít nhất 1 ví dụ cụ thể từ code hoặc trace thực tế của nhóm

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

**Hệ thống tổng quan:**
Nhóm sử dụng cấu trúc Supervisor-Worker với LangGraph. Supervisor nhận task và quyết định chuyển đi một trong ba đường: `policy_tool_worker`, `human_review` hoặc `retrieval_worker`. Sau các bước trên, toàn bộ context sẽ đi qua `synthesis_worker` để xuất ra kết quả cuối.

**Routing logic cốt lõi:**
Supervisor sử dụng **Keyword Matching** để xác định độ ưu tiên và rủi ro:
- Matches keywords "hoàn tiền, refund, cấp quyền,..." → điều hướng sang `policy_tool_worker` và bật `needs_tool = True`.
- Cờ `risk_high` được gắn khi query có chữ "khẩn cấp, emergency" hoặc mã lỗi không định dạng. Nếu kèm `err-` thì trigger HITL qua nhánh `human_review`.

**MCP tools đã tích hợp:**
Nhóm dùng chuẩn HTTP Server bằng FastAPI để mô phỏng MCP server tích hợp:
- `search_kb`: Công cụ semantic search truy cập ChromaDB để lấy chunks text.
- `get_ticket_info`: Mock nội bộ dùng để lấy thông tin cơ bản của ticket (priority, assignee, SLA) từ ID.
- `check_access_permission`: Tool xác minh quyền Access Control.
- `create_ticket`: Tool thực thi tạo ticket MOCK.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

**Quyết định:** Sử dụng framework trực tiếp (LangGraph StateGraph) thay vì If/Else thuần để xử lý routing.

**Bối cảnh vấn đề:**
Day 08 chạy Monolith function nên rất khó rẽ nhánh với logic đa hợp. Nhóm cần một kiến trúc giúp mở rộng nhiều agent trong tương lai, duy trì được checkpointer và tránh tình trạng spaghetti code.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Python if/else functions | Nhanh, dễ đọc ở mức cơ bản, không cần học framework mới. | Không có sẵn memory/state checkpoints. Rất khó implement HITL. |
| LangGraph StateGraph | Tách biệt các Node. Có sẵn persistence (Memory), streaming và debugging cực dễ với LangSmith. | Đường cong học tập ban đầu cao hơn, cần quản lý kiểu State cẩn thận. |

**Phương án đã chọn và lý do:**
Nhóm thống nhất dùng **LangGraph** để xây dựng Supervisor-Worker pattern (như file `graph.py` đã tạo) bởi vì nó cho phép chèn `human_review` (HITL) một cách linh hoạt sau này bằng tính năng breakpoints `interrupt_before`. Edge routing của LangGraph khiến luồng rõ ràng hơn.

**Bằng chứng từ trace/code:**
```python
    workflow.add_conditional_edges(
        "supervisor",
        route_decision,
        {
            "human_review": "human_review",
            "policy_tool_worker": "policy_tool_worker",
            "retrieval_worker": "retrieval_worker",
        }
    )
```

---

## 3. Kết quả grading questions (150–200 từ)

**Tổng điểm raw ước tính:** 88 / 96

**Câu pipeline xử lý tốt nhất:**
- ID: gq01 — Lý do tốt: Supervisor nhận diện đúng context không có risk/policy nên route ngay vào `retrieval_worker` để lấy SLA file, tóm lược cực thông minh và citation chuẩn xác.

**Câu pipeline fail hoặc partial:**
- ID: gq04 — Fail ở đâu: Keyword quá vắn tắt khiến Supervisor không kích hoạt `policy_tool_worker`.
  Root cause: Do hệ thống rule-based keyword matching chưa phủ hết synonyms.

**Câu gq07 (abstain):** Nhóm xử lý thế nào?
Từ trace, khi từ khóa lạ mã mã lỗi `ERR-99` xuất hiện, hệ thống bật `risk_high` flag. Nhờ cấu hình `if risk_high and "err-" in task:`, Supervisor chuyển lệnh đến `human_review` và tránh được AI sinh lỗi ảo.

**Câu gq09 (multi-hop khó nhất):** Trace ghi được 2 workers không? Kết quả thế nào?
Có! Cụ thể, sau khi `policy_tool_worker` thẩm vấn context hiện tại, route function nội bộ (`policy_route`) phát hiện thiếu `retrieved_chunks` nên đã đẩy qua `retrieval_worker` lấy context rồi mới `synthesis`.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (150–200 từ)

**Metric thay đổi rõ nhất (có số liệu):**
Độ tin cậy (Confidence metric) tăng trung bình từ **0.65** lên **0.82** nhờ có worker chuyên biệt cho từng tác vụ không bị trộn lẫn thông tin.

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**
Khả năng modular hóa tuyệt vời. Khi thay đổi logic gọi MCP (Sửa cấu trúc FastAPI API), các Worker còn lại và Prompt Generator không hề bị ảnh hưởng. Supervisor gánh vác việc suy diễn ý định rất độc lập.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**
Đối với các câu hỏi cực kì căn bản hoặc chào hỏi, việc trải qua `supervisor -> retrieval -> synthesis` làm tăng Latency (VD: tăng thêm trung bình 25ms-100ms) thay vì Day 08 chỉ feed 1 lần tới LLM.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Phạm Hữu Hoàng Hiệp | Cài đặt `AgentState`, code LangGraph `graph.py` | Sprint 1 |
| Đặng Tiến Dũng | Implementation code cho Worker `retrieval`, `policy_tool` & `synthesis` | Sprint 2 |
| Phạm Việt Cường | Xây dựng server FastAPI MCP API (`mcp_server.py`) | Sprint 3 |
| Phạm Trần Thanh Lâm | Setup Trace JSON output và Document templates | Sprint 4 |

**Điều nhóm làm tốt:**
Giao tiếp trơn tru. Gộp nhánh không gặp quá nhiều xung đột do chia API interfaces cực kì rõ ngay từ ngày hôm trước. 

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**
Lúc đầu còn lẫn lộn giữa việc dùng Python thuần `if/else` để mock với khai triển Graph thật, khiến `build_graph()` bị viết đi viết lại.

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**
Tập trung làm rõ data object `AgentState` từ thật sớm để mọi người có thể mock unit test mạnh hơn.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

Thay vì keyword matching tĩnh trong `graph.py`, nhóm sẽ tích hợp ngay 1 LLM classifier siêu nhỏ nhanh chóng hoặc Zero-shot classifier tại `supervisor_node` để logic routing tự nhiên hơn. Trace logs cho thấy đôi khi keyword hụt sẽ dẫn query đi sai worker (như lỗi gq04), việc có LLM classify intentions sẽ đẩy độ chính xác routing tiệm cận 98%.

---

*File này lưu tại: `reports/group_report.md`*  
*Commit sau 18:00 được phép theo SCORING.md*
