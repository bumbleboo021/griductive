from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

SatOutcome = Literal["SAT", "UNSAT", "TIMEOUT"]

@dataclass
class SatQueryRecord:
     """Bản ghi chi tiết 1 lần gọi SAT solver"""
     cell: str

     # Giả định đƯợc truyền vào SAT solver:
     # "ASSUME_INNOCENT" = giả sử ô này là Innocent (¬Ci)
     # "ASSUME_CRIMINAL" = giả sử ô này là Criminal (Ci)
     # "BASE_CHECK" = kiểm tra tính nhất quán ban đầu của KB
     assumption_type: Literal["BASE_CHECK", "ASSUME_INNOCENT", "ASSUME_CRIMINAL"]
     outcome: SatOutcome
     entailed: Literal["CRIMINAL", "INNOCENT", None] = None

     def to_dict(self) -> dict:
          return{
               "ô": self.cell,
               "loại_giả_định": self.assumption_type,
               "kết_quả_SAT": self.outcome,
               "kết_luận": self.entailed,
          }

@dataclass
class TraceStep:
     """Bản ghi của một bước suy luận"""
     step_number: int
     active_clue_ids: list[str]
     sat_queries: list[SatQueryRecord] = field(default_factory=list)

     forced_cell: str | None = None
     forced_status: Literal["CRIMINAL", "INNOCENT", None] = None

     new_clue_id: str | None = None

     @property
     def num_sat_queries(self) -> int:
          """Tổng số lần gọi SAT solver ở bước này"""
          return len(self.sat_queries)

     @property
     def is_forced(self) -> bool:
          """Kiêm tra bước này có tìm được ô ép buộc không"""
          return self.forced_cell is not None

     def to_dict(self) -> dict:
          return{
               "bước": self.step_number,
               "số_manh_mối_đang_mở": len(self.active_clue_ids),
               "id_manh_mối_đang_mở": self.active_clue_ids,
               "số_truy_vấn_SAT": self.num_sat_queries,
               "chi_tiết_truy_vấn": [q.to_dict() for q in self.sat_queries],
               "ô_bị_ép_buộc": self.forced_cell,
               "phán_quyết": self.forced_status,
               "manh_mối_mới": self.new_clue_id,
          }

@dataclass
class DeductionTrace:
     """Bản ghi toàn bộ quá trình suy luận của Agent cho một màn chơi"""     
     puzzle_name: str
     board_size: int
     started_at: str = field(default_factory=lambda: datetime.now().isoformat())
     steps: list[TraceStep] = field(default_factory=list)

     # Trạng thối cuối cùng
     is_solved: bool = False
     is_stalled: bool = False
     is_inconsistent: bool = False

     # Các thuộc tính tính toán tổng hợp
     @property
     def total_steps(self) -> int:
          """Tổng số bước lật thẻ đã thực hiện"""
          return len(self.steps)

     @property
     def total_sat_calls(self) -> int:
          """Tổng số lần gọi SAT solver trong toàn bộ quá trình giải"""
          return sum(step.num_sat_queries for step in self.steps)

     @property
     def forced_steps(self) -> list[TraceStep]:
          """Lọc ra các bước mà Agent tìm được ô bị ép buộc"""
          return [s for s in self.steps if s.is_forced]

     # Các phương thức ghi nhật kí
     def begin_step(self, active_clue_ids: list[str]) -> TraceStep:
          """Bắt đầu một bước suy luận mới và trả về TraceStep để ghi thêm thông tin"""
          step = TraceStep(
               step_number = len(self.steps) + 1,
               active_clue_ids = list(active_clue_ids),
          )
          self.steps.append(step)
          return step

     def record_base_check(self, step: TraceStep, outcome: SatOutcome) -> None:
          """Ghi nhận kết quả kiểm tra tính nhất quán ban đầu của KB"""
          step.sat_queries.append(SatQueryRecord(
               cell="KB", 
               assumption_type="BASE_CHECK",
               outcome=outcome,
          ))

     def record_entailment_query(
               self,
               step: TraceStep,
               cell: str,
               assumption_type: Literal["ASSUME_INNOCENT", "ASSUME_CRIMINAL"],
               outcome: SatOutcome,
               entailed: Literal["CRIMINAL", "INNOCENT", None],
     ) -> None:
          """Ghi nhận một truy vấn phân loại ô và kết luận"""
          step.sat_queries.append(SatQueryRecord(
               cell=cell,
               assumption_type=assumption_type,
               outcome=outcome,
               entailed=entailed,
          ))

     def set_forced_verdict(
               self,
               step: TraceStep,
               cell: str,
               status: Literal["CRIMINAL", "INNOCENT"],
     ) -> None:
          """Ghi nhận phán quyết ép buộc được chọn trong bước này"""
          step.forced_cell  = cell
          step.forced_status = status

     def set_new_clue(self, step: TraceStep, clue_id: str | None) -> None:
          """Ghi nhận ID manh mối mới được lật sau khi phán quyết được chấp nhận"""
          step.new_clue_id = clue_id

     # Các phương thức xuất kết quả
     def print_summary(self) -> None:
          """In tóm tắt vết suy luận ra màn hình dạng văn bản"""
          print("=" * 65)
          print(f"  VẾT SUY LUẬN: {self.puzzle_name} (Bàn {self.board_size}×{self.board_size})")
          print(f"  Bắt đầu lúc: {self.started_at}")
          print("=" * 65)

          for step in self.steps:
               status_icon = "✓" if step.is_forced else "?"
               verdict_text = (
                    f"{step.forced_cell} -> {step.forced_status}"
                    if step.is_forced
                    else "Không tìm được ô bị ép buộc (STALLED)"
               )
               print(f"\n[Bước {step.step_number}] {status_icon} {verdict_text}")
               print(f"  Manh mối đang mở ({len(step.active_clue_ids)}): "
                     f"{', '.join(step.active_clue_ids) or '(chưa có)'}")
               print(f"  Số truy vấn SAT: {step.num_sat_queries}")

               for q in step.sat_queries:
                    prefix = "   ├─" if q != step.sat_queries[-1] else "   └─"
                    assumption_text = {
                         "BASE_CHECK": "Kiểm tra KB",
                         "ASSUME_INNOCENT": f"GIả sử {q.cell}=Innocent (¬C)",
                         "ASSUME_CRIMINAL": f"Giả sử {q.cell}=Criminal (C)",
                    }[q.assumption_type]
                    conclusion = f" → Kết luận: {q.entailed}" if q.entailed else ""
                    print(f"  {prefix} [{q.outcome}] {assumption_text}{conclusion}")

               if step.new_clue_id:
                    print(f"  Manh mối mới được lật: {step.new_clue_id}")

          print("\n" + "=" * 65)

          # Trạng thái kết thúc
          if self.is_solved:
               status_text = "✓ GIẢI XONG HOÀN TOÀN"
          elif self.is_inconsistent:
               status_text = "✗ PHÁT HIỆN MÂU THUẪN TRONG KB"
          elif self.is_stalled:
               status_text = "~ BẾ TẮC (Không còn ô nào ép buộc được)"
          else:
               status_text = "… ĐANG TIẾN HÀNH"

          print(f"  Trạng thái cuối:  {status_text}")
          print(f"  Tổng số bước:     {self.total_steps}")
          print(f"  Tổng SAT calls:   {self.total_sat_calls}")
          print("=" * 65)

     def to_dict(self) -> dict:
          """Chuyển toàn bộ vết suy luận sang dạng dict"""
          return{
               "tên_màn_chơi": self.puzzle_name,
               "kích_thước_bàn_cờ": self.board_size,
               "bắt_đầu_lúc": self.started_at,
               "trạng_thái": (
                    "SOLVED" if self.is_solved
                    else "INCONSISTENT" if self.is_inconsistent
                    else "STALLED" if self.is_stalled
                    else "IN_PROGRESS"
               ),
               "tổng_số_bước": self.total_steps,
               "tổng_SAT_calls": self.total_sat_calls,
               "chi_tiết_các_bước": [step.to_dict() for step in self.steps],
          }

     def to_json(self, indent: int = 2) -> str:
          """Xuất vết suy luận thành chuỗi JSON"""
          return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

     def save_json(self, filepath: str) -> None:
          """Lưu vết suy luận ra file JSON"""
          with open(filepath, "w", encoding="utf-8") as f:
               f.write(self.to_json())
          print(f"Đã lưu vết suy luận ra: {filepath}")