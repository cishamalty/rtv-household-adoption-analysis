# app_mugume_dash_complete.py - Raising The Village Program Monitoring Dashboard
import dash
from dash import dcc, html, dash_table, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Load data - NOTE: Double curly braces {} to escape f-string
df = pd.read_csv(r"E:/MUGUME/Raising village/outputs/Mugume_first_visit_scores_by_geo.csv")
training = pd.read_csv(r"E:/MUGUME/Raising village/outputs/Mugume_training_counts_and_props_by_geo.csv")
visits = pd.read_csv(r"E:/MUGUME/Raising village/outputs/Mugume_visits_by_geo.csv")

# Convert to percentage
for col in ['wash_mean', 'agri_mean', 'vsla_mean', 'overall_mean']:
    if col in df.columns and df[col].max() <= 1.1:
        df[col] = df[col] * 100

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Raising The Village - Program Monitoring"

# Layout
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Program Monitoring Dashboard", className="text-center text-primary mb-4"))),
    
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='region-filter',
            options=[{'label': r, 'value': r} for r in sorted(df['region_name'].dropna().unique())],
            placeholder="All Regions", className="mb-3"
        ), width=4),
        dbc.Col(dcc.Dropdown(id='district-filter', placeholder="All Districts"), width=4),
    ]),
    
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id='kpi-overall'), html.P("Overall Adoption")
        ]), color="success", inverse=True), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id='kpi-wash'), html.P("WASH Score")
        ]), color="info", inverse=True), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id='kpi-agri'), html.P("Agriculture Score")
        ]), color="warning", inverse=True), width=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(id='kpi-vsla'), html.P("VSLA Participation")
        ]), color="danger", inverse=True), width=3),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='main-chart'), width=8),
        dbc.Col(dcc.Graph(id='radar-chart'), width=4),
    ]),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='visits-chart'), width=6),
        dbc.Col(dcc.Graph(id='training-chart'), width=6),
    ]),
    
    dbc.Row(dbc.Col(dash_table.DataTable(
        id='data-table', page_size=10, style_table={'overflowX': 'auto'}
    ))),
    
    html.Footer("© 2025 Raising The Village | Prepared by: Mugume Martin", className="text-center text-muted mt-4")
], fluid=True)

# Callbacks
@app.callback(
    Output('district-filter', 'options'),
    Input('region-filter', 'value')
)
def update_districts(region):
    if region:
        districts = sorted(df[df['region_name'] == region]['district_name'].unique())
    else:
        districts = sorted(df['district_name'].unique())
    return [{'label': d, 'value': d} for d in districts]

@app.callback(
    [Output('kpi-overall', 'children'), Output('kpi-wash', 'children'),
     Output('kpi-agri', 'children'), Output('kpi-vsla', 'children'),
     Output('main-chart', 'figure'), Output('radar-chart', 'figure'),
     Output('visits-chart', 'figure'), Output('training-chart', 'figure'),
     Output('data-table', 'data'), Output('data-table', 'columns')],
    [Input('region-filter', 'value'), Input('district-filter', 'value')]
)
def update_dashboard(region, district):
    filtered = df.copy()
    if region: filtered = filtered[filtered['region_name'] == region]
    if district: filtered = filtered[filtered['district_name'] == district]
    
    kpi_o = f"{filtered['overall_mean'].mean():.1f}%" if not filtered.empty else "N/A"
    kpi_w = f"{filtered['wash_mean'].mean():.1f}%" if not filtered.empty else "N/A"
    kpi_a = f"{filtered['agri_mean'].mean():.1f}%" if not filtered.empty else "N/A"
    kpi_v = f"{filtered['vsla_mean'].mean():.1f}%" if not filtered.empty else "N/A"
    
    bar_fig = px.bar(filtered.sort_values('overall_mean'), 
                     x='cluster_name', y='overall_mean', color='overall_mean',
                     color_continuous_scale=['red', 'orange', 'green'], range_color=[0, 100],
                     labels={'overall_mean': 'Overall Adoption (%)'}, height=500)
    bar_fig.update_layout(xaxis_title="Cluster", yaxis_title="Adoption (%)")
    
    radar_fig = go.Figure()
    means = [filtered[c].mean() for c in ['wash_mean','agri_mean','vsla_mean','overall_mean']]
    radar_fig.add_trace(go.Scatterpolar(r=means, theta=['WASH','Agriculture','VSLA','Overall'], 
                                       fill='toself', name='Selected'))
    radar_fig.update_layout(polar=dict(radialaxis=dict(range=[0,100])), height=400)
    
    visits_fig = px.bar(visits[visits['region_name'].isin(filtered['region_name'].unique())] if region else visits,
                        x='cluster_name', y=['visited_once_prop','visited_twice_prop','visited_thrice_plus_prop'],
                        barmode='stack', labels={'value': 'Proportion', 'variable': 'Visit Count'})
    visits_fig.update_yaxes(tickformat='.0%')
    
    train_cols = [c for c in training.columns if '_prop' in c]
    train_fig = px.bar(training[training['region_name'].isin(filtered['region_name'].unique())] if region else training,
                       x='cluster_name', y=train_cols, barmode='group')
    train_fig.update_yaxes(tickformat='.0%')
    
    table_data = filtered[['region_name','district_name','cluster_name','overall_mean']].round(1).to_dict('records')
    table_cols = [
        {"name": "Region", "id": "region_name"},
        {"name": "District", "id": "district_name"},
        {"name": "Cluster", "id": "cluster_name"},
        {"name": "Overall (%)", "id": "overall_mean"}
    ]
    
    return kpi_o, kpi_w, kpi_a, kpi_v, bar_fig, radar_fig, visits_fig, train_fig, table_data, table_cols

if __name__ == '__main__':
    print("Starting dashboard...")
    print("Open http://127.0.0.1:8050 in your browser")
    app.run(debug=True)
