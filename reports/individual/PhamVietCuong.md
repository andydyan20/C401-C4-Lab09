# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Phạm Việt Cường  
**Vai trò trong nhóm:** MCP Owner  
**Ngày nộp:** 2026-04-14  
**Độ dài yêu cầu:** 500-800 từ

---

## 1. Tôi phụ trách phần nào? (100-150 từ)

Trong bài lab này, tôi phụ trách vai trò MCP Owner, tập trung vào hai điểm: implement mock MCP server và tích hợp MCP vào policy worker. Cụ thể, tôi làm việc trên `mcp_server.py` để đảm bảo server có tool `search_kb(query, top_k)` và `get_ticket_info(ticket_id)` theo đúng yêu cầu Sprint 3. Ở phía worker, tôi sửa `workers/policy_tool.py` để worker gọi MCP client (`dispatch_tool`) thay vì truy cập dữ liệu trực tiếp trong worker logic. Ngoài ra, tôi bổ sung trace fields `mcp_tool_called` và `mcp_result` để dễ quan sát từng lần gọi tool.

**Module/file tôi chịu trách nhiệm:**
- File chính: `mcp_server.py`, `workers/policy_tool.py`
- Functions tôi implement: `tool_search_kb()`, `_call_mcp_tool()`, cập nhật `run()` trong policy worker

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Phần của tôi nằm giữa supervisor/worker và trace owner: supervisor đặt `needs_tool`, policy worker gọi MCP tools, sau đó synthesis và eval đọc được trace chi tiết để phân tích.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

Commit `b56d2c8` trên nhánh `main`, gồm thay đổi trong `mcp_server.py`, `workers/policy_tool.py`, `graph.py` và trace xác nhận tool call.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150-200 từ)

**Quyết định:** Tôi chọn cách tích hợp MCP theo hướng "worker chỉ gọi tool qua MCP interface", không để worker phụ thuộc trực tiếp vào retrieval/chromadb internals.

**Lý do:**

Lúc đầu, worker có xu hướng làm quá nhiều việc: vừa policy check vừa tự truy cập tri thức. Tôi chọn gom external capability vào `dispatch_tool()` vì cách này đúng tinh thần MCP: policy worker không cần biết backend tra cứu bằng cách nào, chỉ cần tên tool và input schema. Hai lựa chọn thay thế là: (1) để worker tiếp tục gọi retrieval/chromadb trực tiếp; (2) dùng HTTP MCP server ngay lập tức. Tôi không chọn (1) vì tăng coupling và khó trace. Tôi tạm thời không chọn (2) vì lab yêu cầu mock MCP là đủ full credit, và ưu tiên ổn định.

**Trade-off đã chấp nhận:**

Mock in-process client nhanh để làm, nhưng chưa tạo boundary mạng rõ như MCP server thật. Đổi lại, code dễ đọc, dễ test, và có thể nâng cấp lên HTTP sau.

**Bằng chứng từ trace/code:**

```34:75:artifacts/traces/run_20260414_160843_mcp_policy.json
  "mcp_tools_used": [
    {
      "tool": "get_ticket_info",
      "mcp_tool_called": "get_ticket_info",
      "input": {
        "ticket_id": "P1-LATEST"
      },
      "output": {
        "ticket_id": "IT-9847",
        "priority": "P1",
        "status": "in_progress"
      },
      "mcp_result": {
        "ticket_id": "IT-9847",
        "priority": "P1",
        "status": "in_progress"
      }
    }
  ],
```

---

## 3. Tôi đã sửa một lỗi gì? (150-200 từ)

**Lỗi:** Trace chưa ghi rõ `mcp_tool_called` và `mcp_result` theo tiêu chí Sprint 3, chỉ có thông tin tổng hợp trong `mcp_tools_used`.

**Symptom (pipeline làm gì sai?):**

Khi đối chiếu với README/SCORING, tôi thấy trace tuy có danh sách tool calls nhưng thiếu hai trường được gọi tên cụ thể. Điều này làm việc debug mcp_call bị khó, vì người đọc phải suy luận từ object lớn thay vì có field chuẩn.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Lỗi nằm ở contract implementation trong `workers/policy_tool.py`: hàm `_call_mcp_tool()` chưa trả về keys `mcp_tool_called` và `mcp_result`; đồng thời `run()` chưa đưa 2 field này lên state top-level.

**Cách sửa:**

Tôi sửa `_call_mcp_tool()` để trả về bộ field đầy đủ (`tool`, `mcp_tool_called`, `input`, `output`, `mcp_result`, `timestamp`, `error`). Sau đó trong `run()`, mỗi lần gọi `search_kb`/`get_ticket_info` đều append vào `state["mcp_tool_called"]` và `state["mcp_result"]`. Tôi cũng bổ sung khởi tạo field trong `graph.py` để tránh missing-key khi trace run full graph.

**Bằng chứng trước/sau:**
> Trước: trace chỉ có `mcp_tools_used`.
> Sau: trace `artifacts/traces/run_20260414_160843_mcp_policy.json` có đầy đủ `mcp_tool_called` và `mcp_result` ở cả object tool-call và state-level list.

---

## 4. Tôi tự đánh giá đóng góp của mình (100-150 từ)

**Tôi làm tốt nhất ở điểm nào?**

Tôi làm tốt ở việc "đồng bộ yêu cầu bài tập -> code -> trace evidence". Sau khi implement, tôi không dừng ở mức code chạy được mà còn tạo trace thật để chứng minh tiêu chí MCP đã đạt.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Tôi chưa tối ưu hóa hoàn toàn cho trường hợp retrieval model tải lần đầu (cold start Chroma/embedding) nên có lúc test chậm. Nếu có thêm thời gian, tôi sẽ bổ sung chế độ fallback rõ hơn cho demo.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

Nếu tôi chưa xong MCP layer, policy worker không có external capability và Sprint 3 sẽ không đủ tiêu chí trace.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

Tôi phụ thuộc vào supervisor owner để set `needs_tool` hợp lý, và phụ thuộc trace/docs owner để tổng hợp kết quả từ các file trace vào báo cáo nhóm.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50-100 từ)

Tôi sẽ nâng cấp mock MCP thành HTTP MCP server (FastAPI + endpoint `tools/list` và `tools/call`) để worker gọi qua network boundary thay vì in-process import. Lý do: trong các lần test, trace đã cho thấy tool call được sử dụng thật; bước tiếp theo cần mở rộng để mô phỏng sản xuất tốt hơn, đặc biệt khi scale nhiều workers cùng gọi tools đồng thời.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
