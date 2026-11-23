"""Kiểm tra nghiệm duy nhất của toàn bộ màn chơi

Thuật toán kiểm tra bằng SAT Solver:
     1. Mã hóa toàn bộ tập manh mối của màn chơi sang CNF
     2. Gọi Solver tìm nghiệm đầu tiên của M1:
          - Nếu UNSAT => Vô nghiệm
     3. Tạo mệnh đề chặn trên các biến chính:
          Blocking Clause = OR_{v in primary_vars} (¬v nếu M1[v] == True else v)
     4. Thêm Blocking Clause vào công thức CNF và gọi Solver tìm nghiệm thứ hai:
          - Nếu UNSAT => Không tồn tại nghiệm nào khác => Nghiệm duy nhất
          - Nếu SAT => Tồn tại ít nhất 2 nghiệm khác nhau => Đa nghiệm
"""

from __future__ import annotations
import enum
import logging
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from griductive.domain.models import PublicState, Status
from griductive.engine.puzzle import Puzzle, load_puzzle

logger = logging.getLogger(__name__)

class UniquenessStatus(str, enum.Enum):
     """Trạng thái tính duy nhất của màn hình"""
     UNIQUE = "UNIQUE" # Có đúng 1 nghiệm duy nhất 
     AMBIGUOUS = "AMBIGUOUS" # Có từ 2 nghiệm trở lêm
     NO_SOLUTION = "NO_SOLUTION" # Vô nghiệm
     TIMEOUT = "TIMEOUT" # Bộ giải bị quá thời gian

@dataclass(frozen=True)
class UniquenessResult:
     """Kết quả kiểm tra tính duy nhất của nghiệm toàn màn chơi"""
     status: UniquenessStatus
     puzzle_name: str
     board_size: int

     # Nghiệm đầu tiên tìm được 
     first_model: dict[str, Status] | None = None

     # Nghiệm thứ 2 tìm được
     second_model: dict[str, Status] | None = None

     # Mệnh đề chặn đã tạo
     blocking_clause: tuple[int,...] | None = None

     # Các số liệu phục vụ thực nghiệm
     num_primary_vars: int = 0
     num_aux_vars: int = 0
     num_clauses_base: int = 0
     num_sat_calls: int = 0
     runtime_seconds: float = 0.0

     @property
     def is_unique(self) -> bool:
          """True khi và chỉ khi màn chơi có 1 nghiệm duy nhất"""
          return self.status == UniquenessStatus.UNIQUE

     def to_dict(self) -> dict:
          """Chuyển kết quả sang dict để truy xuất"""
          return{
               "màn_chơi": self.puzzle_name,
               "kích_thước": self.board_size,
               "trạng_thái": self.status.value,
               "nghiệm_duy_nhất": self.is_unique,
               "số_biến_chính": self.num_primary_vars,
               "số_biến_phụ": self.num_aux_vars,
               "số_mệnh_đề_gốc": self.num_clauses_base,
               "số_lần_goi_SAT": self.num_sat_calls,
               "thời_gian_giây": round(self.runtime_seconds,4),
               "nghiệm_thứ_nhất": (
                    {c: s.value for c, s in self.first_model.items()}
                    if self.first_model else None
               ),
               "nghiệm_thứ_hai": (
                    {c: s.value for c, s in self.second_model.items()}
                    if self.second_model else None 
               ),
               "mệnh_đề_chặn": list(self.blocking_clause) if self.blocking_clause else None,
          }

     def print_summary(self) -> None:
          """In kết quả kiểm tra ra màn hình"""
          print("=" * 65)
          print(f"  KIỂM TRA TÍNH DUY NHẤT: {self.puzzle_name} (Bàn {self.board_size}×{self.board_size})")
          print("=" * 65)
          print(f"  Trạng thái:          {self.status.value}")
          print(f"  Nghiệm duy nhất?     {'CÓ (HỢP LỆ)' if self.is_unique else 'KHÔNG'}")
          print(f"  Số biến chính:       {self.num_primary_vars}")
          print(f"  Số biến phụ:         {self.num_aux_vars}")
          print(f"  Số mệnh đề gốc:      {self.num_clauses_base}")
          print(f"  Số lần gọi SAT:      {self.num_sat_calls}")
          print(f"  Thời gian thực thi:  {self.runtime_seconds:.4f}s")
          if self.first_model:
               print(f"\n  Nghiệm thứ nhất M1:")
               crims = [c for c, s in sorted(self.first_model.items()) if s == Status.CRIMINAL]
               inns = [c for c, s in sorted(self.first_model.items()) if s == Status.INNOCENT]
               print(f"    - Criminals ({len(crims)}): {', '.join(crims)}")
               print(f"    - Innocents ({len(inns)}): {', '.join(inns)}")
          if self.status == UniquenessStatus.AMBIGUOUS and self.second_model:
               print(f"\n  Nghiệm thứ hai M2 (chứng minh đa nghiệm):")
               crims2 = [c for c, s in sorted(self.second_model.items()) if s == Status.CRIMINAL]
               inns2 = [c for c, s in sorted(self.second_model.items()) if s == Status.INNOCENT]
               print(f"    - Criminals ({len(crims2)}): {', '.join(crims2)}")
               print(f"    - Innocents ({len(inns2)}): {', '.join(inns2)}")
               diffs = [
                    c for c in sorted(self.first_model.keys())
                    if self.first_model[c] != self.second_model[c]
               ]
               print(f"    - Các ô khác biệt: {', '.join(diffs)}")
          if self.blocking_clause:
               preview = list(self.blocking_clause[:8])
               suffix = f"... ({len(self.blocking_clause)} literals)" if len(self.blocking_clause) > 8 else ""
               print(f"\n  Blocking Clause (chỉ trên biến chính): {preview} {suffix}")
          print("=" * 65)

def check_uniqueness(
          puzzle_or_path: Puzzle | str | Path,
          timeout_seconds: float = 5.0,
          strict_dpll: bool = False,
) -> UniquenessResult:
     """Kiểm tra tính duy nhất của nghiệm cho toàn bộ manh mối màn chơi
     
     Args:
          puzzle_or_path: Đối tượng Puzzle hoặc đường dẫn đến file JSON màn chơi
          timeout_seconds: Thời gian tối đa cho mỗi lần gọi SAT solver
          strict_dpll: Nếu True, chỉ dùng DPLL solver, không fallback sang tìm kiếm ngữ nghĩa
          
     Returns:
          UniquenessResult chứa kết luận UNIQUE, AMBIGUOUS, NO_SOLUTION, TIMEOUT
     """
     if isinstance(puzzle_or_path, (str, Path)):
          puzzle = load_puzzle(Path(puzzle_or_path))
          puzzle_name = Path(puzzle_or_path).stem
     else:
          puzzle = puzzle_or_path
          puzzle_name = getattr(puzzle, "title", "Puzzle")

     initial_verdicts = tuple(
          (c, s) for c, s in puzzle.solution if c in puzzle.initially_revealed
     )
     full_state = PublicState(
          size = puzzle.size,
          characters=puzzle.characters,
          verdicts=initial_verdicts,
          clues=puzzle.clues,
     )
     start_time = perf_counter()

     if strict_dpll:
          return _check_uniqueness_via_sat(full_state, puzzle_name, timeout_seconds, start_time)

     try:
          return _check_uniqueness_via_sat(full_state, puzzle_name, timeout_seconds, start_time)
     except (ImportError, ModuleNotFoundError, NotImplementedError) as err:
          logger.debug("SAT chưa sẵn sàng (%s). Dùng fallback ngữ nghĩa để kiểm tra", err)
          return _check_uniqueness_via_semantic(full_state, puzzle, puzzle_name, timeout_seconds, start_time)

def _check_uniqueness_via_sat(
          full_state: PublicState,
          puzzle_name: str,
          timeout_seconds: float,
          start_time: float,
) -> UniquenessResult:
     """Thuật toán kiểm tra tính duy nhất bằng SAT solver và Blocking Clause"""
     from griductive.logic.encoder import encode
     from griductive.sat.dpll import solve

     # B1: Mã hóa toàn bộ manh mối sang CNF
     cnf = encode(full_state)

     # B2: Gọi SAT solver để tìm nghiệm thứ nhất M1
     res1 = solve(
          clauses = cnf.clauses,
          total_vars = cnf.total_vars,
          assumptions = (),
          timeout_seconds = timeout_seconds,
     )

     if getattr(res1, "is_timeout", False):
          return UniquenessResult(
               status=UniquenessStatus.TIMEOUT,
               puzzle_name=puzzle_name,
               board_size=full_state.size,
               num_primary_vars=cnf.num_primary_vars,
               num_aux_vars=cnf.num_aux_vars,
               num_clauses_base=len(cnf.clauses),
               num_sat_calls=1,
               runtime_seconds=perf_counter() - start_time,
          )
     
     if not res1.is_sat or res1.model is None:
          # Không tìm được nghiệm nào thỏa
          return UniquenessResult(
               status=UniquenessStatus.NO_SOLUTION,
               puzzle_name=puzzle_name,
               board_size=full_state.size,
               num_primary_vars=cnf.num_primary_vars,
               num_aux_vars=cnf.num_aux_vars,
               num_clauses_base=len(cnf.clauses),
               num_sat_calls=1,
               runtime_seconds=perf_counter() - start_time,
          )

     # Chuyển nghiệm M1 sang tọa độ ô
     first_model: dict[str, Status] = {}
     for cell, var in cnf.cell_to_var.items():
          is_criminal = bool(res1.model.get(var, False))
          first_model[cell] = Status.CRIMINAL if is_criminal else Status.INNOCENT

     # B3: Tạo mệnh đề chặn chỉ trên biến chính
     blocking_clause = tuple(
          -var if res1.model.get(var, False) else var
          for var in sorted(cnf.primary_vars)
     )

     # B4: Thêm Blocking Clause và gọi SAT solver tìm nghiệm thứ 2 M2
     augmented_clauses = tuple(list(cnf.clauses) + [blocking_clause])
     res2 = solve(
          clauses = augmented_clauses,
          total_vars = cnf.total_vars,
          assumptions = (),
          timeout_seconds =timeout_seconds,
     )

     if getattr(res2, "is_timeout", False):
          return UniquenessResult(
               status=UniquenessStatus.TIMEOUT,
               puzzle_name=puzzle_name,
               board_size=full_state.size,
               first_model=first_model,
               num_primary_vars=cnf.num_primary_vars,
               num_aux_vars=cnf.num_aux_vars,
               num_clauses_base=len(cnf.clauses),
               num_sat_calls=2,
               runtime_seconds=perf_counter() - start_time,
          )

     if not res2.is_sat:
          # Nghiệm duy nhất
          return UniquenessResult(
               status=UniquenessStatus.UNIQUE,
               puzzle_name=puzzle_name,
               board_size=full_state.size,
               first_model=first_model,
               blocking_clause=blocking_clause,
               num_primary_vars=cnf.num_primary_vars,
               num_aux_vars=cnf.num_aux_vars,
               num_clauses_base=len(cnf.clauses),
               num_sat_calls=2,
               runtime_seconds=perf_counter() - start_time,
          )

     # res2.is_sat == True => Tìm thấy nghiệm thứ hai M2
     second_model: dict[str, Status] = {}
     for cell, var in cnf.cell_to_var.items():
          is_criminal = bool(res2.model.get(var, False))
          second_model[cell] = Status.CRIMINAL if is_criminal else Status.INNOCENT

     return UniquenessResult(
          status=UniquenessStatus.AMBIGUOUS,
          puzzle_name=puzzle_name,
          board_size=full_state.size,
          first_model=first_model,
          second_model=second_model,
          blocking_clause=blocking_clause,
          num_primary_vars=cnf.num_primary_vars,
          num_aux_vars=cnf.num_aux_vars,
          num_clauses_base=len(cnf.clauses),
          num_sat_calls=2,
          runtime_seconds=perf_counter() - start_time,
     )

def _check_uniqueness_via_semantic(
          full_state: PublicState,
          puzzle: Puzzle,
          puzzle_name: str,
          timeout_seconds: float,
          start_time: float,
) -> UniquenessResult:
     """Kiểm tra nghiệm duy nhất thông qua tìm kiếm ngữ nghĩa"""
     from griductive.engine.reference import possible

     cells = [c.cell for c in full_state.characters]
     initial_fixed = {c: s == Status.CRIMINAL for c, s in full_state.verdicts}
     models: list[dict[str, bool]] = []
     deadline = perf_counter() + timeout_seconds

     def backtrack(assignment: dict[str, bool]) -> None:
          if perf_counter() > deadline:
               raise TimeoutError("Quá thời gian khi kiểm tra nghiệm duy nhất")
          if not all(possible(clue, assignment) for clue in full_state.clues) :
               return

          unassigned = next((c for c in cells if c not in assignment), None)
          if unassigned is None:
               models.append(dict(assignment))
               return 

          for val in (False, True):
               assignment[unassigned] = val
               backtrack(assignment)
               del assignment[unassigned]
               if len(models) >= 2:
                    return

     try:
          backtrack(dict(initial_fixed))
     except TimeoutError:
          return UniquenessResult(
               status=UniquenessStatus.TIMEOUT,
               puzzle_name=puzzle_name,
               board_size=full_state.size,
               num_primary_vars=full_state.size * full_state.size,
               num_sat_calls=0,
               runtime_seconds=perf_counter() - start_time,
          )

     num_prim = full_state.size * full_state.size
     if len(models) == 0:
          status = UniquenessStatus.NO_SOLUTION
          m1, m2 = None, None

     elif len(models) == 1:
          status = UniquenessStatus.UNIQUE
          m1 = {c: Status.CRIMINAL if v else Status.INNOCENT for c, v in models[0].items()}
          m2 = None

     else:
          status = UniquenessStatus.AMBIGUOUS
          m1 = {c: Status.CRIMINAL if v else Status.INNOCENT for c, v in models[0].items()}
          m2 = {c: Status.CRIMINAL if v else Status.INNOCENT for c, v in models[1].items()} 
     
     return UniquenessResult(
          status=status,
          puzzle_name=puzzle_name,
          board_size=full_state.size,
          first_model=m1,
          second_model=m2, 
          num_primary_vars=num_prim,
          num_aux_vars=0,
          num_clauses_base=len(full_state.clues),
          num_sat_calls=len(models),
          runtime_seconds=perf_counter() - start_time,
     )