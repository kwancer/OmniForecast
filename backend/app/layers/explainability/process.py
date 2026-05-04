import json
import os
import re
from typing import Any, Dict, Generator, List, Optional, Tuple

from pydantic import BaseModel, Field
from google import genai
import pandas as pd
from dotenv import load_dotenv

from app.domain.data import ExplainabilityEvidence, ForecastMetric
from app.domain.ontology import ForecastOntology

load_dotenv()


class ToolArg(BaseModel):
    name: str = Field(description="Name of the parameter")
    value: str = Field(description="Value of the parameter as a string")


class ToolCall(BaseModel):
    tool: str = Field(description="Name of the tool to call")
    args: List[ToolArg] = Field(default_factory=list, description="Arguments for the tool")


class ToolCallPlan(BaseModel):
    tool_calls: List[ToolCall] = Field(description="List of tool calls to execute")


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
        return "gemini-3-flash-preview"

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

    def _extract_forecast_series(
        self, forecast_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        points: List[Dict[str, Any]] = []
        y_values: List[float] = []
        lowers: List[float] = []
        uppers: List[float] = []

        for idx, row in enumerate(forecast_results):
            y = self._safe_float(
                row.get("mean") or row.get("median_forecast") or row.get("value")
            )
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
        endpoint_pct = (
            ((end - start) / max(abs(start), 1e-9)) * 100 if y_values else 0.0
        )

        avg_width = None
        if lowers and uppers and len(lowers) == len(uppers):
            widths = [max(0.0, uppers[i] - lowers[i]) for i in range(len(lowers))]
            avg_width = self._series_mean(widths)

        return {
            "points": points,
            "values": y_values,
            "lowers": lowers,
            "uppers": uppers,
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

    def _metric_lookup(
        self, metrics: List[Dict[str, Any]], metric_name: str
    ) -> Optional[float]:
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
        persisted_artifacts = (
            ontology.get("_artifacts", {}) if isinstance(ontology, dict) else {}
        )
        data_health_report = persisted_artifacts.get("data_health_report") or {}

        series = self._extract_forecast_series(forecast_results)

        target_name = "target"
        for col in ontology.get("columns", []):
            if col.get("role") == "target":
                target_name = (
                    col.get("display_name") or col.get("column_name") or "target"
                )
                break

        mae = self._metric_lookup(metrics, "MAE")
        mape = self._metric_lookup(metrics, "MAPE")

        granularity = ((ontology.get("problem") or {}).get("granularity") or {}).get(
            "unit"
        )
        horizon = (
            (ontology.get("requirements") or {}).get("horizon_requirement") or {}
        ).get("steps")

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
            "rmse": self._metric_lookup(metrics, "RMSE"),
            "r2": self._metric_lookup(metrics, "R²"),
            "data_health_report": data_health_report,
            "forecast_skill_score": self._compute_forecast_skill_score(
                {"data_health_report": data_health_report}
            ),
            "stored_explanation": session.explanation or "",
            "tournament_results": persisted_artifacts.get("tournament_results") or [],
            "backtest_data": persisted_artifacts.get("backtest_data") or [],
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
            "get_tournament_results": "Returns all models tested in the tournament with their MAE, status (winner/runner_up/rejected), and complexity.",
        }

    def _tool_call(
        self, tool_name: str, args: Dict[str, Any], ctx: Dict[str, Any]
    ) -> Any:
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
                cols = [
                    c for c in cols if str(c.get("role", "")).lower() == role_filter
                ]
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
            n = int(args.get("n", 1000)) if str(args.get("n", "")).strip() else 1000
            n = max(1, min(n, 1000))
            return ctx.get("series", {}).get("points", [])[:n]

        if tool_name == "get_cleaning_summary":
            report = ctx.get("cleaning_report", {})
            actions = report.get("actions", []) if isinstance(report, dict) else []
            summary = report.get("summary") if isinstance(report, dict) else None
            return {
                "summary": summary,
                "action_count": len(actions),
                "actions": actions[:6],
            }

        if tool_name == "get_model_metadata":
            return ctx.get("model_metadata", {})

        if tool_name == "get_forecast_skill_score":
            score = ctx.get("forecast_skill_score")
            if score is None:
                return {
                    "value": None,
                    "status": "unavailable",
                    "reason": "Baseline and winner MSE were not available in session artifacts.",
                }
            return {"value": score, "status": "ok"}

        if tool_name == "get_tournament_results":
            return ctx.get("tournament_results", [])

        return {"error": f"unknown tool: {tool_name}"}

    _TOOL_LABELS = {
        "get_session_overview": "Session Overview",
        "get_metric": "Performance Metric",
        "list_metrics": "All Metrics",
        "get_ontology_path": "Ontology Config",
        "list_columns": "Column Roles",
        "get_forecast_diagnostics": "Forecast Diagnostics",
        "get_forecast_points": "Forecast Data Points",
        "get_cleaning_summary": "Data Cleaning",
        "get_model_metadata": "Model Selection",
        "get_forecast_skill_score": "Skill Score",
        "get_tournament_results": "Model Tournament",
    }

    def _tool_trace_to_evidence(
        self, tool_trace: List[Dict[str, Any]]
    ) -> List[ExplainabilityEvidence]:
        evidence: List[ExplainabilityEvidence] = []
        for call in tool_trace:
            tool_name = call.get("tool", "unknown_tool")
            label = self._TOOL_LABELS.get(tool_name, tool_name)
            output = call.get("output")
            if isinstance(output, dict) and output.get("error"):
                continue
            detail = (
                json.dumps(output, default=str)
                if not isinstance(output, str)
                else output
            )
            if len(detail) > 300:
                detail = detail[:300] + "…"
            evidence.append(ExplainabilityEvidence(source=label, detail=detail))
        return evidence

    def _build_fact_sheet(
        self, ctx: Dict[str, Any], tool_trace: List[Dict[str, Any]]
    ) -> str:
        """Convert tool outputs + context into a structured, human-readable fact sheet."""
        lines: List[str] = ["FORECAST FACT SHEET", "─" * 40]

        lines.append(f"Target Variable: {ctx.get('target_name', 'unknown')}")
        if ctx.get("horizon"):
            lines.append(
                f"Forecast Horizon: {ctx['horizon']} {ctx.get('granularity', 'periods')}"
            )

        model = ctx.get("model_metadata", {})
        if model:
            lines.append(
                f"Active Model: {model.get('name', 'Unknown')} — {model.get('rationale', 'selected by tournament')}"
            )
            if model.get("description"):
                lines.append(f"Model Type: {model['description']}")

        # ── Forecast shape & direction ──
        series = ctx.get("series", {})
        values = series.get("values", [])
        if series.get("count", 0) > 1:
            shape = self._describe_shape(series)
            ep = series.get("endpoint_pct", 0)
            direction = "upward" if ep > 1 else ("downward" if ep < -1 else "stable")
            lines.append(f"Overall Direction: {direction} ({ep:+.1f}% endpoint change)")
            lines.append(f"Pattern Shape: {shape}")
            lines.append(
                f"Forecast Range: {series.get('start', 0):.2f} → {series.get('end', 0):.2f}"
            )
            if values:
                lines.append(f"Forecast Min Value: {min(values):.2f}")
                lines.append(f"Forecast Max Value: {max(values):.2f}")
                lines.append(f"Forecast Mean Value: {self._series_mean(values):.2f}")

        # ── Prediction intervals ──
        lowers = series.get("lowers", [])
        uppers = series.get("uppers", [])
        if series.get("avg_interval_width") is not None:
            lines.append(
                f"Avg Prediction Band Width: ±{series['avg_interval_width']:.2f}"
            )
        if lowers and uppers:
            lines.append(
                f"Tightest Interval: ±{min(max(0, uppers[i] - lowers[i]) for i in range(min(len(lowers), len(uppers)))):.2f}"
            )
            lines.append(
                f"Widest Interval: ±{max(max(0, uppers[i] - lowers[i]) for i in range(min(len(lowers), len(uppers)))):.2f}"
            )

        # ── Reliability metrics ──
        skill = ctx.get("forecast_skill_score")
        mape = ctx.get("mape")
        mae = ctx.get("mae")
        rmse = ctx.get("rmse")
        r2 = ctx.get("r2")
        reliability = self._reliability_label(skill=skill, mape=mape)
        lines.append(f"Reliability Rating: {reliability}")
        if skill is not None:
            lines.append(
                f"Skill Score: {skill:.2f} (1.0 = perfect, 0.0 = no better than naive)"
            )
        if mape is not None:
            lines.append(f"MAPE: {mape:.1f}% (average percentage error)")
        if mae is not None:
            lines.append(f"MAE: {mae:.2f} (average absolute error in target units)")
        if rmse is not None:
            lines.append(f"RMSE: {rmse:.2f} (root mean squared error)")
        if r2 is not None:
            lines.append(
                f"R²: {r2:.3f} (coefficient of determination, 1.0 = perfect fit)"
            )

        # ── Data health ──
        health = ctx.get("data_health_report", {})
        if isinstance(health, dict) and health:
            score = self._safe_float(health.get("score"))
            if score is not None:
                lines.append(
                    f"Data Health Score: {score:.0f}/100 ({health.get('rating', 'unknown')})"
                )
            if health.get("explanation"):
                lines.append(f"Data Health Note: {health['explanation']}")

        # ── Tournament results ──
        tournament = ctx.get("tournament_results", [])
        if tournament:
            lines.append(f"Model Tournament: {len(tournament)} model(s) evaluated")
            for tr in tournament:
                if isinstance(tr, dict):
                    status = tr.get("status", "unknown").upper()
                    name = tr.get("model_name", "?")
                    tr_mae = self._safe_float(tr.get("mae"))
                    complexity = self._safe_float(tr.get("complexity"))
                    entry = (
                        f"  {'🏆' if status == 'WINNER' else '  '} {name} — MAE: {tr_mae:.2f}"
                        if tr_mae is not None
                        else f"  {name}"
                    )
                    if complexity is not None:
                        entry += f", complexity: {complexity:.1f}"
                    entry += f" [{status}]"
                    lines.append(entry)

        # ── Cleaning ──
        cleaning = ctx.get("cleaning_report", {})
        if isinstance(cleaning, dict):
            actions = cleaning.get("actions", [])
            if actions:
                lines.append(f"Data Cleaning: {len(actions)} action(s)")
                for a in actions[:4]:
                    if isinstance(a, dict):
                        lines.append(
                            f"  • {a.get('column', '?')}: {a.get('description', a.get('action', ''))}"
                        )

        # ── Forecast Data Points ──
        points = ctx.get("series", {}).get("points", [])
        if points:
            limit = 1000
            display_points = points[:limit]
            lines.append(f"Forecast Data Points (first {len(display_points)}):")
            for pt in display_points:
                if isinstance(pt, dict):
                    date = pt.get("date", f"t+{pt.get('index', '?')}")
                    y = pt.get("y")
                    lo, hi = pt.get("lower"), pt.get("upper")
                    s = f"  {date}: {y:.2f}" if y is not None else f"  {date}: N/A"
                    if lo is not None and hi is not None:
                        s += f" [{lo:.2f} – {hi:.2f}]"
                    lines.append(s)

        return "\n".join(lines)

    _SYNTHESIS_SYSTEM = (
        "You are a helpful forecast analyst embedded in a forecasting dashboard. "
        "The user can already see the chart, metrics, model name, and data health score on screen "
        "— DO NOT repeat those numbers back to them. Instead, help them INTERPRET what they see.\n\n"
        "Your job is to:\n"
        "- Explain what the forecast means in practical, real-world terms\n"
        "- Flag anything surprising, risky, or worth paying attention to\n"
        "- Help them decide whether to trust the forecast and how to act on it\n"
        "- Translate technical concepts into everyday language (no jargon without explanation)\n\n"
        "CRITICAL — metric skepticism:\n"
        "- MAPE can be MISLEADINGLY low for targets with large absolute values (e.g. GDP, revenue). "
        "A 0.1% MAPE on a billion-dollar figure still means the error is hundreds of millions. "
        "ALWAYS contextualise MAPE by mentioning what the MAE means in real-world units. "
        "If MAPE looks suspiciously perfect (< 1%), flag that it may be deceptive and explain why.\n"
        "- The **Forecast Skill Score** is the most honest reliability indicator — it measures how much "
        "better the model is versus a naive baseline (just repeating the last value). "
        "A score of 0.0 means the model is no better than guessing. A score of 0.7+ is genuinely strong. "
        "Always mention the skill score when discussing reliability or trust.\n"
        "- If the winning model is a Naive Baseline, be upfront that the data may lack predictable patterns.\n\n"
        "Writing rules:\n"
        "- Never open with greetings (no 'Good morning', 'Hello', 'Hi there')\n"
        "- Never just list facts the user can see on screen — add insight they can't get from the chart alone\n"
        "- Write like you're talking to a smart colleague who isn't a data scientist\n"
        "- Use **bold** sparingly for genuinely key insights\n"
        "- Keep it short: 2-4 sentences for simple questions, up to a short paragraph for complex ones\n"
        "- Be honest about limitations — if the model struggled, say so plainly\n"
        "- Use the fact sheet for grounding but focus on the 'so what?' not the raw numbers"
    )

    def _generate_dynamic_suggestions(
        self, ctx: Dict[str, Any], history: Optional[List[Dict[str, str]]] = None
    ) -> List[str]:
        asked = set()
        if history:
            for t in history:
                if t.get("role") == "user":
                    asked.add(t.get("content", "").strip().lower())

        pool: List[str] = []
        series = ctx.get("series", {})
        skill = ctx.get("forecast_skill_score")
        mape = ctx.get("mape")
        cleaning = ctx.get("cleaning_report", {})
        ep = series.get("endpoint_pct", 0)

        if series.get("sign_changes", 0) >= 2:
            pool.append("Why does the forecast oscillate?")
        if abs(ep) > 10:
            d = "upward" if ep > 0 else "downward"
            pool.append(f"What's driving the {d} trend?")
        if skill is not None and skill < 0.3:
            pool.append("Why is model performance limited?")
        if mape is not None and mape > 15:
            pool.append("What's causing the high error rate?")
        if isinstance(cleaning, dict) and cleaning.get("actions"):
            pool.append("What data cleaning was applied?")
        if series.get("avg_interval_width") is not None:
            pool.append("How wide are the prediction intervals?")

        pool.extend(
            [
                "Why was this model selected?",
                "How reliable is this forecast for planning?",
                "What assumptions could change this outcome?",
                "What are the key risks in this forecast?",
            ]
        )

        seen: set = set()
        result: List[str] = []
        for s in pool:
            key = s.strip().lower()
            if key not in asked and key not in seen:
                seen.add(key)
                result.append(s)
            if len(result) >= 3:
                break
        return result or pool[:3]

    def _run_rule_based_tool_plan(self, question: str) -> List[Dict[str, Any]]:
        q = question.lower()
        calls: List[Dict[str, Any]] = [{"tool": "get_session_overview", "args": {}}]

        if any(k in q for k in ["reliab", "error", "mape", "mae", "rmse", "accuracy"]):
            calls.append({"tool": "list_metrics", "args": {}})
            calls.append({"tool": "get_forecast_skill_score", "args": {}})

        if any(
            k in q
            for k in ["forecast", "trend", "shape", "flat", "up", "down", "interval"]
        ):
            calls.append({"tool": "get_forecast_diagnostics", "args": {}})
            calls.append({"tool": "get_forecast_points", "args": {"n": 1000}})

        if any(
            k in q
            for k in [
                "ontology",
                "column",
                "role",
                "covariate",
                "granularity",
                "horizon",
            ]
        ):
            calls.append({"tool": "list_columns", "args": {}})
            calls.append(
                {"tool": "get_ontology_path", "args": {"path": "problem.granularity"}}
            )
            calls.append(
                {"tool": "get_ontology_path", "args": {"path": "requirements"}}
            )

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
                    [
                        f"{turn.get('role', 'user')}: {turn.get('content', '')}"
                        for turn in turns
                    ]
                )

            prompt = (
                "You are planning tool calls for a forecasting explainability assistant. "
                'Return JSON only with schema: {"tool_calls":[{"tool":"name","args":{}}]}. '
                "Choose only from the provided tools and keep to max 6 calls.\n\n"
                f"Available Tools:\n{json.dumps(available_tools, indent=2)}\n\n"
                f"Recent Chat:\n{history_block}\n\n"
                f"User Question:\n{question}"
            )

            response = client.models.generate_content(
                model=self._model_name(),
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ToolCallPlan,
                },
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
                # Convert List[ToolArg] back to Dict[str, Any]
                args_list = call.get("args", [])
                args_dict = {}
                if isinstance(args_list, list):
                    for arg in args_list:
                        if isinstance(arg, dict) and "name" in arg:
                            args_dict[arg["name"]] = arg.get("value")
                
                if name in available_tools:
                    cleaned_calls.append({"tool": name, "args": args_dict})

            return cleaned_calls or None
        except (
            RuntimeError,
            ValueError,
            TypeError,
            OSError,
            TimeoutError,
            ConnectionError,
            json.JSONDecodeError,
        ):
            return None

    def _build_synthesis_prompt(
        self,
        question: str,
        fact_sheet: str,
        history: Optional[List[Dict[str, str]]],
    ) -> str:
        history_block = ""
        if history:
            turns = history[-8:]
            history_block = (
                "Conversation so far:\n"
                + "\n".join(
                    [f"{t.get('role', 'user')}: {t.get('content', '')}" for t in turns]
                )
                + "\n\n"
            )

        return (
            f"{self._SYNTHESIS_SYSTEM}\n\n"
            f"{history_block}"
            f"Fact Sheet:\n{fact_sheet}\n\n"
            f"User Question: {question}"
        )

    def _synthesize_with_llm(
        self,
        question: str,
        history: Optional[List[Dict[str, str]]],
        tool_trace: List[Dict[str, Any]],
        ctx: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not self._has_llm():
            return None

        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            fact_sheet = self._build_fact_sheet(ctx, tool_trace)
            prompt = self._build_synthesis_prompt(question, fact_sheet, history)

            response = client.models.generate_content(
                model=self._model_name(), contents=prompt
            )
            answer = (response.text or "").strip()
            if not answer:
                return None

            return {
                "answer": answer,
                "suggestions": self._generate_dynamic_suggestions(ctx, history),
            }
        except (
            RuntimeError,
            ValueError,
            TypeError,
            OSError,
            TimeoutError,
            ConnectionError,
        ):
            return None

    def synthesize_stream(
        self,
        question: str,
        session: Any,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Generator[Tuple[str, Any], None, None]:
        """Stream synthesis tokens. Yields (type, payload) tuples."""
        ctx = self._build_context(session)
        tools = self._tool_list()

        llm_plan = self._llm_generate_tool_plan(
            question=question, history=history, available_tools=tools
        )
        planned_calls = llm_plan or self._run_rule_based_tool_plan(question=question)

        tool_trace: List[Dict[str, Any]] = []
        for call in planned_calls:
            output = self._tool_call(call.get("tool", ""), call.get("args", {}), ctx)
            tool_trace.append(
                {
                    "tool": call.get("tool", ""),
                    "args": call.get("args", {}),
                    "output": output,
                }
            )

        if not self._has_llm():
            fallback = self._deterministic_answer_from_tools(question, tool_trace)
            yield ("chunk", fallback)
            yield (
                "meta",
                {
                    "evidence": [
                        e.model_dump() for e in self._tool_trace_to_evidence(tool_trace)
                    ],
                    "suggestions": self._generate_dynamic_suggestions(ctx, history),
                },
            )
            return

        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            fact_sheet = self._build_fact_sheet(ctx, tool_trace)
            prompt = self._build_synthesis_prompt(question, fact_sheet, history)

            for chunk in client.models.generate_content_stream(
                model=self._model_name(), contents=prompt
            ):
                token = chunk.text or ""
                if token:
                    yield ("chunk", token)

            yield (
                "meta",
                {
                    "evidence": [
                        e.model_dump() for e in self._tool_trace_to_evidence(tool_trace)
                    ],
                    "suggestions": self._generate_dynamic_suggestions(ctx, history),
                },
            )
        except (
            RuntimeError,
            ValueError,
            TypeError,
            OSError,
            TimeoutError,
            ConnectionError,
        ) as exc:
            yield ("chunk", f"Analysis unavailable: {exc}")
            yield (
                "meta",
                {
                    "evidence": [],
                    "suggestions": self._generate_dynamic_suggestions(ctx, history),
                },
            )

    def _deterministic_answer_from_tools(
        self, question: str, tool_trace: List[Dict[str, Any]]
    ) -> str:
        if not tool_trace:
            return "I do not have enough grounded session artifacts to answer this question yet."

        q = question.lower()
        overview = next(
            (
                t.get("output")
                for t in tool_trace
                if t.get("tool") == "get_session_overview"
            ),
            {},
        )
        if not isinstance(overview, dict):
            overview = {}
        diagnostics = next(
            (
                t.get("output")
                for t in tool_trace
                if t.get("tool") == "get_forecast_diagnostics"
            ),
            None,
        )
        metrics = next(
            (t.get("output") for t in tool_trace if t.get("tool") == "list_metrics"),
            None,
        )
        skill = next(
            (
                t.get("output")
                for t in tool_trace
                if t.get("tool") == "get_forecast_skill_score"
            ),
            None,
        )
        model = next(
            (
                t.get("output")
                for t in tool_trace
                if t.get("tool") == "get_model_metadata"
            ),
            None,
        )

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
                    reliability = self._reliability_label(
                        skill=skill.get("value"), mape=None
                    )
            elif isinstance(metrics, list):
                mape_val = next(
                    (
                        self._safe_float(m.get("value"))
                        for m in metrics
                        if str(m.get("name", "")).upper() == "MAPE"
                    ),
                    None,
                )
                reliability = self._reliability_label(skill=None, mape=mape_val)

            if reliability == "unknown":
                return "I cannot give a reliable confidence rating yet because quality signals are missing for this run."
            return (
                f"Confidence level is {reliability}. "
                "In simple terms, this means the forecast is "
                f"{'more dependable for planning' if reliability == 'strong' else ('usable with some caution' if reliability == 'moderate' else 'best treated as directional guidance rather than a firm commitment')}."
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

        # Try LLM-generated briefing first
        if self._has_llm():
            try:
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                # Build a lightweight fact sheet for the briefing
                overview_trace = [
                    {
                        "tool": "get_session_overview",
                        "args": {},
                        "output": {
                            "target": ctx.get("target_name"),
                            "horizon": ctx.get("horizon"),
                            "granularity": ctx.get("granularity"),
                            "model": ctx.get("model_metadata", {}),
                        },
                    }
                ]
                fact_sheet = self._build_fact_sheet(ctx, overview_trace)

                prompt = (
                    "You are a helpful forecast analyst embedded in a forecasting dashboard. "
                    "Write a short opening message (2-4 sentences) for someone viewing their forecast results.\n\n"
                    "CRITICAL RULES:\n"
                    "- NEVER open with greetings ('Good morning', 'Hello', etc.)\n"
                    "- The user can ALREADY SEE the chart, metrics (MAE, MAPE), model name, and data health on screen. "
                    "DO NOT just repeat those numbers back. Instead, interpret them.\n"
                    "- Focus on the ONE thing that matters most: should they trust this forecast? "
                    "To determine trust, ALWAYS look at the **Forecast Skill Score** first. If it's low or 0.0, warn the user "
                    "that the forecast is basically guessing or a random walk. If it's high (0.6+), tell them it found strong patterns.\n"
                    "Is there something surprising? What should they watch out for?\n"
                    "- Write for someone who is NOT a data scientist — no unexplained jargon\n"
                    "- Be genuinely helpful, not performatively technical\n"
                    "- End with a brief, natural invitation to ask questions (not formal)\n\n"
                    "Good example: 'This forecast looks solid for planning purposes — the model found a clear "
                    "weekly pattern in your sales data and is projecting it forward with fairly tight prediction bands. "
                    "The main thing to watch is whether next week's promotional activity changes the pattern. "
                    "Ask me anything about the assumptions or risks.'\n\n"
                    "Bad example: 'The MAPE is 6.3% and the MAE is 12.4. The model is AutoETS. "
                    "The forecast shows an upward trend of +2.1%.'\n\n"
                    f"Fact Sheet (for your reference, not to repeat):\n{fact_sheet}"
                )
                response = client.models.generate_content(
                    model=self._model_name(), contents=prompt
                )
                answer = (response.text or "").strip()
                if answer:
                    return answer
            except (
                RuntimeError,
                ValueError,
                TypeError,
                OSError,
                TimeoutError,
                ConnectionError,
            ):
                pass

        # Template fallback
        model_name = ctx["model_metadata"].get("name", "Selected model")
        rationale = ctx["model_metadata"].get(
            "rationale", "chosen from tournament performance"
        )
        horizon = ctx.get("horizon") or len(ctx.get("forecast_results") or [])
        granularity = ctx.get("granularity") or "periods"
        series = ctx.get("series", {})
        shape = self._describe_shape(series)
        endpoint_pct = series.get("endpoint_pct", 0.0)
        reliability = self._reliability_label(
            skill=ctx.get("forecast_skill_score"), mape=ctx.get("mape")
        )

        briefing = (
            f"Forecast briefing for {ctx['target_name']} over {horizon} {granularity}. "
            f"Overall direction looks {('upward' if endpoint_pct > 1 else 'downward' if endpoint_pct < -1 else 'mostly stable')}, "
            f"with a pattern that appears {shape}. "
            f"Confidence level is {reliability}. "
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

        llm_plan = self._llm_generate_tool_plan(
            question=question, history=history, available_tools=tools
        )
        planned_calls = llm_plan or self._run_rule_based_tool_plan(question=question)

        tool_trace: List[Dict[str, Any]] = []
        for call in planned_calls:
            tool_name = call.get("tool", "")
            args = call.get("args", {})
            output = self._tool_call(tool_name=tool_name, args=args, ctx=ctx)
            tool_trace.append({"tool": tool_name, "args": args, "output": output})

        evidence = [e.model_dump() for e in self._tool_trace_to_evidence(tool_trace)]
        suggestions = self._generate_dynamic_suggestions(ctx, history)

        llm_result = self._synthesize_with_llm(
            question=question,
            history=history,
            tool_trace=tool_trace,
            ctx=ctx,
        )
        if llm_result:
            return {
                "answer": llm_result["answer"],
                "evidence": evidence,
                "suggestions": llm_result.get("suggestions", suggestions),
            }

        return {
            "answer": self._sanitize_user_text(
                self._deterministic_answer_from_tools(
                    question=question, tool_trace=tool_trace
                )
            ),
            "evidence": evidence,
            "suggestions": suggestions,
        }
