# Kết quả chấm điểm — Grading Questions (30 điểm nhóm)

> **File chấm:** `artifacts/grading_run.jsonl` (chạy lúc 18:17–18:19, 14/04/2026)  
> **Tiêu chí:** `data/grading_questions.json` + `SCORING.md` §3

---

## Tổng điểm

| Metric | Giá trị |
|--------|---------|
| **Tổng raw** | **68 / 96** |
| **Quy đổi 30 điểm** | **(68 / 96) × 30 = 21.25 / 30** |

---

## Chi tiết từng câu

### gq01 — SLA detail retrieval (10đ) → **5/10 (Partial)**

| Criteria | Đáp ứng? |
|----------|----------|
| Nêu đúng 3 kênh: Slack `#incident-p1`, email, PagerDuty | ❌ Chỉ nêu PagerDuty, thiếu Slack và email |
| Thời gian escalation: 22:57 (10 phút sau 22:47) | ✅ |
| Đối tượng escalation: Senior Engineer | ✅ |

**Nhận xét:** 2/3 criteria (≥50%), không hallucinate → **Partial = 50%**.  
Trace có `supervisor_route` + `route_reason` → không bị trừ 20%.

---

### gq02 — Temporal policy scoping (10đ) → **−5/10 (Penalty)**

| Criteria | Đáp ứng? |
|----------|----------|
| Nhận ra đơn trước 01/02 → áp dụng chính sách v3 | ✅ |
| Nêu rõ tài liệu chỉ có v4, không thể confirm theo v3 | ❌ Không đề cập |
| KHÔNG tự bịa nội dung v3 | ❌ **Bịa điều kiện v3** (7 ngày, chưa mở seal…) |

> [!CAUTION]
> Pipeline fabricated v3 policy content by copying v4 conditions and attributing them to v3. This triggers the **Penalty** rule: −50% = **−5 điểm**.

---

### gq03 — Multi-section access control (10đ) → **10/10 (Full)** ✨

| Criteria | Đáp ứng? |
|----------|----------|
| Số người phê duyệt: 3 | ✅ |
| Tên: Line Manager, IT Admin, IT Security | ✅ |
| Người cuối cùng: IT Security | ✅ |

**Nhận xét:** 3/3 criteria, trả lời chuẩn xác, cite nguồn `access_control_sop.txt`.

---

### gq04 — Specific numeric fact (6đ) → **6/6 (Full)** ✨

| Criteria | Đáp ứng? |
|----------|----------|
| Con số: 110% | ✅ |
| Giải thích: thêm 10% bonus so với hoàn tiền gốc | ✅ (implicit: "110% so với số tiền gốc cần hoàn") |

---

### gq05 — SLA escalation rule (8đ) → **8/8 (Full)** ✨

| Criteria | Đáp ứng? |
|----------|----------|
| Hành động: tự động escalate | ✅ |
| Đối tượng: Senior Engineer | ✅ |
| Không nêu sai thời gian/đối tượng | ✅ |

---

### gq06 — HR policy eligibility (8đ) → **8/8 (Full)** ✨

| Criteria | Đáp ứng? |
|----------|----------|
| Probation KHÔNG được remote | ✅ |
| Điều kiện: phải qua probation | ✅ |
| Giới hạn: 2 ngày/tuần + Team Lead phê duyệt | ✅ |

**Nhận xét:** Trả lời xuất sắc, còn bổ sung chi tiết ngày onsite bắt buộc.

---

### gq07 — Anti-hallucination / Abstain (10đ) → **10/10 (Full)** ✨

| Criteria | Đáp ứng? |
|----------|----------|
| Nêu rõ không có trong tài liệu | ✅ *"Không đủ thông tin trong tài liệu nội bộ."* |
| Không bịa con số phạt | ✅ |

> [!TIP]
> Đây là câu "bẫy" quan trọng nhất. Pipeline xử lý hoàn hảo — abstain rõ ràng, không hallucinate.

---

### gq08 — Multi-detail FAQ (8đ) → **8/8 (Full)** ✨

| Criteria | Đáp ứng? |
|----------|----------|
| Chu kỳ đổi mật khẩu: 90 ngày | ✅ |
| Cảnh báo trước: 7 ngày | ✅ |
| Cite nguồn: `it_helpdesk_faq.txt` | ✅ |

---

### gq09 — Cross-doc multi-hop (16đ) → **8/16 (Partial)**

**Phần (1) — SLA P1 Notification:**

| Criteria | Đáp ứng? |
|----------|----------|
| 3 kênh: Slack, email, PagerDuty | ⚠️ Nêu 2/3 (Slack + email), thiếu PagerDuty |
| Escalation: 10 phút → Senior Engineer | ❌ Không đề cập |

**Phần (2) — Level 2 Emergency Access:**

| Criteria | Đáp ứng? |
|----------|----------|
| Level 2 CÓ emergency bypass | ❌ *"Không đủ thông tin"* |
| Approval: Line Manager + IT Admin on-call | ❌ |
| Không cần IT Security cho Level 2 | ❌ |

**Nhận xét:** Theo rubric đặc biệt gq09 — trả lời được 1 trong 2 phần (SLA notification, dù thiếu sót) → **Partial = 8/16**.

---

### gq10 — Policy exception completeness (10đ) → **10/10 (Full)** ✨

| Criteria | Đáp ứng? |
|----------|----------|
| Kết luận: KHÔNG hoàn tiền | ✅ |
| Lý do: Flash Sale ngoại lệ, Điều 3, v4 | ✅ |
| Không bị đánh lừa bởi "lỗi nhà sản xuất" | ✅ |
| Cite nguồn: `policy_refund_v4.txt` | ✅ |

**Nhận xét:** Trả lời đúng kết luận với citation chính xác. Có đoạn giữa hơi mâu thuẫn ("Không đủ thông tin") nhưng kết luận cuối vẫn đúng.

---

## Bảng tổng hợp

| ID | Câu tóm tắt | Điểm tối đa | Điểm đạt | Mức |
|----|-------------|-------------|----------|-----|
| gq01 | P1 22:47 — kênh + deadline | 10 | **5** | Partial |
| gq02 | Đơn 31/01 hoàn tiền — v3 vs v4 | 10 | **−5** | Penalty ⚠️ |
| gq03 | Level 3 access — phê duyệt | 10 | **10** | Full ✨ |
| gq04 | Store credit = ?% | 6 | **6** | Full ✨ |
| gq05 | P1 10 phút không phản hồi | 8 | **8** | Full ✨ |
| gq06 | Probation remote | 8 | **8** | Full ✨ |
| gq07 | Mức phạt SLA (bẫy) | 10 | **10** | Full ✨ |
| gq08 | Mật khẩu 90 ngày + cảnh báo | 8 | **8** | Full ✨ |
| gq09 | P1 2am + Level 2 emergency | 16 | **8** | Partial |
| gq10 | Flash Sale + lỗi NSX | 10 | **10** | Full ✨ |
| | | **96** | **68** | |

---

## Điểm quy đổi

```
Điểm grading = (68 / 96) × 30 = 21.25 / 30 điểm
```

> [!IMPORTANT]
> **7/10 câu đạt Full marks.** Điểm bị mất chủ yếu do:
> - **gq02 (−5đ):** Hallucination — bịa nội dung policy v3
> - **gq09 (−8đ):** Retrieval không cross-document được (thiếu access_control_sop cho phần Level 2)
> - **gq01 (−5đ):** Thiếu 2/3 kênh notification
