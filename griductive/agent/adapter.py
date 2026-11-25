from __future__ import annotations
import logging
from collections.abc import Mapping
from time import perf_counter
from typing import Tuple
from griductive.domain.models import Analysis, PublicState, Status
from griductive.agent.trace import DeductionTrace, TraceStep

logger = logging.getLogger(__name__)

class Agent:
     """Tác tử suy luận logic xây dựng trên bộ giải DPLL SAT"""

     def __init__(self, timeout_seconds: float = 3.0, strict_dpll: bool = False, *, on_sat_result=None) -> None:
          self.timeout_seconds = timeout_seconds
          self.on_sat_result = on_sat_result
          self.strict_dpll = strict_dpll
          self.last_query_count = 0
          self.last_sat_calls = 0
          self.last_solver_metrics = dict(decisions=0, propagations=0, backtracks=0)
          self.last_solver_runtime_ms = 0.0
          self.trace = None

     def analyze(self, state: PublicState) -> Analysis:
          """Phân tích trạng thái công khai hiện tại và phân loại các ô chưa giải
          
          Returns:
               Analysis(consistent = False, verdicts = ()) nếu KB công khai bị mâu thuẫn
               Analysis(consistent = True, verdicts = tuple(...)) chứa phân loại cho tất cả các ô chưa giải theo đúng thứ tự hàng trước
          """
          # Capture this live call, including failures, without reading puzzle files.
          self.last_trace_step = TraceStep(1, [clue.id for clue in state.clues])
          self.last_backend = "CNF / DPLL"
          self.last_fallback_reason = None
          self.last_cnf_counts = None
          self.last_query_count = 0
          self.last_sat_calls = 0
          self.last_solver_metrics = dict(decisions=0, propagations=0, backtracks=0)
          self.last_solver_runtime_ms = 0.0
          try:
               return self._analyze_with_trace(state, self.last_trace_step)
          finally:
               self.last_query_count = self.last_sat_calls

     def _solve_recorded(self, solve, **kwargs):
          """Measure actual solver invocations; missing counters stay unavailable."""
          self.last_sat_calls += 1
          started = perf_counter()
          try:
               result = solve(**kwargs)
          except Exception:
               self.last_solver_metrics = dict.fromkeys(self.last_solver_metrics)
               raise
          finally:
               self.last_solver_runtime_ms += (perf_counter()-started)*1000
          if self.on_sat_result is not None:
               self.on_sat_result(result)
          stats = getattr(result, 'stats', None)
          for name, total in self.last_solver_metrics.items():
               value = getattr(result, name, None)
               if value is None and stats is not None:
                    value = stats.get(name) if isinstance(stats, Mapping) else getattr(stats, name, None)
               valid = isinstance(value, int) and not isinstance(value, bool) and value >= 0
               self.last_solver_metrics[name] = total+value if total is not None and valid else None
          return result

     def run_trace(
               self,
               puzzle_path: str,
               puzzle_name: str = "Unknown",
     ) -> DeductionTrace:
          """Chạy giải toàn bộ 1 màn chơi và ghu lại vết suy luận
          
          Args:
               puzzle_path: Đường dẫn đến file JSON của màn chơi
               puzzle_name: Tên hiển thị của màn chơi
          
          Returns:
               DeductionTrace chứa toàn bộ nhật kí suy luận từng bước
          """
          from griductive.engine.game import GameEngine
          from griductive.engine.puzzle import load_puzzle
          from pathlib import Path

          puzzle = load_puzzle(Path(puzzle_path))
          engine = GameEngine(puzzle, self)

          trace = DeductionTrace(
               puzzle_name = puzzle_name,
               board_size = puzzle.size,
          )
          self.trace = trace
          self._active_trace = trace

          try:
               step_number = 0
               while not engine.solved:
                    step_number += 1
                    state = engine.public_state()

                    trace_step = trace.begin_step(
                         active_clue_ids = [c.id for c in state.clues]
                    )

                    analysis = self._analyze_with_trace(state, trace_step)

                    if not analysis.consistent:
                         trace.is_inconsistent = True
                         break

                    # Tìm ô ép buộc đầu tiên theo row-major
                    forced = next(
                         ((cell, status) for cell, status in analysis.verdicts
                          if status != Status.UNKNOWN),
                          None, 
                    )

                    if forced is None:
                         # Không tìm đƯợc ô nào bị ép buộc
                         trace.is_stalled = True
                         break

                    forced_cell, forced_status = forced
                    trace.set_forced_verdict(trace_step, forced_cell, forced_status.value)

                    # Gửi cho GameEngine
                    outcome = engine.submit_verdict(forced_cell, forced_status)

                    # Ghi nhận manh mối mới 
                    if outcome.code in ("ACCEPTED", "SOLVED"):
                         new_state = engine.public_state()
                         new_clue_ids = {c.id for c in new_state.clues}
                         old_clue_ids = {c.id for c in state.clues}
                         newly_revealed = new_clue_ids - old_clue_ids
                         new_clue_id = next(iter(newly_revealed), None)
                         trace.set_new_clue(trace_step, new_clue_id)

                    if outcome.code == "SOLVED":
                         trace.is_solved = True
                         break

          finally:
               self._active_trace = None

          return trace 

     def _analyze_with_trace(
               self, state: PublicState, trace_step: TraceStep
     ) -> Analysis:
          """Phân tích KB và ghi nhận chi tiết từng truy vấn SAT vào trace_step"""
          try:
               return self._analyze_via_dpll(state, trace_step = trace_step)

          except(ImportError, ModuleNotFoundError, NotImplementedError) as err:
               if self.strict_dpll:
                    raise
               logger.debug("Các module CNF/DPLL chưa sẵn sàng (%s). Chuyển sang bộ giải tham chiếu", err)
               self.last_backend = "Reference fallback"
               self.last_fallback_reason = str(err)
               return self._fallback_reference(state)

     def _analyze_via_dpll(self, state: PublicState, trace_step: TraceStep | None = None) -> Analysis:
          """Quy trình suy luận logic bằng CNF/DPLL
          
          Args:
               state: Trạng thái công khai hiện tại
               trace_step: Nếu không phải None, ghi nhận chi tiết các truy vấn SAT
          """
          from griductive.logic.encoder import encode
          self.last_sat_calls = 0
          self.last_solver_metrics = dict(decisions=0, propagations=0, backtracks=0)
          self.last_solver_runtime_ms = 0.0

          # Mã hóa trạng thái sang CNF
          cnf_result = encode(state)
          self.last_cnf_counts = (cnf_result.num_primary_vars,
                                  cnf_result.num_aux_vars, cnf_result.num_clauses)
          from griductive.sat.dpll import solve

          # Kiểm tra tính nhất quán của KBt
          base_res = self._solve_recorded(solve,
               clauses = cnf_result.clauses,
               total_vars = cnf_result.total_vars,
               assumptions = (),
               timeout_seconds = self.timeout_seconds,
          )

          # Ghi nhận kết quả kiểm tra KB vào trace
          if trace_step is not None:
               outcome_str = (
                    "TIMEOUT" if getattr(base_res, "is_timeout", False)
                    else "SAT" if base_res.is_sat else "UNSAT"
               )

               # Ghi trực tiếp vào danh sách truy vấn của trace_step
               from griductive.agent.trace import SatQueryRecord
               trace_step.sat_queries.append(SatQueryRecord(
                    cell = "KB",
                    assumption_type = "BASE_CHECK",
                    outcome = outcome_str,
               ))

          if getattr(base_res, "is_timeout", False):
               raise TimeoutError("Bộ giải SAT bị quá thời gian khi kiểm tra tính nhất quán của KB")

          if not base_res.is_sat:
               #KB mâu thuẫn
               return Analysis(consistent=False, verdicts=())

          # Lấy danh sách các ô chưa giải theo thứ tự hàng trước
          solved_cells = {cell for cell, _ in state.verdicts}
          unresolved_cells = [
               char.cell for char in state.characters if char.cell not in solved_cells
          ]

          # Phân loại từng ô chưa giải bằng suy luận phản chứng
          verdicts: list[Tuple[str, Status]] = []
          queries = 1

          for cell in unresolved_cells:
               var_id = cnf_result.cell_to_var[cell]

               # Query 1: Giả sử ô này là Innocent (Ci = False => assumption là -var_id)
               # Nếu KBt ^ ¬Ci là UNSAT => KBt |= Ci (ô này bắt buộc là CRIMINAL)
               res_innocent = self._solve_recorded(solve,
                    clauses = cnf_result.clauses,
                    total_vars = cnf_result.total_vars,
                    assumptions = (-var_id,),
                    timeout_seconds = self.timeout_seconds,
               )
               queries += 1
               if getattr(res_innocent, "is_timeout", False):
                    if trace_step is not None:
                         from griductive.agent.trace import SatQueryRecord
                         trace_step.sat_queries.append(SatQueryRecord(
                              cell, "ASSUME_INNOCENT", "TIMEOUT"))
                    raise TimeoutError(f"Bộ giải SAT bị quá thời gian khi phân tích ô {cell}")

               if not res_innocent.is_sat:
                    verdicts.append((cell, Status.CRIMINAL))

                    if trace_step is not None:
                         from griductive.agent.trace import SatQueryRecord
                         trace_step.sat_queries.append(SatQueryRecord(
                              cell = cell,
                              assumption_type = "ASSUME_INNOCENT",
                              outcome = "UNSAT",
                              entailed = "CRIMINAL",
                         ))
                    continue

               # Ghi nhận query 1 vào trace
               if trace_step is not None:
                    from griductive.agent.trace import SatQueryRecord
                    trace_step.sat_queries.append(SatQueryRecord(
                         cell = cell,
                         assumption_type = "ASSUME_INNOCENT",
                         outcome = "SAT",
                         entailed = None,
                    ))

               # Query 2: Giả sử ô này là Criminal (Ci = True => assumption là +var_id)
               # Nếu KBt ^ Ci là UNSAT => KBt |= ¬Ci (ô này bắt buộc là INNOCENT)
               res_criminal = self._solve_recorded(solve,
                    clauses = cnf_result.clauses,
                    total_vars = cnf_result.total_vars,
                    assumptions = (var_id,),
                    timeout_seconds = self.timeout_seconds,
               )
               queries += 1
               if getattr(res_criminal, "is_timeout", False):
                    if trace_step is not None:
                         from griductive.agent.trace import SatQueryRecord
                         trace_step.sat_queries.append(SatQueryRecord(
                              cell, "ASSUME_CRIMINAL", "TIMEOUT"))
                    raise TimeoutError(f"Bộ giải SAT bị quá thời gian khi phân tích ô {cell}")

               if not res_criminal.is_sat:
                    verdicts.append((cell, Status.INNOCENT))
                    if trace_step is not None:
                         from griductive.agent.trace import SatQueryRecord
                         trace_step.sat_queries.append(SatQueryRecord(
                              cell = cell,
                              assumption_type = "ASSUME_CRIMINAL",
                              outcome = "UNSAT",
                              entailed = "INNOCENT",
                         ))
                    continue

               # Ghi nhận query 1 vào trace
               if trace_step is not None:
                    from griductive.agent.trace import SatQueryRecord
                    trace_step.sat_queries.append(SatQueryRecord(
                         cell = cell,
                         assumption_type = "ASSUME_CRIMINAL",
                         outcome = "SAT",
                         entailed = None,
                    ))

               # Cả 2 đều SAT => UNKNOWN
               verdicts.append((cell, Status.UNKNOWN))

          self.last_query_count = queries
          return Analysis(consistent=True, verdicts=tuple(verdicts))

     def _fallback_reference(self, state: PublicState) -> Analysis:
          """Cơ chế dự phòng sang bộ phân tích tham chiếu"""
          from griductive.engine.reference import ReferenceAnalyzer
          return ReferenceAnalyzer(timeout=self.timeout_seconds).analyze(state)
