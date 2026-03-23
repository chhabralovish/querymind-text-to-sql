import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def auto_chart(df: pd.DataFrame, question: str = ""):
    """
    Automatically generate the most appropriate chart for the data.
    Returns a Plotly figure or None if chart is not appropriate.
    """
    if df is None or df.empty:
        return None

    # Need at least 2 columns and 2 rows for a meaningful chart
    if len(df.columns) < 2 or len(df) < 2:
        return None

    # Identify column types
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = df.select_dtypes(exclude=['number']).columns.tolist()

    # Too many rows — sample for chart
    chart_df = df.head(50)

    try:
        # Case 1: One categorical + one numeric → Bar chart
        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            x_col = cat_cols[0]
            y_col = num_cols[0]

            # If too many categories, take top 20
            if chart_df[x_col].nunique() > 20:
                chart_df = chart_df.nlargest(20, y_col)

            fig = px.bar(
                chart_df,
                x=x_col,
                y=y_col,
                title=f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
                color=y_col,
                color_continuous_scale="blues",
                template="plotly_white"
            )
            fig.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                height=400
            )
            return fig

        # Case 2: Two numeric columns → Scatter plot
        elif len(num_cols) >= 2:
            fig = px.scatter(
                chart_df,
                x=num_cols[0],
                y=num_cols[1],
                title=f"{num_cols[1].replace('_', ' ').title()} vs {num_cols[0].replace('_', ' ').title()}",
                template="plotly_white",
                trendline="ols" if len(chart_df) > 5 else None
            )
            fig.update_layout(height=400)
            return fig

        # Case 3: Single numeric column → Histogram
        elif len(num_cols) == 1:
            fig = px.histogram(
                chart_df,
                x=num_cols[0],
                title=f"Distribution of {num_cols[0].replace('_', ' ').title()}",
                template="plotly_white",
                color_discrete_sequence=["#636EFA"]
            )
            fig.update_layout(height=400)
            return fig

        # Case 4: Two categorical columns → Grouped bar
        elif len(cat_cols) >= 2:
            counts = chart_df.groupby(cat_cols[:2]).size().reset_index(name='count')
            fig = px.bar(
                counts,
                x=cat_cols[0],
                y='count',
                color=cat_cols[1],
                title=f"Count by {cat_cols[0]} and {cat_cols[1]}",
                template="plotly_white",
                barmode="group"
            )
            fig.update_layout(height=400)
            return fig

    except Exception:
        return None

    return None


def pie_chart(df: pd.DataFrame, label_col: str, value_col: str, title: str = ""):
    """Generate a pie chart."""
    fig = px.pie(
        df.head(10),
        names=label_col,
        values=value_col,
        title=title or f"{value_col} by {label_col}",
        template="plotly_white"
    )
    return fig