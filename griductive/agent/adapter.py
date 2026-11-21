from __future__ import annotations
import logging
from typing import Tuple
from griductive.domain.models import Analysis, PublicState, Status

logger = logging.getLogger(__name__)

class Agent:
     """Tác tử suy luận logic xây dựng trên bộ giải DPLL SAT"""

     def __init__(self, timeout_seconds: float = 3.0, strict_dpll: bool = False) -> None:
          self.timeout_seconds = timeout_seconds
          self.strict_dpll = strict_dpll
          self.last_query_count = 0

     def analyze(self, state: PublicState) -> Analysis:
          """Phân tích trạng thái công khai hiện tại và phân loại các ô chưa giải
          
          Returns:
               Analysis(consistent = False, verdicts = ()) nếu KB công khai bị mâu thuẫn
               Analysis(consistent = True, verdicts = tuple(...)) chứa phân loại cho tất cả các ô chưa giải theo đúng thứ tự hàng trước
          """
          if self.strict_dpll:
               return self._analyze_via_dpll(state)

          try:
               return self._analyze_via_dpll(state)

          except (ImportError, ModuleNotFoundError, NotImplementedError) as err:
               logger.debug("Các module CNF/DPLL chưa sẵn sàng (%s). Chuyển sang bộ giải tham chiếu", err)
               return self._fallback_reference(state)

     def _analyze_via_dpll(self, state: PublicState) -> Analysis:
          """Quy trình suy luận logic ằng CNF/DPLL"""
          from griductive.logic.encoder import encode
          from griductive.sat.dpll import solve

          # Mã hóa trạng thái sang CNF
          cnf_result = encode(state)

          # Kiểm tra tính nhất quán của KBt
          base_res = solve(
               clauses = cnf_result.clauses,
               total_vars = cnf_result.total_vars,
               assumptions = (),
               timeout_seconds = self.timeout_seconds,
          )

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
               res_innocent = solve(
                    clauses = cnf_result.clauses,
                    total_vars = cnf_result.total_vars,
                    assumptions = (-var_id,),
                    timeout_seconds = self.timeout_seconds,
               )
               queries += 1
               if getattr(res_innocent, "is_timeout", False):
                    raise TimeoutError(f"Bộ giải SAT bị quá thời gian khi phân tích ô {cell}")

               if not res_innocent.is_sat:
                    verdicts.append((cell, Status.CRIMINAL))
                    continue

               # Truy vấn 2: Giả sử ô này là Criminal (Ci = True => assumption là +var_id)
               # Nếu KBt ^ Ci là UNSAT => KBt |= ¬Ci (ô này bắt buộc là INNOCENT)
               res_criminal = solve(
                    clauses = cnf_result.clauses,
                    total_vars = cnf_result.total_vars,
                    assumptions = (var_id,),
                    timeout_seconds = self.timeout_seconds,
               )
               queries += 1
               if getattr(res_criminal, "is_timeout", False):
                    raise TimeoutError(f"Bộ giải SAT bị quá thời gian khi phân tích ô {cell}")

               if not res_criminal.is_sat:
                    verdicts.append((cell, Status.INNOCENT))
                    continue 

               # Cả 2 đều SAT => UNKNOWN
               verdicts.append((cell, Status.UNKNOWN))

          self.last_query_count = queries
          return Analysis(consistent=True, verdicts=tuple(verdicts))

     def _fallback_reference(self, state: PublicState) -> Analysis:
          """Cơ chế dự phòng sang bộ phân tích tham chiếu"""
          from griductive.engine.reference import ReferenceAnalyzer
          return ReferenceAnalyzer(timeout=self.timeout_seconds).analyze(state)