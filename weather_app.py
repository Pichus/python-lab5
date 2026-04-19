import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import html, dcc
from dash.dependencies import Input, Output

df = pd.read_csv("weather2026.csv", encoding="utf-8")

df["період"] = df["період"].fillna("2026-03")
df["хмарність"] = df["хмарність"].str.replace("%", "").astype(float)
df["опади"] = df["опади"].str.replace(" м.м.", "").str.replace("-", "0").astype(float)
df["денна"] = df["денна температура повітря"].str.replace("°C", "").astype(float)
df["нічна"] = df["нічна температура повітря"].str.replace("°C", "").astype(float)
df["вітер"] = df["сила вітру"].str.replace(" м/с", "").astype(float)

df["дата"] = pd.to_datetime(df["період"] + "-" + df["день"].astype(str))

CLOUD_BINS = [0, 35, 70, 100]
CLOUD_LABELS = ["Сонячний", "Мінливо хмарний", "Хмарний"]
df["тип_дня"] = pd.cut(
    df["хмарність"], bins=CLOUD_BINS, labels=CLOUD_LABELS, include_lowest=True
)

periods = sorted(df["період"].unique())
period_options = [{"label": p, "value": p} for p in periods]

CHART_OPTIONS = [
    {"label": "а) Денна та нічна температура", "value": "temp"},
    {"label": "б) Хмарність", "value": "cloud"},
    {"label": "в) Сила вітру", "value": "wind"},
    {"label": "г) Опади (бульбашковий)", "value": "bubble"},
]

ANALYTICS_OPTIONS = [
    {"label": "а) Відхилення нічної від денної температури", "value": "hist"},
    {"label": "б) Кількість днів за типом хмарності (стовпчикова)", "value": "bar"},
    {"label": "в) Розподіл хмарності по місяцях (сонячний вибух)", "value": "sunburst"},
    {"label": "г) Дні з опадами по місяцях (кругова)", "value": "pie"},
]

CLOUD_COLORS = {
    "Хмарний": "#607D8B",
    "Мінливо хмарний": "#90A4AE",
    "Сонячний": "#FFD54F",
}

app = dash.Dash(__name__)

app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "maxWidth": "1200px",
        "margin": "0 auto",
        "padding": "20px",
    },
    children=[
        html.H1(
            "Аналіз погодних даних 2025–2026",
            style={"textAlign": "center", "color": "#1a237e"},
        ),
        html.P(
            "Виконавець: Тижук Дмитро Іванович, група К-26",
            style={"textAlign": "center", "color": "#555", "marginBottom": "30px"},
        ),
        html.Hr(),
        html.H2("Помісячні графіки", style={"color": "#283593"}),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Оберіть місяць:"),
                        dcc.Dropdown(
                            id="period-select",
                            options=period_options,
                            value=periods[0],
                            clearable=False,
                        ),
                    ],
                    style={
                        "width": "48%",
                        "display": "inline-block",
                        "marginRight": "2%",
                    },
                ),
                html.Div(
                    [
                        html.Label("Оберіть графік:"),
                        dcc.Dropdown(
                            id="chart-select",
                            options=CHART_OPTIONS,
                            value="temp",
                            clearable=False,
                        ),
                    ],
                    style={"width": "48%", "display": "inline-block"},
                ),
            ]
        ),
        html.Div(id="monthly-chart", style={"marginTop": "20px"}),
        html.Hr(),
        html.H2("Аналітика за весь період спостережень", style={"color": "#283593"}),
        html.Div(
            [
                html.Label("Оберіть аналітику:"),
                dcc.Dropdown(
                    id="analytics-select",
                    options=ANALYTICS_OPTIONS,
                    value="hist",
                    clearable=False,
                    style={"width": "60%"},
                ),
            ]
        ),
        html.Div(id="analytics-chart", style={"marginTop": "20px"}),
    ],
)


@app.callback(
    Output("monthly-chart", "children"),
    Input("period-select", "value"),
    Input("chart-select", "value"),
)
def update_monthly(period, chart):
    cur = df[df["період"] == period].copy()
    title_suffix = f" — {period}"

    if chart == "temp":
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=cur["день"],
                y=cur["денна"],
                mode="lines+markers",
                name="Денна температура",
                line=dict(color="#e65100"),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=cur["день"],
                y=cur["нічна"],
                mode="lines+markers",
                name="Нічна температура",
                line=dict(color="#1565c0"),
            )
        )
        fig.update_layout(
            title=f"Денна та нічна температура{title_suffix}",
            xaxis_title="День місяця",
            yaxis_title="Температура (°C)",
            legend_title="Тип",
        )

    elif chart == "cloud":
        fig = px.line(
            cur,
            x="день",
            y="хмарність",
            markers=True,
            title=f"Хмарність{title_suffix}",
            labels={"день": "День місяця", "хмарність": "Хмарність (%)"},
            color_discrete_sequence=["#546e7a"],
        )
        fig.update_layout(yaxis=dict(range=[0, 105]))

    elif chart == "wind":
        fig = px.line(
            cur,
            x="день",
            y="вітер",
            markers=True,
            title=f"Сила вітру{title_suffix}",
            labels={"день": "День місяця", "вітер": "Сила вітру (м/с)"},
            color_discrete_sequence=["#00838f"],
        )

    else:
        bubble_size = cur["опади"].where(cur["опади"] > 0, 0.5)
        fig = px.scatter(
            cur,
            x="день",
            y="денна",
            size=bubble_size,
            title=f"Денна температура та опади{title_suffix}",
            labels={
                "день": "День місяця",
                "денна": "Денна температура (°C)",
                "опади": "Опади (мм)",
            },
            color="денна",
            color_continuous_scale="Oranges",
            hover_data={"опади": True},
            size_max=40,
        )
        fig.update_layout(coloraxis_colorbar_title="Температура (°C)")

    return dcc.Graph(figure=fig)


@app.callback(
    Output("analytics-chart", "children"),
    Input("analytics-select", "value"),
)
def update_analytics(chart):
    if chart == "hist":
        df["відхилення"] = df["денна"] - df["нічна"]
        fig = px.histogram(
            df,
            x="відхилення",
            nbins=20,
            title="Гістограма відхилення нічної температури від денної",
            labels={"відхилення": "Відхилення (°C)", "count": "Кількість днів"},
            color_discrete_sequence=["#1565c0"],
        )
        fig.update_layout(yaxis_title="Кількість днів", bargap=0.05)

    elif chart == "bar":
        counts = (
            df.groupby(["період", "тип_дня"], observed=True)
            .size()
            .reset_index(name="кількість")
        )
        counts["тип_дня"] = counts["тип_дня"].astype(str)
        fig = px.bar(
            counts,
            x="період",
            y="кількість",
            color="тип_дня",
            title="Кількість днів за типом хмарності по місяцях",
            labels={
                "період": "Місяць",
                "кількість": "Кількість днів",
                "тип_дня": "Тип дня",
            },
            color_discrete_map=CLOUD_COLORS,
            category_orders={"тип_дня": CLOUD_LABELS},
        )
        fig.update_layout(barmode="stack", xaxis_tickangle=-45)

    elif chart == "sunburst":
        counts = (
            df.groupby(["період", "тип_дня"], observed=True)
            .size()
            .reset_index(name="кількість")
        )
        counts["тип_дня"] = counts["тип_дня"].astype(str)
        fig = px.sunburst(
            counts,
            path=["період", "тип_дня"],
            values="кількість",
            title="Розподіл типів хмарності по місяцях (сонячний вибух)",
            color="тип_дня",
            color_discrete_map=CLOUD_COLORS,
        )

    else:
        rain_days = (
            df[df["опади"] > 0]
            .groupby("період")
            .size()
            .reset_index(name="днів з опадами")
        )
        fig = px.pie(
            rain_days,
            names="період",
            values="днів з опадами",
            title="Частка днів з опадами по місяцях",
            labels={"період": "Місяць", "днів з опадами": "Кількість днів"},
        )
        fig.update_traces(textposition="inside", textinfo="label+value")

    return dcc.Graph(figure=fig)


if __name__ == "__main__":
    app.run()
