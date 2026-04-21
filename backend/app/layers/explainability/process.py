import json
import os
import re
from typing import Any, Dict, List, Optional

from google import genai
import pandas as pd
from dotenv import load_dotenv

from app.domain.data import ExplainabilityEvidence, ForecastMetric
from app.domain.ontology import ForecastOntology

load_dotenv()


class StandardExplainer:
    """
    Generates natural language explanations using deterministic templates.
    """

    def explain(
        self,
        history_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        ontology: ForecastOntology,
        metrics: List[ForecastMetric],
    ) -> str:
        """
        Generates a simple natural language summary of the forecast including
        performance insights.
        """
        target_col = next(c.column_name for c in ontology.columns if c.role == "target")

        last_hist_val = float(history_df[target_col].iloc[-1])

        # New forecast format uses 'mean' column
        # Fallback to target_col for backward compatibility
        if "mean" in forecast_df.columns:
            last_pred_val = float(forecast_df["mean"].iloc[-1])
        else:
            last_pred_val = float(forecast_df[target_col].iloc[-1])

        horizon = len(forecast_df)

        trend = "increase" if last_pred_val > last_hist_val else "decrease"
        if last_hist_val == 0:
            pct_change = 0.0
        else:
            pct_change = ((last_pred_val - last_hist_val) / last_hist_val) * 100

        # Extract MAE for reliability mention
        mae = next((m.value for m in metrics if m.name == "MAE"), 0.0)
        reliability = "high" if mae < (abs(last_hist_val) * 0.1) else "moderate"

        explanation = (
            f"Based on the historical data, the system forecasts a {trend} in "
            f"{target_col} over the next {horizon} periods.\n"
            f"The value is expected to move from {last_hist_val:.2f} to "
            f"{last_pred_val:.2f}, representing a {pct_change:.1f}% change.\n\n"
            f"The model indicates {reliability} reliability based on validation "
            f"testing. The primary patterns identified were projected forward "
            f"using deterministic statistical methods."
        )

        return explanation.strip()


class ForecastExplainabilityService:
    """Grounded explainability for initial briefing and user Q&A."""

    def _model_name(self) -> str:
        return "gemini-2.5-flash"

    def _has_llm(self) -> bool:
        api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        return bool(api_key and "PLACEHOLDER" not in api_key)

    def _safe_float(self, value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _sanitize_user_text(self, text: str) -> str:
        cleaned = text.replace("**", "")
        cleaned = cleaned.replace("`", "")
        cleaned = re.sub(r"^\s*[-*]\s+", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _reliability_label(self, skill: Optional[float], mape: Optional[float]) -> str:
        if skill is not None:
            if skill >= 0.6:
                return "strong"
            if skill >= 0.3:
                return "moderate"
            return "limited"

        if mape is not None:
            if mape <= 10:
                return "strong"
            if mape <= 20:
                return "moderate"
            return "limited"

        return "unknown"

    def _series_mean(self, values: List[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _extract_forecast_series(self, forecast_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        points: List[Dict[str, Any]] = []
        y_values: List[float] = []
        lowers: List[float] = []
        uppers: List[float] = []

        for idx, row in enumerate(forecast_results):
            y = self._safe_float(row.get("mean") or row.get("median_forecast") or row.get("value"))
            low = self._safe_float(row.get("conf_80_lower") or row.get("lower"))
            up = self._safe_float(row.get("conf_80_upper") or row.get("upper"))

            if y is None:
                continue

            y_values.append(y)
            if low is not None:
                lowers.append(low)
            if up is not None:
                uppers.append(up)

            points.append(
                {
                    "index": idx,
                    "date": row.get("date") or row.get("year") or row.get("ds"),
                    "y": y,
                    "lower": low,
                    "upper": up,
                }
            )

        diffs = [y_values[i + 1] - y_values[i] for i in range(len(y_values) - 1)]
        sign_changes = 0
        for i in range(len(diffs) - 1):
            a = diffs[i]
            b = diffs[i + 1]
            if a == 0 or b == 0:
                continue
            if (a > 0 > b) or (a < 0 < b):
                sign_changes += 1

        start = y_values[0] if y_values else 0.0
        end = y_values[-1] if y_values else 0.0
        span = (max(y_values) - min(y_values)) if y_values else 0.0
        baseline = max(abs(self._series_mean(y_values)), 1e-9)
        span_pct = (span / baseline) * 100
        endpoint_pct = ((end - start) / max(abs(start), 1e-9)) * 100 if y_values else 0.0

        avg_width = None
        if lowers and uppers and len(lowers) == len(uppers):
            widths = [max(0.0, uppers[i] - lowers[i]) for i in range(len(lowers))]
            avg_width = self._series_mean(widths)

        return {
            "points": points,
            "values": y_values,
            "start": start,
            "end": end,
            "span": span,
            "span_pct": span_pct,
            "endpoint_pct": endpoint_pct,
            "sign_changes": sign_changes,
            "avg_interval_width": avg_width,
            "count": len(y_values),
        }

    def _describe_shape(self, series: Dict[str, Any]) -> str:
        if series["count"] < 2:
            return "insufficient points to assess shape"

        span_pct = series["span_pct"]
        sign_changes = series["sign_changes"]
        endpoint_pct = series["endpoint_pct"]

        if span_pct < 1.0:
            return "mostly flat"
        if sign_changes >= 2:
            return "oscillatory with multiple turning points"
        if endpoint_pct >= 1.0:
            return "upward-leaning"
        if endpoint_pct <= -1.0:
            return "downward-leaning"
        return "range-bound"

    def _metric_lookup(self, metrics: List[Dict[str, Any]], metric_name: str) -> Optional[float]:
        target = metric_name.lower()
        for metric in metrics:
            name = str(metric.get("name", "")).lower()
            if name == target:
                return self._safe_float(metric.get("value"))
        return None

    def _compute_forecast_skill_score(self, ctx: Dict[str, Any]) -> Optional[float]:
        health = ctx.get("data_health_report") or {}
        mse_naive = self._safe_float(health.get("mse_naive"))
        mse_winner = self._safe_float(health.get("mse_winner"))
        if mse_naive is None or mse_winner is None or mse_naive == 0:
            return None
        # Skill score: 1 - (model_error / baseline_error)
        return 1.0 - (mse_winner / mse_naive)

    def _build_context(self, session: Any) -> Dict[str, Any]:
        ontology = session.ontology or {}
        metrics = session.metrics or []
        forecast_results = session.forecast_results or []
        cleaning_report = session.cleaning_report or {}
        model_metadata = ontology.get("model_metadata") or {}
        persisted_artifacts = ontology.get("_artifacts", {}) if isinstance(ontology, dict) else {}
        data_health_report = persisted_artifacts.get("data_health_report") or {}

        series = self._extract_forecast_series(forecast_results)

        target_name = "target"
        for col in ontology.get("columns", []):
            if col.get("role") == "target":
                target_name = col.get("display_name") or col.get("column_name") or "target"
                break

        mae = self._metric_lookup(metrics, "MAE")
        mape = self._metric_lookup(metrics, "MAPE")

        granularity = (((ontology.get("problem") or {}).get("granularity") or {}).get("unit"))
        horizon = ((((ontology.get("requirements") or {}).get("horizon_requirement") or {}).get("steps")))

        return {
            "session_id": session.session_id,
            "target_name": target_name,
            "ontology": ontology,
            "metrics": metrics,
            "forecast_results": forecast_results,
            "cleaning_report": cleaning_report,
            "model_metadata": model_metadata,
            "series": series,
            "granularity": granularity,
            "horizon": horizon,
            "mae": mae,
            "mape": mape,
            "data_health_report": data_health_report,
            "forecast_skill_score": self._compute_forecast_skill_score({"data_health_report": data_health_report}),
            "stored_explanation": session.explanation or "",
        }

    def _tool_list(self) -> Dict[str, str]:
        return {
            "get_session_overview": "Returns top-level session summary including target, horizon, granularity, and model metadata.",
            "get_metric": "Returns value for a named metric such as MAE, MAPE, RMSE.",
            "list_metrics": "Lists all available metrics.",
            "get_ontology_path": "Returns any ontology subsection by dot-path, e.g. 'problem.granularity' or 'requirements'.",
            "list_columns": "Lists columns with role/type/covariate info. Optional filter by role.",
            "get_forecast_diagnostics": "Returns deterministic forecast diagnostics including shape, range, endpoint change, and interval width.",
            "get_forecast_points": "Returns first N forecast points with interval bounds.",
            "get_cleaning_summary": "Returns cleaning summary and action count.",
            "get_model_metadata": "Returns selected model metadata.",
            "get_forecast_skill_score": "Returns forecast skill score if baseline and winner MSE are available.",
        }

    def _tool_call(self, tool_name: str, args: Dict[str, Any], ctx: Dict[str, Any]) -> Any:
        if tool_name == "get_session_overview":
            return {
                "target": ctx.get("target_name"),
                "horizon": ctx.get("horizon"),
                "granularity": ctx.get("granularity"),
                "model": ctx.get("model_metadata", {}),
            }

        if tool_name == "get_metric":
            metric_name = str(args.get("name", "")).strip()
            return {
                "name": metric_name,
                "value": self._metric_lookup(ctx.get("metrics", []), metric_name),
            }

        if tool_name == "list_metrics":
            return ctx.get("metrics", [])

        if tool_name == "get_ontology_path":
            path = str(args.get("path", "")).strip()
            node: Any = ctx.get("ontology", {})
            if not path:
                return node
            for key in path.split("."):
                if isinstance(node, dict) and key in node:
                    node = node[key]
                else:
                    return {"error": f"ontology path not found: {path}"}
            return node

        if tool_name == "list_columns":
            role_filter = str(args.get("role", "")).strip().lower()
            cols = ctx.get("ontology", {}).get("columns", [])
            if role_filter:
                cols = [c for c in cols if str(c.get("role", "")).lower() == role_filter]
            return cols

        if tool_name == "get_forecast_diagnostics":
            series = ctx.get("series", {})
            return {
                "shape": self._describe_shape(series),
                "point_count": series.get("count", 0),
                "start": series.get("start"),
                "end": series.get("end"),
                "endpoint_pct": series.get("endpoint_pct"),
                "span": series.get("span"),
                "span_pct": series.get("span_pct"),
                "turning_points": series.get("sign_changes"),
                "avg_interval_width": series.get("avg_interval_width"),
            }

        if tool_name == "get_forecast_points":
            n = int(args.get("n", 5)) if str(args.get("n", "")).strip() else 5
            n = max(1, min(n, 30))
            return ctx.get("series", {}).get("points", [])[:n]

        if tool_name == "get_cleaning_summary":
            report = ctx.get("cleaning_report", {})
            actions = report.get("actions", []) if isinstance(report, dict) else []
            summary = report.get("summary") if isinstance(report, dict) else None
            return {"summary": summary, "action_count": len(actions), "actions": actions[:6]}

        if tool_name == "get_model_metadata":
            return ctx.get("model_metadata", {})

        if tool_name == "get_forecast_skill_score":
            score = ctx.get("forecast_skill_score")
            if score is None:
                return {"value": None, "status": "unavailable", "reason": "Baseline and winner MSE were not available in session artifacts."}
            return {"value": score, "status": "ok"}

        return {"error": f"unknown tool: {tool_name}"}

    def _tool_trace_to_evidence(self, tool_trace: List[Dict[str, Any]]) -> List[ExplainabilityEvidence]:
        evidence: List[ExplainabilityEvidence] = []
        for call in tool_trace:
            tool_name = call.get("tool", "unknown_tool")
            output = call.get("output")
            detail = str(output)
            if len(detail) > 220:
                detail = detail[:220] + "..."
            evidence.append(ExplainabilityEvidence(source=f"tool:{tool_name}", detail=detail))
        return evidence

    def _run_rule_based_tool_plan(self, question: str) -> List[Dict[str, Any]]:
        q = question.lower()
        calls: List[Dict[str, Any]] = [{"tool": "get_session_overview", "args": {}}]

        if any(k in q for k in ["reliab", "error", "mape", "mae", "rmse", "accuracy"]):
            calls.append({"tool": "list_metrics", "args": {}})
            calls.append({"tool": "get_forecast_skill_score", "args": {}})

        if any(k in q for k in ["forecast", "trend", "shape", "flat", "up", "down", "interval"]):
            calls.append({"tool": "get_forecast_diagnostics", "args": {}})
            calls.append({"tool": "get_forecast_points", "args": {"n": 8}})

        if any(k in q for k in ["ontology", "column", "role", "covariate", "granularity", "horizon"]):
            calls.append({"tool": "list_columns", "args": {}})
            calls.append({"tool": "get_ontology_path", "args": {"path": "problem.granularity"}})
            calls.append({"tool": "get_ontology_path", "args": {"path": "requirements"}})

        if any(k in q for k in ["model", "why"]):
            calls.append({"tool": "get_model_metadata", "args": {}})

        if "clean" in q:
            calls.append({"tool": "get_cleaning_summary", "args": {}})

        return calls[:8]

    def _llm_generate_tool_plan(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]],
        available_tools: Dict[str, str],
    ) -> Optional[List[Dict[str, Any]]]:
        if not self._has_llm():
            return None

        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            history_block = ""
            if history:
                turns = history[-8:]
                history_block = "\n".join(
                    [f"{turn.get('role', 'user')}: {turn.get('content', '')}" for turn in turns]
                )

            prompt = (
                "You are planning tool calls for a forecasting explainability assistant. "
                "Return JSON only with schema: {\"tool_calls\":[{\"tool\":\"name\",\"args\":{}}]}. "
                "Choose only from the provided tools and keep to max 6 calls.\n\n"
                f"Available Tools:\n{json.dumps(available_tools, indent=2)}\n\n"
                f"Recent Chat:\n{history_block}\n\n"
                f"User Question:\n{question}"
            )

            response = client.models.generate_content(
                model=self._model_name(),
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            payload = json.loads((response.text or "{}").strip())
            tool_calls = payload.get("tool_calls", [])
            if not isinstance(tool_calls, list):
                return None

            cleaned_calls: List[Dict[str, Any]] = []
            for call in tool_calls[:6]:
                if not isinstance(call, dict):
                    continue
                name = str(call.get("tool", "")).strip()
                args = call.get("args", {})
                if name in available_tools and isinstance(args, dict):
                    cleaned_calls.append({"tool": name, "args": args})

            return cleaned_calls or None
        except (RuntimeError, ValueError, TypeError, OSError, TimeoutError, ConnectionError, json.JSONDecodeError):
            return None

    def _synthesize_with_llm(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]],
        tool_trace: List[Dict[str, Any]],
    ) -> Optional[str]:
        if not self._has_llm():
            return None

        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            history_block = ""
            if history:
                turns = history[-8:]
                history_block = "\n".join(
                    [f"{turn.get('role', 'user')}: {turn.get('content', '')}" for turn in turns]
                )

            prompt = (
                "You are an explainability copilot for forecasting. "
                "Answer ONLY from tool outputs below. If something is missing, explicitly say it is unavailable. "
                "Use plain language for non-technical project managers. "
                "Do not use markdown formatting and never use double asterisks. "
                "Do not mention tool names, tool calls, JSON, MAE, RMSE, MAPE, or internal diagnostics terms directly. "
                "Translate technical signals into simple confidence statements. "
                "Keep response concise and practical.\n\n"
                f"Recent Chat:\n{history_block}\n\n"
                f"User Question:\n{question}\n\n"
                f"Tool Outputs:\n{json.dumps(tool_trace, indent=2)}"
            )
            response = client.models.generate_content(model=self._model_name(), contents=prompt)
            answer = (response.text or "").strip()
            if not answer:
                return None
            return self._sanitize_user_text(answer)
        except (RuntimeError, ValueError, TypeError, OSError, TimeoutError, ConnectionError):
            return None

    def _deterministic_answer_from_tools(self, question: str, tool_trace: List[Dict[str, Any]]) -> str:
        if not tool_trace:
            return "I do not have enough grounded session artifacts to answer this question yet."

        q = question.lower()
        overview = next((t.get("output") for t in tool_trace if t.get("tool") == "get_session_overview"), {})
        if not isinstance(overview, dict):
            overview = {}
        diagnostics = next((t.get("output") for t in tool_trace if t.get("tool") == "get_forecast_diagnostics"), None)
        metrics = next((t.get("output") for t in tool_trace if t.get("tool") == "list_metrics"), None)
        skill = next((t.get("output") for t in tool_trace if t.get("tool") == "get_forecast_skill_score"), None)
        model = next((t.get("output") for t in tool_trace if t.get("tool") == "get_model_metadata"), None)

        if "model" in q or "why" in q:
            if isinstance(model, dict) and model:
                return (
                    f"The chosen model is {model.get('name', 'our selected model')}. "
                    f"It was selected because {model.get('rationale', 'it performed best for this dataset and forecast horizon')}."
                )
            return "I do not have model-selection details for this run yet."

        if any(k in q for k in ["reliab", "error", "mape", "mae", "accuracy", "skill"]):
            reliability = "unknown"
            if isinstance(skill, dict):
                if skill.get("status") == "ok":
                    reliability = self._reliability_label(skill=skill.get("value"), mape=None)
            elif isinstance(metrics, list):
                mape_val = next((self._safe_float(m.get("value")) for m in metrics if str(m.get("name", "")).upper() == "MAPE"), None)
                reliability = self._reliability_label(skill=None, mape=mape_val)

            if reliability == "unknown":
                return "I cannot give a reliable confidence rating yet because quality signals are missing for this run."
            return (
                f"Confidence level is {reliability}. "
                "In simple terms, this means the forecast is "
                f"{ 'more dependable for planning' if reliability == 'strong' else ('usable with some caution' if reliability == 'moderate' else 'best treated as directional guidance rather than a firm commitment') }."
            )

        if diagnostics:
            direction = "stable"
            endpoint = self._safe_float(diagnostics.get("endpoint_pct"))
            if endpoint is not None:
                if endpoint > 1:
                    direction = "upward"
                elif endpoint < -1:
                    direction = "downward"

            return (
                f"The outlook is {direction} overall and currently looks {diagnostics.get('shape', 'mixed')}. "
                "Expect some movement over the forecast period, so this should be used as a planning guide rather than an exact day-by-day promise."
            )

        return (
            f"This forecast covers {overview.get('target', 'the target metric')} for the next "
            f"{overview.get('horizon', 'planned')} {overview.get('granularity', 'periods')}."
        )

    def generate_initial_briefing(self, session: Any) -> str:
        ctx = self._build_context(session)
        model_name = ctx["model_metadata"].get("name", "Selected model")
        rationale = ctx["model_metadata"].get("rationale", "chosen from tournament performance")
        horizon = ctx.get("horizon") or len(ctx.get("forecast_results") or [])
        granularity = ctx.get("granularity") or "periods"
        series = ctx.get("series", {})
        shape = self._describe_shape(series)
        endpoint_pct = series.get("endpoint_pct", 0.0)
        avg_interval_width = series.get("avg_interval_width")

        mape = ctx.get("mape")
        skill = ctx.get("forecast_skill_score")

        reliability = self._reliability_label(skill=skill, mape=mape)

        uncertainty_text = (
            "Uncertainty appears contained for most of the horizon."
            if avg_interval_width is not None
            else "Uncertainty details are limited in this run, so use extra caution."
        )

        briefing = (
            f"Forecast briefing for {ctx['target_name']} over {horizon} {granularity}. "
            f"Overall direction looks {('upward' if endpoint_pct > 1 else 'downward' if endpoint_pct < -1 else 'mostly stable')}, "
            f"with a pattern that appears {shape}. "
            f"Confidence level is {reliability}. "
            f"{uncertainty_text} "
            f"Active model: {model_name} ({rationale}).\n\n"
            "You can ask me plain-language questions about what this means for planning, risk, assumptions, and next steps."
        )
        return self._sanitize_user_text(briefing)

    def answer_question(
        self,
        question: str,
        session: Any,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        ctx = self._build_context(session)
        tools = self._tool_list()
        suggestions = [
            "Why was this model selected?",
            "How much should I trust this forecast for planning?",
            "What assumptions could change this outcome?",
        ]

        llm_plan = self._llm_generate_tool_plan(question=question, history=history, available_tools=tools)
        planned_calls = llm_plan or self._run_rule_based_tool_plan(question=question)

        tool_trace: List[Dict[str, Any]] = []
        for call in planned_calls:
            tool_name = call.get("tool", "")
            args = call.get("args", {})
            output = self._tool_call(tool_name=tool_name, args=args, ctx=ctx)
            tool_trace.append({"tool": tool_name, "args": args, "output": output})

        llm_answer = self._synthesize_with_llm(
            question=question,
            history=history,
            tool_trace=tool_trace,
        )
        if llm_answer:
            return {
                "answer": self._sanitize_user_text(llm_answer),
                "evidence": [],
                "suggestions": suggestions,
            }

        return {
            "answer": self._sanitize_user_text(self._deterministic_answer_from_tools(question=question, tool_trace=tool_trace)),
            "evidence": [],
            "suggestions": suggestions,
        }
