from typing import List, Tuple

import pandas as pd

from app.domain.data import CleaningAction, CleaningReport
from app.domain.ontology import ForecastOntology


class RuleBasedCleaner:
    """
    Implementation of AutoCleaner using deterministic rules based on the Ontology.
    """

    def _safe_convert_datetime(self, series: pd.Series) -> pd.Series:
        """
        Robust cleaner that handles Mixed Formats, Excel Dates, Unix Stamps,
        and 'Ancient' dates.
        """
        # 1. THE HAPPY PATH: Let Pandas guess (fastest for standard ISO data)
        # We try this first because it's C-optimized.
        try:
            return pd.to_datetime(series, format="mixed", dayfirst=True)
        except (ValueError, TypeError, pd.errors.OutOfBoundsDatetime):
            pass

        # 2. NUMERIC CHECK (Excel vs Unix)
        # If the column is numeric (or mostly numeric strings), handle that.
        series_numeric = pd.to_numeric(series, errors="coerce")
        if series_numeric.notna().sum() > (len(series) * 0.5):  # If mostly numeric
            sample = series_numeric.dropna().iloc[0]
            # Heuristic: Unix timestamps (seconds) are usually > 1 billion (Year 2001+)
            if sample > 1_000_000_000:
                return pd.to_datetime(series_numeric, unit="s", errors="coerce")
            # Heuristic: Excel serials are usually < 100,000 (Year 2173)
            elif sample < 200_000:
                return pd.to_datetime(
                    series_numeric, unit="D", origin="1899-12-30", errors="coerce"
                )

        # 3. THE "YEAR 1" FIX (Your specific error)
        # Handles "1-01", "01-01" by shifting to 2000s
        str_series = series.astype(str).str.strip()
        if str_series.str.match(r"^\d{1,2}[-/]\d{1,2}$").any():
            try:
                # Prepend '20' to turn "1-01" -> "2001-01"
                corrected = str_series.apply(
                    lambda x: f"20{x.zfill(5)}" if "-" in x else f"20{x.zfill(5)}"
                )
                return pd.to_datetime(corrected, errors="coerce")
            except Exception:
                pass

        # 4. LAST RESORT: Coerce
        return pd.to_datetime(series, errors="coerce", dayfirst=True)

    def clean(
        self, df: pd.DataFrame, ontology: ForecastOntology
    ) -> Tuple[pd.DataFrame, CleaningReport]:
        """
        Preprocesses the dataset based on the ontology and generates
        a report of all actions
        """
        initial_shape = list(df.shape)
        actions: List[CleaningAction] = []

        # Identify roles
        time_col = next(
            (c.column_name for c in ontology.columns if c.role == "time_index"), None
        )
        target_col = next(
            (c.column_name for c in ontology.columns if c.role == "target"), None
        )

        if not time_col or not target_col:
            raise ValueError("Ontology must specify a time_index and a target column.")

        df = df.copy()

        # 0. Normalize Column Names
        original_cols = df.columns.tolist()
        df.columns = df.columns.str.strip()
        if any(c != o for c, o in zip(df.columns, original_cols)):
            actions.append(
                CleaningAction(
                    column="Multiple",
                    action="normalization",
                    description="Normalized column names by stripping whitespace.",
                )
            )

        # Reconcile Ontology with Cleaned DataFrame
        # If the LLM outputted "Column " (with space) but we have "Column" (stripped),
        # we update the ontology's column name to match the DataFrame.
        for col_def in ontology.columns:
            stripped_name = col_def.column_name.strip()
            if col_def.column_name not in df.columns and stripped_name in df.columns:
                # Update the ontology to use the stripped name
                col_def.column_name = stripped_name

        # Refresh roles in case they were updated during reconciliation
        time_col = next(
            (c.column_name for c in ontology.columns if c.role == "time_index"), None
        )
        target_col = next(
            (c.column_name for c in ontology.columns if c.role == "target"), None
        )

        # Verify columns exist
        if time_col not in df.columns:
            raise ValueError(
                f"Time column '{time_col}' not found in dataset. "
                f"Available: {df.columns.tolist()}"
            )
        if target_col not in df.columns:
            raise ValueError(
                f"Target column '{target_col}' not found in dataset. "
                f"Available: {df.columns.tolist()}"
            )

        # 1. Convert Target to Numeric
        nulls_before = df[target_col].isna().sum()
        df[target_col] = pd.to_numeric(df[target_col], errors="coerce")
        nulls_after = df[target_col].isna().sum()
        if nulls_after > nulls_before:
            actions.append(
                CleaningAction(
                    column=target_col,
                    action="type_conversion",
                    description=(
                        f"Converted target to numeric. "
                        f"{nulls_after - nulls_before} invalid cells replaced with NaN."
                    ),
                )
            )

        # 2. Convert Time Column (Updated)
        try:
            df[time_col] = self._safe_convert_datetime(df[time_col])

            # Validation: Check if we lost too much data
            # If >50% became NaT, our conversion strategy likely failed
            if df[time_col].isna().mean() > 0.5:
                raise ValueError(
                    f"Failed to parse >50% of dates in column '{time_col}'"
                )

        except Exception as e:
            raise ValueError(f"Could not convert {time_col} to datetime: {e}")

        # Drop rows where datetime conversion failed (NaT)
        if df[time_col].isna().any():
            dropped_count = df[time_col].isna().sum()
            df = df.dropna(subset=[time_col])
            actions.append(
                CleaningAction(
                    column=str(time_col),
                    action="row_dropping",
                    description=f"Dropped {dropped_count} rows with unparseable dates.",
                )
            )

        # 3. Sort & Set Index
        df = df.sort_values(time_col).set_index(time_col)

        # 4. Handle Duplicates
        if df.index.duplicated().any():
            target_def = next(
                c for c in ontology.columns if c.column_name == target_col
            )
            method = target_def.resampling_method
            old_count = len(df)
            if method == "sum":
                df = df.groupby(level=0).sum()
            elif method == "mean":
                df = df.groupby(level=0).mean()
            elif method == "last":
                df = df.groupby(level=0).last()
            elif method == "max":
                df = df.groupby(level=0).max()
            else:
                df = df.groupby(level=0).mean()  # Default

            actions.append(
                CleaningAction(
                    column=str(time_col),
                    action="aggregation",
                    description=(
                        f"Found duplicated timestamps. Aggregated observations "
                        f"from {old_count} to {len(df)} using '{method}' strategy."
                    ),
                )
            )

        # 5. Infer Frequency and Reindex
        inferred_freq = pd.infer_freq(df.index)

        if not inferred_freq:
            unit = ontology.problem.granularity.unit
            if unit == "day":
                inferred_freq = "D"
            elif unit == "month":
                inferred_freq = "MS"
            elif unit == "hour":
                inferred_freq = "H"
            else:
                inferred_freq = "D"
            actions.append(
                CleaningAction(
                    column=str(time_col),
                    action="resampling",
                    description=(
                        f"Could not infer frequency automatically. "
                        f"Applied manual frequency '{inferred_freq}' based on ontology."
                    ),
                )
            )
        else:
            actions.append(
                CleaningAction(
                    column=str(time_col),
                    action="resampling",
                    description=(
                        f"Inferred frequency '{inferred_freq}' and reindexed to ensure "
                        f"regularity."
                    ),
                )
            )

        # Reindex to fill gaps
        full_idx = pd.date_range(
            start=df.index.min(), end=df.index.max(), freq=inferred_freq
        )
        old_len = len(df)
        df = df.reindex(full_idx)
        if len(df) > old_len:
            actions.append(
                CleaningAction(
                    column=str(time_col),
                    action="gap_filling",
                    description=(
                        f"Detected gaps in continuity. Added "
                        f"{len(df) - old_len} missing timestamps."
                    ),
                )
            )

        # 6. Imputation
        target_def = next(c for c in ontology.columns if c.column_name == target_col)
        nulls_count = df[target_col].isna().sum()
        if nulls_count > 0:
            if target_def.data_type == "continuous":
                df[target_col] = (
                    df[target_col].interpolate(method="linear").ffill().bfill()
                )
                imp_method = "Linear Interpolation"
            else:
                df[target_col] = df[target_col].ffill().bfill()
                imp_method = "Forward Fill"

            actions.append(
                CleaningAction(
                    column=target_col,
                    action="imputation",
                    description=f"Imputed {nulls_count} values using {imp_method}.",
                )
            )

        df.index.name = time_col
        final_df = df.reset_index()

        report = CleaningReport(
            actions=actions,
            initial_shape=initial_shape,
            final_shape=list(final_df.shape),
            summary=(
                f"Cleaned dataset. Performed {len(actions)} specific "
                f"transformations to prepare for modeling."
            ),
        )

        return final_df, report
