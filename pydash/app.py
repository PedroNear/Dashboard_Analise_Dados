# dashboard_pnadc.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import os

print("📊 Iniciando carregamento de dados...")

# Verificar e carregar dados
arquivo_excel = "dados_PNADC_preparado_dashboard.xlsx"
if os.path.exists(arquivo_excel):
    df = pd.read_excel(arquivo_excel, sheet_name="Dados_Cor_Dashboard")
    print("✅ Dados carregados do Excel")
else:
    print("⚠️  Arquivo Excel não encontrado. Criando dados de exemplo...")
    
    # Criar dados de exemplo
    estados = ['São Paulo', 'Rio de Janeiro', 'Minas Gerais', 'Bahia', 'Paraná', 'Rio Grande do Sul']
    regioes = ['Sudeste', 'Sudeste', 'Sudeste', 'Nordeste', 'Sul', 'Sul']
    siglas = ['SP', 'RJ', 'MG', 'BA', 'PR', 'RS']
    
    dados_exemplo = []
    for ano in range(2012, 2018):
        for i, estado in enumerate(estados):
            dados_exemplo.append({
                'Ano': ano,
                'COR': 'BRANCA',
                'Localidade': estado,
                'Sigla_Localidade': siglas[i],
                'Regiao': regioes[i],
                'ESPVIDA': 75 + (ano-2012)*0.5 + i*0.3,
                'IDHM_E': 0.7 + (ano-2012)*0.02 + i*0.03,
                'IDHM_L': 0.8 + (ano-2012)*0.01 + i*0.02,
                'V_RENOCUP': 1500 + (ano-2012)*100 + i*200,
                'T_ANALF25M': 5 - (ano-2012)*0.2 - i*0.3
            })
    
    df = pd.DataFrame(dados_exemplo)
    print("✅ Dados de exemplo criados")

print(f"📈 Dimensões do dataset: {df.shape}")

# Limpeza básica
df = df.dropna(subset=['Ano', 'COR', 'Localidade', 'Regiao'])

# Inicializar app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout do app
app.layout = dbc.Container([
    html.H1("📊 Dashboard PNADC - Indicadores por Cor e Localidade", 
            className="my-4 text-center",
            style={'color': '#2E86AB'}),
    
    # Informações sobre os dados
    dbc.Alert([
        html.H4("ℹ️ Sobre os Dados", className="alert-heading"),
        f"Dados carregados: {len(df)} linhas, {df['Ano'].min()}-{df['Ano'].max()}",
        html.Br(),
        f"Estados: {df['Localidade'].nunique()}, Regiões: {df['Regiao'].nunique()}"
    ], color="info", className="mb-4"),

    # Filtros
    dbc.Card([
        dbc.CardHeader("🎛️ Filtros", style={'background-color': '#F8F9FA'}),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("📅 Ano"),
                    dcc.Dropdown(
                        id='ano-dropdown',
                        options=[{'label': str(ano), 'value': ano} for ano in sorted(df['Ano'].unique())],
                        value=df['Ano'].max()
                    )
                ], width=3),
                dbc.Col([
                    html.Label("👤 Cor/Raça"),
                    dcc.Dropdown(
                        id='cor-dropdown',
                        options=[{'label': cor, 'value': cor} for cor in df['COR'].unique()],
                        value='BRANCA'
                    )
                ], width=3),
                dbc.Col([
                    html.Label("🗺️ Região"),
                    dcc.Dropdown(
                        id='regiao-dropdown',
                        options=[{'label': reg, 'value': reg} for reg in df['Regiao'].unique()],
                        value='Sudeste'
                    )
                ], width=3),
                dbc.Col([
                    html.Label("📊 Indicador"),
                    dcc.Dropdown(
                        id='indicador-dropdown',
                        options=[
                            {'label': 'Esperança de Vida', 'value': 'ESPVIDA'},
                            {'label': 'IDHM Educação', 'value': 'IDHM_E'},
                            {'label': 'IDHM Longevidade', 'value': 'IDHM_L'},
                            {'label': 'Renda Ocupacional', 'value': 'V_RENOCUP'},
                            {'label': 'Taxa de Analfabetismo (25M+)', 'value': 'T_ANALF25M'}
                        ],
                        value='ESPVIDA'
                    )
                ], width=3)
            ], className="mb-4"),
        ])
    ], className="mb-4"),

    # Tabs para Estados vs Regiões
    dcc.Tabs(id='tabs', value='tab-estados', children=[
        dcc.Tab(label='🏙️ Visão por Estado', value='tab-estados'),
        dcc.Tab(label='🗺️ Visão por Região', value='tab-regioes'),
    ]),

    html.Div(id='tabs-content'),

], fluid=True)

# Callback para atualizar abas
@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs', 'value'),
     Input('ano-dropdown', 'value'),
     Input('cor-dropdown', 'value'),
     Input('regiao-dropdown', 'value'),
     Input('indicador-dropdown', 'value')]
)
def render_content(tab, ano, cor, regiao, indicador):
    dff = df[(df['Ano'] == ano) & (df['COR'] == cor)]

    if tab == 'tab-estados':
        dff_estado = dff[dff['Regiao'] == regiao]
        return dbc.Row([
            dbc.Col([
                dcc.Graph(
                    id='mapa-brasil',
                    figure=px.choropleth(
                        dff,
                        locations='Sigla_Localidade',
                        locationmode='ISO-3',
                        color=indicador,
                        scope='south america',
                        title=f'{indicador} por Estado ({ano}) - {cor}',
                        hover_name='Localidade',
                        color_continuous_scale='Viridis'
                    ).update_geos(visible=False, projection_scale=1.2, center={"lat": -14, "lon": -55})
                )
            ], width=6),
            dbc.Col([
                dcc.Graph(
                    id='bar-estados',
                    figure=px.bar(
                        dff_estado,
                        x='Localidade',
                        y=indicador,
                        title=f'{indicador} - Estados da {regiao}',
                        text=indicador
                    ).update_traces(texttemplate='%{text:.2f}', textposition='outside')
                )
            ], width=6)
        ])

    elif tab == 'tab-regioes':
        dff_regiao = dff.groupby('Regiao')[indicador].mean().reset_index()
        return dbc.Row([
            dbc.Col([
                dcc.Graph(
                    id='bar-regioes',
                    figure=px.bar(
                        dff_regiao,
                        x='Regiao',
                        y=indicador,
                        title=f'{indicador} - Média por Região',
                        text=indicador
                    ).update_traces(texttemplate='%{text:.2f}', textposition='outside')
                )
            ], width=6),
            dbc.Col([
                dcc.Graph(
                    id='linha-evolucao',
                    figure=px.line(
                        df[df['COR'] == cor].groupby(['Ano', 'Regiao'])[indicador].mean().reset_index(),
                        x='Ano',
                        y=indicador,
                        color='Regiao',
                        title=f'Evolução do {indicador} por Região ({cor})'
                    )
                )
            ], width=6)
        ])

# Rodar o app - LINHA CORRIGIDA!
if __name__ == '__main__':
    app.run(debug=True, port=8050)  # ✅ CORREÇÃO: app.run() em vez de app.run_server()