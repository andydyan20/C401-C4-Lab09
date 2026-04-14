# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Đặng Tiến Dũng - 2A202600024
**Vai trò trong nhóm:** Worker Owner  
**Ngày nộp:** 2026-04-14  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (150 từ)

Tôi phụ trách vai trò **Worker Owner**, chịu trách nhiệm trực tiếp trong việc hiện thực hóa các node xử lý logic nghiệp vụ sau khi Supervisor đã điều phối request. Cụ thể:
- **Retrieval Worker (`workers/retrieval.py`)**: Xây dựng engine tìm kiếm ngữ nghĩa dùng ChromaDB, đảm bảo kết quả trả về đúng format `retrieved_chunks` với đầy đủ metadata.
- **Policy Tool Worker (`workers/policy_tool.py`)**: Phát triển bộ kiểm soát chính sách (policy analyzer) để nhận diện các ngoại lệ (exceptions) như Flash Sale hay sản phẩm đã kích hoạt.
- **Synthesis Worker (`workers/synthesis.py`)**: Xây dựng logic tổng hợp câu trả lời grounded, đảm bảo LLM chỉ trả lời dựa vào bằng chứng (evidence) và trích dẫn nguồn chính xác.
- **Worker Contracts**: Đảm bảo toàn bộ input/output của các worker tuân thủ nghiêm ngặt file `worker_contracts.yaml`.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (200 từ)

**Quyết định:** Tôi quyết định sử dụng **Hybrid Logic (kết hợp Rule-based và LLM context)** trong `policy_tool_worker` thay vì chỉ dựa hoàn toàn vào việc prompt cho LLM ở node Synthesis.

**Lý do:** 
Trong các tình huống nhạy cảm về chính sách (như hoàn tiền), LLM có thể bị hallucinate hoặc không nắm bắt được các "ngoại lệ cứng" (flash sale, digital products). Bằng cách sử dụng logic kiểm tra cứng ngay tại worker này, tôi có thể gắn các nhãn `exceptions_found` rõ ràng vào state. Điều này giúp hệ thống trở nên minh bạch: nếu LLM trả lời sai, tôi có thể tra cứu trace và khẳng định ngay là do logic kiểm tra chính sách của worker hay do LLM không tuân thủ prompt.

**Trade-off:**
Việc sử dụng rule-based đòi hỏi tôi phải cập nhật code khi chính sách công ty thay đổi (không linh hoạt bằng LLM). Tuy nhiên, đổi lại là sự an toàn tuyệt đối cho các nghiệp vụ tài chính.

**Bằng chứng từ trace/code:**
Trong `workers/policy_tool.py`, tôi đã triển khai bộ check ngoại lệ cụ thể:
```python
if any(kw in task_lower for kw in ["license key", "license", "subscription"]):
    exceptions_found.append({
        "type": "digital_product_exception",
        "rule": "Sản phẩm kỹ thuật số không được hoàn tiền (Điều 3)."
    })
```
Kết quả trace run `test_workers.py` cho thấy `policy_applies` chuyển sang `False` ngay khi phát hiện từ khóa "flash sale", bảo vệ hệ thống khỏi các quyết định sai lầm.

---

## 3. Tôi đã sửa một lỗi gì? (200 từ)

**Lỗi:** **Dimension Mismatch (384 vs 1536) trong Retrieval Worker**.

**Symptom:** Khi chạy test độc lập cho Retrieval Worker, hệ thống liên tục crash với thông báo lỗi: `⚠️ ChromaDB query failed: Collection expecting embedding with dimension of 384, got 1536`.

**Root cause:** 
Đây là lỗi phát sinh trong quá trình chuyển đổi hạ tầng. Ban đầu, database được indexed cục bộ (offline) bằng SentenceTransformer (384 dimensions). Nhưng khi tôi implement code dùng OpenAI trong worker để tăng chất lượng search, model mới (`text-embedding-3-small`) sinh ra vector 1536 dimensions. Việc so sánh vector khác chiều không gian là nhiệm vụ bất khả thi đối với ChromaDB.

**Cách sửa:**
Tôi đã buộc phải thực hiện re-index toàn bộ Knowledge Base. Tôi đã viết một script tạm thời gọi OpenAI API để tạo lại vector cho tất cả tài liệu hiện có, đảm bảo collection `day09_docs` thống nhất với model mà worker đang sử dụng.

**Bằng chứng trước/sau:**
- **Trước khi sửa:** Output báo lỗi `dimension mismatch`, `chunks_count: 0`.
- **Sau khi sửa:** Chạy `python workers/test_workers.py` trả về `Result: 3 chunks found.` cho câu hỏi về P1 SLA, chứng minh việc đồng bộ hóa model đã thành công.

---

## 4. Tôi tự đánh giá đóng góp của mình (150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã xây dựng được bộ Worker có tính Module hóa cực cao. Mỗi worker đều có thể chạy độc lập (standalone) thông qua block `if __name__ == "__main__"`. Điều này không chỉ giúp tôi debug nhanh mà còn giúp Supervisor Owner có thể tích hợp code của tôi vào graph một cách mượt mà mà không lo xung quanh.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Logic xử lý `confidence` trong Synthesis worker của tôi vẫn còn sơ sài, chủ yếu dựa vào similarity score từ ChromaDB. Chỗ này nên được cải thiện bằng cách dùng LLM-as-Judge để đánh giá độ khớp giữa câu trả lời và context.

**Nhóm phụ thuộc vào tôi ở đâu?**
Supervisor Owner phụ thuộc hoàn toàn vào output từ worker của tôi để đưa ra phản hồi cuối cùng. Nếu tôi chưa xong worker logic, hệ thống chỉ là một "bộ não" trống rỗng không có thông tin.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi phụ thuộc vào Supervisor Owner trong việc tách task. Nếu Supervisor parse sai task (nhầm từ HR sang IT), worker của tôi sẽ retrieve sai tài liệu hoặc áp dụng nhầm chính sách.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (100 từ)

Tôi sẽ tập trung vào việc tối ưu **Context Window** cho Synthesis worker. Hiện nay tôi đang truyền toàn bộ chunk văn bản vào LLM. Với thêm 2 giờ, tôi sẽ implement một bước lọc trung gian để loại bỏ các thông tin thừa trong chunk (noise reduction), giúp LLM tập trung hơn vào evidence chính xác, từ đó tăng độ tin cậy (confidence score) được log trong trace.

---
