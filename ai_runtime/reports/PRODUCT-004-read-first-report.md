# PRODUCT-004 — Word Memo / Dika Document Generation (Revised Plan)

## 1. Exact Word Template Paragraph and Placeholder Mapping
An extraction of all 23 paragraphs in `Word Template.docx` reveals the following exact paragraph positions and surrounding context mapping:

| Paragraph Index | Surrounding Context Prefix | Original Placeholder | Destination Field / Source |
| :--- | :--- | :--- | :--- |
| **5** | `  รบ 54101/` | `[….]` | `Memo.memo_number` |
| **7** | `  ` | `[วันที่ทำรายการ]` | `Memo.memo_date` (Formatted to Thai BE Date) |
| **9** | `  ขออนุมัติเบิกจ่าย` | `[ ค่า....................]` | `Case.expense_group` |
| **12** | `ด้วยสำนักปลัดเทศบาล ได้รับแจ้ง` | `[ ค่า....................]` | `Case.expense_group` (Duplicate placeholder) |
| **12** | `ประจำเดือน` | `[……….. 25xx…]` | `Case.work_month` + `Case.fiscal_year_be` |
| **12** | `ตามใบแจ้งค่าใช้บริการของ` | `[…………………ผู้ออกบิล…………………..]` | `BillHeader.provider` |
| **12** | `เลขที่ ` | `[…………………..]` | `bill_number` (Extracted dynamically from `BillData`) |
| **12** | `และ ` | `[……………(กรณีมากกว่า 1 บิล)...]` | Omitted/Empty (for single bill mvp) |
| **12** | `ลงวันที่ ` | `[…….วันที่ออกบิล.......]` | `BillHeader.bill_date` (Formatted to Thai BE Date) |
| **12** | `รวมจำนวนเงิน ` | `[…………..]` | `BillHeader.total_amount` |
| **12** | (Total amount text block) | `[……………….บาท…..สตางค์]` | `BillHeader.total_amount` (via `bahttext()`) |
| **13** | `เบิกจ่ายค่าใช้บริการโทรศัพท์จำนวน ` | `[…………..]` | `BillHeader.total_amount` (Duplicate placeholder) |
| **13** | `ประจำปีงบประมาณ พ.ศ. ` | `[…25xx..]` | `Case.fiscal_year_be` |
| **13** | `ซึ่งขณะนี้งบประมาณคงเหลือ ` | `[………………………….]` | Remaining budget (Stubbed/Projected) |

---

## 2. Duplicate Placeholder & Positional Replacement Strategy
To avoid run-splitting corruption and correctly handle duplicate placeholders:
1. **Paragraph-level run merging**: Before replacing, if a paragraph contains the bracket delimiters, we will merge the text elements of all runs into the first run and clear subsequent runs. This preserves formatting while allowing clean search-and-replace.
2. **Deterministic Context Matches**:
   * Global replacements will resolve duplicate tokens like `[ ค่า....................]` and `[…………..]` accurately.
   * Special format conversions (e.g. converting `BillHeader.bill_date` $\rightarrow$ Thai date text like `10 พฤษภาคม 2569`, and total amount $\rightarrow$ `หนึ่งพันสองร้อยห้าสิบบาทถ้วน`) will be computed before replacement.

---

## 3. Revised Database Schema Changes
No modifications will be made to the `BillHeader` table.
* **`memos` Table Extension**: We will add `file_path` column to the `Memo` model to store the generated document destination.
```python
class Memo(Base):
    __tablename__ = "memos"

    id = Column(Integer, primary_key=True, index=True)
    dika_id = Column(Integer, ForeignKey("dikas.id"), nullable=False)
    memo_number = Column(String, nullable=True)
    memo_date = Column(Date, nullable=True)
    content = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)  # <-- Added
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

## 4. Minimal Dika & Memo Input Scope
The input payload from the UI for saving Dika details is strictly limited to:
* `dika_no` (maps to `Dika.dika_number` in DB)
* `dika_date` (maps to `Dika.dika_date`)
* `payee_name` (maps to `Case.vendor_name` to avoid altering BillHeader/Dika schema)
* `memo_number` (maps to `Memo.memo_number`)
* `memo_date` (maps to `Memo.memo_date`)

---

## 5. Backend API Endpoints
Under `src/product/api/cases.py`:
1. `POST /api/cases/{case_id}/dika`
   * **Body**:
     ```json
     {
       "dika_no": "123/2569",
       "dika_date": "2026-05-20",
       "payee_name": "บริษัท โทรคมนาคมแห่งชาติ จำกัด (มหาชน)",
       "memo_number": "45",
       "memo_date": "2026-05-20"
     }
     ```
   * **Action**: Saves `Dika` and `Memo` records; updates `Case.vendor_name` with `payee_name`.
2. `POST /api/cases/{case_id}/memo/generate`
   * **Action**:
     * Retrieves Case, Dika, Memo, and the case's associated `BillHeader`.
     * Dynamically invokes `UnifiedBillPipeline.run` on the source document's path to extract `bill_number` without storing it in `BillHeader`.
     * Fills `Word Template.docx`, outputs the file to `data/generated/case_{case_id}_memo.docx`, and writes the `file_path` to `Memo`.
     * Updates `Case.status` to `word_generated`.
3. `GET /api/cases/{case_id}/memo/download`
   * **Action**: Returns the generated docx file from the local path.

---

## 6. Frontend UI Details
Inside [page.tsx](file:///d:/utility_automation_v2_light/frontend/product-ui/app/cases/%5Bid%5D/page.tsx):
* Add a card/section labeled **"ข้อมูลฎีกาและบันทึกข้อความ" (Dika and Memo Information)**.
* **Fields**:
  * เลขที่ฎีกา (Dika No.)
  * วันที่ฎีกา (Dika Date)
  * ผู้รับเงิน (Payee Name)
  * เลขที่บันทึกข้อความ (Memo No.)
  * วันที่บันทึกข้อความ (Memo Date)
* **Actions**:
  * Button: **"บันทึกข้อมูลฎีกา" (Save Dika Data)**.
  * Button: **"สร้างบันทึกข้อความ Word" (Generate Word Memo)** (active if Dika details are saved).
  * Button: **"ดาวน์โหลดบันทึกข้อความ (.docx)"** (visible once generation completes).

---

## 7. Testing Strategy
* **Unit Tests (`tests/product/test_word_generation.py`)**:
  * Verify `bahttext` converts float numbers to correct Thai words.
  * Verify `thai_date_format` converts date to correct Thai year representation.
  * Mock `python-docx` file template replacement and verify paragraph run cleanup.
* **API Tests**:
  * Verify `POST /api/cases/{case_id}/dika` updates database records correctly.
  * Verify `POST /api/cases/{case_id}/memo/generate` runs cleanly.

---

## 8. Exclusions & Constraints
* **No OCR changes**: Keep pipeline unchanged.
* **No e-LAAS automation**: Out of scope.
* **No frontend redesign**: Keep existing clean tailwind dashboard styling.
* **No commit/push**: Blocked until explicit controller approval.
