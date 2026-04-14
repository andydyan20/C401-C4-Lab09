# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Phạm Trần Thanh Lâm  
**Vai trò trong nhóm:** Trace & Docs Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

**Module/file tôi chịu trách nhiệm:**
- File chính: `graph.py` (phần định nghĩa `AgentState` và xuất trace list) và các template document báo cáo (bao gồm cả `group_report.md` và file export `eval_trace`).
- Functions tôi implement: Mở rộng `AgentState` để theo vết chi tiết hơn các hoạt động của hệ thống, thiết lập hàm `save_trace()` để xuất dữ liệu minh bạch, có đối chứng cho hệ thống Multi-Agent thay vì chỉ in ra console.

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Tôi tạo ra contract về cấu trúc Trace (bằng việc yêu cầu `worker_io_logs`, `mcp_tool_called`, `mcp_result` tồn tại ngay trong state). Nhờ vậy, Worker Owner (Hoàng Hiệp) và MCP Owner (Việt Cường) chỉ việc đẩy log vào đúng biến của State, thay vì tự format log ở mỗi node. Tôi cũng giúp Supervisor Owner (Tiến Dũng) kiểm chứng kết quả định tuyến thông qua các JSON output xuất ra `artifacts/traces/run_*.json`.

**Bằng chứng:**
Commit cập nhật biến `AgentState` để bắt thông tin trong file `graph.py`:
```python
    mcp_tool_called: list               # Trace list tên tool MCP đã gọi
    mcp_result: list                    # Trace list output MCP cho mỗi tool call
    workers_called: list                # Danh sách workers đã được gọi
    worker_io_logs: list                # Log input/output của từng worker theo contract
```

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Thêm explicit attributes trực tiếp vào `AgentState` để record trace (như `mcp_tool_called`, `worker_io_logs`, `mcp_result`) thay vì trộn mọi thứ vào 1 chuỗi list `history` chung.

**Lý do:**
Lúc đầu, toàn bộ thông tin log được nối chuỗi và nhét chung vào danh sách `history`. Điều này cực kì tệ hại cho tôi (Trace Owner) lúc parsing vì không thể dùng script `eval_trace.py` lập trình truy xuất dễ dàng do chuỗi dài khó phân tích. Do đó, tôi đưa ra quyết định yêu cầu nhóm lưu trace cụ thể bằng array/object để từng MCP call và Worker IO tách biệt hẵn ra. Điều này giúp tính điểm hoặc kiểm tra (VD: có gọi tool search_kb không?) trở nên tường minh. Nó cũng giúp đo đếm được worker latency dễ dàng nếu cần mở rộng.

**Trade-off đã chấp nhận:**
Dictionary `AgentState` bị phình to hơn đáng kể, làm memory tăng lên một li trong runtime, các bạn developer khác trong nhóm phải code rườm rà hơn một xíu khi trả về state.

**Bằng chứng từ trace/code:**
Khởi tạo state mới trong `make_initial_state`:
```python
        "mcp_tools_used": [],
        "mcp_tool_called": [],
        "mcp_result": [],
        "workers_called": [],
        "worker_io_logs": [],
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Dữ liệu trace xuất ra JSON không phản ánh đúng logic routing và thời gian trễ của toàn bộ graph (graph latency count bị hụt do tính thiếu).

**Symptom (pipeline làm gì sai?):**
Trong trace ban đầu được test trên bản console, thời gian trễ `latency_ms` của graph lúc nào cũng được phản ánh nhưng đôi lúc log ghi `completed in 0ms` mà lại mất một lúc mới chạy xong. Hoặc Supervisor bị miss logic điều chế vào Trace khi chạy thông qua LangGraph.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**
Lỗi nằm ở tracking logic. Khi gọi invoke Graph API (`_graph.invoke()`), nếu tracking time bị bỏ sót trước/sau invoke, hoặc logic gán bị ghi chồng trong các node, thì hệ thống không bắt kịp millisecond latency. Thêm vào đó việc thiếu mã hóa utf-8 trên console Windows dẫn tới lỗi hiển thị dấu mũi tên của Trace.

**Cách sửa:**
- Bọc lại bộ đếm `latency_ms` ở endpoint lớn nhất là `run_graph` (đo trực diện thời gian _graph.invoke chạy). Bổ sung encoding UTF-8 tại runtime console bằng khối `sys.stdout.reconfigure(encoding="utf-8")`.

**Bằng chứng trước/sau:**
Trước khi sửa (Lỗi Windows encoding console traceback):
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u25b6'
```

Sau khi tôi sửa trong file `graph.py` để tương thích Windows Console cho log:
```python
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # py>=3.7
    except Exception:
        pass
    ...
    print(f"\n> Query: {query}")
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi nhạy bén phát hiện các vấn đề giao tiếp giữa các thành viên. Nhờ việc thiết lập Contract tracking chuẩn (bộ đôi biến log Trace) từ sớm và đẩy mạnh export ra artifacts format chuẩn, team làm việc trơn tru hơn rất nhiều khi review mã của nhau. Group Report được tôi tổng hợp từ số liệu rất mạch lạc.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Do focus quá nhiều vào cấu trúc Trace evaluation, tôi chưa hỗ trợ quá sâu nhóm ở mảng xây prompt xịn cho LLM `synthesis_worker` - đây là khâu quan trọng để trả về answer hoàn hảo nhất.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_
Nếu tôi không xác định cấu hình JSON Trace chuẩn từ file `.json` ban đầu, việc grading điểm cho Agent thông qua file `grading_questions.json` và code `eval_trace` là bất khả thi.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_
Tôi phụ thuộc vào code của Worker & Supervisor Owner. Nếu các anh đó không update properties state theo đúng quy định tôi vạch ra vào node, thì array của log trả ra sẽ hoàn toàn trống rỗng không parse được số liệu.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ viết một tool nhỏ sử dụng Pandas (hoặc LangSmith dashboard setup) để vizualize cái `mcp_tool_called` và `latency_ms` cho chạy thử trên tập gq01-gq15. Hiện thời, trace JSON mới chỉ nằm dưới dạng text rời rạc phải đọc file từng cái, trace của câu ID gq09 cho thấy Worker có thể tốn hơn cả giây để trả ra kết quả do hit multi-hop. Biểu đồ sẽ thể hiện rõ nút thắt cổ chai hệ thống ở tool MCP hay ở độ trễ tổng hợp LLM.

---

*Lưu file này với tên: `reports/individual/PhamTranThanhLam.md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
