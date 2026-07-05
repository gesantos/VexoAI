import io
import re
import urllib.parse

import pandas as pd
import streamlit as st

from src.admin import GestaoAdministrativa
from src.sourcing import MotorBuscaSourcing
from src.supabase_client import NucleoSupabase


st.set_page_config(
    page_title="Núcleo Único de Recrutamento",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


ETAPAS_KANBAN = ["Mapeado", "Contatado", "Triagem", "Aprovado", "Recusado"]
ETAPAS_VISUAIS = {
    "Mapeado": "Mapeados (Sourcing)",
    "Contatado": "Contatados",
    "Triagem": "Triagem / Interesse",
    "Aprovado": "Entrevista / Aprovados",
    "Recusado": "Recusados",
}
CARGOS_DISPONIVEIS = {
    "Médico do Trabalho": "medico_trabalho",
    "Técnico de Segurança": "tecnico_seguranca",
    "Outra profissão": None,
}
COMPETENCIAS_SUGERIDAS = [
    "NR-7",
    "NR-35",
    "SOC",
    "Age Technology",
    "PCMSO",
    "Audiometria",
    "SESMT",
    "PGR",
    "CIPA",
    "EPI",
]
EXCLUSOES_SUGERIDAS = ["Pediatra", "Plantonista", "Vigilante", "Porteiro"]
TEMPLATES_ABORDAGEM = {
    "Abordagem TST Sênior": (
        "Olá [NOME], tudo bem? Vi a sua experiência em [EMPRESA] com foco em "
        "[CARGO] e achei o seu perfil bastante aderente a uma oportunidade que estamos a conduzir."
    ),
    "Convite Médico do Trabalho": (
        "Olá [NOME], acompanhei o seu histórico em [EMPRESA] e a sua atuação em "
        "[CARGO]. Gostaria de apresentar uma vaga com forte aderência ao seu perfil."
    ),
    "Mensagem Curta de Interesse": (
        "Olá [NOME], identifiquei o seu perfil para uma oportunidade em [CARGO]. "
        "Se fizer sentido para si, posso partilhar mais detalhes."
    ),
}


def aplicar_estilos_globais():
    st.markdown(
        """
        <style>
        :root {
            --bg: #282a36;
            --bg-soft: #343746;
            --surface: rgba(40, 42, 54, 0.92);
            --surface-strong: #343746;
            --border: rgba(189, 147, 249, 0.18);
            --text: #f8f8f2;
            --muted: #bdc1d6;
            --primary: #bd93f9;
            --primary-soft: rgba(189, 147, 249, 0.14);
            --sidebar: #1f2029;
            --sidebar-text: #f8f8f2;
            --success: #50fa7b;
            --info: #8be9fd;
            --warning: #ffb86c;
            --danger: #ff5555;
            --shadow: 0 14px 34px rgba(0, 0, 0, 0.28);
        }
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(189, 147, 249, 0.12), transparent 22%),
                radial-gradient(circle at top left, rgba(139, 233, 253, 0.08), transparent 18%),
                var(--bg);
        }
        [data-testid="stSidebar"] {
            background: var(--sidebar);
            border-right: 1px solid rgba(255,255,255,0.04);
        }
        [data-testid="stSidebar"] * {
            color: var(--sidebar-text);
        }
        .page-shell {
            background: var(--surface);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.9rem;
        }
        .hero-title {
            font-size: 1.45rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.15rem;
        }
        .hero-subtitle {
            color: var(--muted);
            font-size: 0.92rem;
            margin-bottom: 0;
        }
        .soft-card {
            background: var(--surface-strong);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.85rem 0.95rem;
            box-shadow: var(--shadow);
            margin-bottom: 0.6rem;
        }
        .soft-card h4 {
            margin: 0 0 0.35rem 0;
            font-size: 0.94rem;
            color: var(--text);
        }
        .soft-card p {
            margin: 0;
            color: var(--muted);
            font-size: 0.88rem;
        }
        .app-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 0.8rem 0.95rem;
            margin-bottom: 0.9rem;
            box-shadow: var(--shadow);
        }
        .app-topbar-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text);
            margin: 0;
        }
        .app-topbar-subtitle {
            color: var(--muted);
            font-size: 0.82rem;
            margin: 0.1rem 0 0 0;
        }
        .topbar-badges {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 0.5rem;
        }
        .topbar-badge {
            background: var(--primary-soft);
            color: var(--primary);
            border: 1px solid rgba(189, 147, 249, 0.24);
            border-radius: 999px;
            padding: 0.3rem 0.7rem;
            font-size: 0.78rem;
            font-weight: 700;
        }
        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.35rem 0 0.75rem 0;
        }
        .pill {
            background: var(--bg-soft);
            color: var(--text);
            border-radius: 999px;
            padding: 0.3rem 0.7rem;
            font-size: 0.78rem;
            font-weight: 600;
            border: 1px solid rgba(255,255,255,0.04);
        }
        .section-label {
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            color: var(--muted);
            margin: 0.3rem 0 0.45rem 0;
        }
        .layout-panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 0.9rem 0.95rem 0.35rem 0.95rem;
            box-shadow: var(--shadow);
            margin-bottom: 0.8rem;
        }
        .layout-panel h3 {
            margin: 0;
            color: var(--text);
            font-size: 0.96rem;
        }
        .layout-panel p {
            margin: 0.25rem 0 0.8rem 0;
            color: var(--muted);
            font-size: 0.88rem;
        }
        .login-shell {
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 1rem;
            align-items: stretch;
            margin-bottom: 1rem;
        }
        .login-brand {
            background: linear-gradient(135deg, #1f2029, #282a36 55%, #44475a);
            border-radius: 18px;
            padding: 1.4rem;
            color: #f8fafc;
            box-shadow: var(--shadow);
            min-height: 320px;
        }
        .login-brand h2 {
            margin: 0 0 0.45rem 0;
            font-size: 1.8rem;
        }
        .login-brand p {
            color: rgba(226,232,240,0.88);
            font-size: 0.97rem;
            line-height: 1.55;
        }
        .login-list {
            margin-top: 1rem;
            display: grid;
            gap: 0.65rem;
        }
        .login-list-item {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            padding: 0.8rem 0.9rem;
            color: #e2e8f0;
            font-size: 0.9rem;
        }
        .login-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1.25rem;
            box-shadow: var(--shadow);
        }
        .candidate-card {
            background: var(--surface-strong);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 0.9rem;
            box-shadow: var(--shadow);
            margin-bottom: 0.7rem;
        }
        .candidate-name {
            color: var(--text);
            font-size: 0.98rem;
            font-weight: 700;
            margin-bottom: 0.15rem;
        }
        .candidate-meta {
            color: var(--muted);
            font-size: 0.82rem;
            margin-bottom: 0.25rem;
        }
        .kanban-column {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 0.8rem 0.75rem;
            min-height: 240px;
            box-shadow: var(--shadow);
        }
        .kanban-column h4 {
            margin: 0 0 0.25rem 0;
            color: var(--text);
            font-size: 0.9rem;
        }
        .kanban-column p {
            margin: 0 0 0.6rem 0;
            color: var(--muted);
            font-size: 0.8rem;
        }
        div[data-testid="stButton"] > button, div[data-testid="stLinkButton"] a {
            border-radius: 12px !important;
        }
        div[data-testid="stButton"] > button {
            background: #44475a;
            border: 1px solid var(--border);
            color: var(--text);
        }
        div[data-testid="stButton"] > button[kind="primary"] {
            background: var(--primary) !important;
            color: #282a36 !important;
            border-color: var(--primary) !important;
        }
        div[data-testid="stMetric"] {
            background: var(--surface-strong);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.55rem 0.75rem;
            box-shadow: var(--shadow);
        }
        [data-testid="stExpander"] {
            border: 1px solid var(--border);
            border-radius: 14px;
            background: rgba(68, 71, 90, 0.55);
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        textarea,
        input {
            background: #343746 !important;
            color: var(--text) !important;
            border-color: rgba(189, 147, 249, 0.22) !important;
        }
        label, .stMarkdown, p, span, small {
            color: var(--text);
        }
        .stCodeBlock, pre, code {
            background: #1f2029 !important;
            color: #f8f8f2 !important;
        }
        div[data-testid="stAlert"] {
            border-radius: 14px;
            border: 1px solid var(--border);
        }
        .block-container {
            padding-top: 1.1rem;
            padding-bottom: 1.5rem;
        }
        @media (max-width: 900px) {
            .login-shell {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def abrir_container_pagina(titulo, subtitulo):
    st.markdown(
        f"""
        <div class="page-shell">
            <div class="hero-title">{titulo}</div>
            <p class="hero-subtitle">{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def abrir_layout_panel(titulo, texto):
    st.markdown(
        f"""
        <div class="layout-panel">
            <h3>{titulo}</h3>
            <p>{texto}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_pills(valores):
    itens = [valor for valor in valores if valor]
    if not itens:
        return
    html = "".join(f'<span class="pill">{valor}</span>' for valor in itens)
    st.markdown(f'<div class="pill-row">{html}</div>', unsafe_allow_html=True)


def abrir_soft_card(titulo, texto):
    st.markdown(
        f"""
        <div class="soft-card">
            <h4>{titulo}</h4>
            <p>{texto}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_topbar():
    perfil = "Admin" if st.session_state.usuario_admin else "Recrutador"
    st.markdown(
        f"""
        <div class="app-topbar">
            <div>
                <p class="app-topbar-title">Núcleo Único de Recrutamento</p>
                <p class="app-topbar-subtitle">Fluxo integrado de sourcing, radar, pipeline e abordagem.</p>
            </div>
            <div class="topbar-badges">
                <span class="topbar-badge">{st.session_state.usuario_nome}</span>
                <span class="topbar-badge">{perfil}</span>
                <span class="topbar-badge">{st.session_state.menu_atual}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def abrir_candidate_card(candidato):
    st.markdown(
        f"""
        <div class="candidate-card">
            <div class="candidate-name">{candidato['nome']}</div>
            <div class="candidate-meta">{candidato['titulo_profissional']} | {candidato['empresa_atual']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_login_hero():
    st.markdown(
        """
        <div class="login-shell">
            <div class="login-brand">
                <h2>Núcleo Único de Recrutamento</h2>
                <p>Centralize sourcing, radar, pipeline e abordagem em uma operação mais organizada, com busca estruturada e visão contínua dos talentos.</p>
                <div class="login-list">
                    <div class="login-list-item">Busca X-Ray com filtros operacionais e múltiplas fontes.</div>
                    <div class="login-list-item">Radar de talentos com higienização, aderência e ações rápidas.</div>
                    <div class="login-list-item">Pipeline visual para acompanhar cada candidato até a etapa final.</div>
                </div>
            </div>
            <div class="login-card">
        """,
        unsafe_allow_html=True,
    )


def fechar_login_hero():
    st.markdown("</div></div>", unsafe_allow_html=True)


def obter_motor():
    return MotorBuscaSourcing()


def obter_opcoes_fontes_sourcing():
    motor = obter_motor()
    fontes_permitidas = {"linkedin", "doctoralia"}
    return {
        fonte_id: f"{dados['nome']} | {dados['categoria']}"
        for fonte_id, dados in motor.listar_fontes().items()
        if fonte_id in fontes_permitidas
    }


def normalizar_lista_texto(texto):
    itens = re.split(r"[,;\n]", texto or "")
    vistos = set()
    resultado = []
    for item in itens:
        valor = item.strip()
        if not valor:
            continue
        chave = valor.lower()
        if chave in vistos:
            continue
        vistos.add(chave)
        resultado.append(valor)
    return resultado


def combinar_tags(*listas):
    vistos = set()
    resultado = []
    for lista in listas:
        for item in lista or []:
            valor = str(item).strip()
            if not valor:
                continue
            chave = valor.lower()
            if chave in vistos:
                continue
            vistos.add(chave)
            resultado.append(valor)
    return resultado


def normalizar_localizacao_texto(localizacao):
    valor = (localizacao or "").strip()
    if not valor:
        return ""
    if valor.lower() == "remoto":
        return "Remoto"
    partes = [parte.strip() for parte in valor.split(",") if parte.strip()]
    if len(partes) >= 2:
        estado = partes[1].upper()[:2]
        return f"{partes[0]}/{estado}"
    return partes[0]


def montar_link_whatsapp(telefone, mensagem=None):
    numero = re.sub(r"\D", "", telefone or "")
    if not numero:
        return None
    texto = urllib.parse.quote_plus(mensagem or "Olá! Gostaria de falar sobre uma oportunidade.")
    return f"https://wa.me/{numero}?text={texto}"


def destacar_termos(texto, termos):
    destaque = texto
    for termo in sorted(combinar_tags(termos), key=len, reverse=True):
        padrao = re.compile(re.escape(termo), re.IGNORECASE)
        destaque = padrao.sub(lambda m: f"**{m.group(0)}**", destaque)
    return destaque


def obter_titulo_vaga(resultado_sourcing):
    if not resultado_sourcing:
        return "Nova vaga"
    cargo = resultado_sourcing.get("cargo", "Nova vaga")
    local = resultado_sourcing.get("localizacao_exibicao") or resultado_sourcing.get("localizacao") or "Remoto"
    return " | ".join(parte for parte in [cargo, local] if parte)


def inicializar_estado():
    padroes = {
        "autenticado": False,
        "usuario_id": None,
        "usuario_email": None,
        "usuario_nome": None,
        "usuario_admin": False,
        "menu_atual": "Construtor Inteligente",
        "nucleo_supabase": None,
        "mensagem_login": None,
        "resultado_sourcing": None,
        "radar_resultados": [],
        "vaga_ativa_id": None,
        "abordagem_pendente": None,
        "query_manual_editor": "",
        "contatos_temporarios": {},
        "input_localizacao": "",
    }

    for chave, valor in padroes.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


def obter_nucleo():
    if st.session_state.nucleo_supabase is None:
        st.session_state.nucleo_supabase = NucleoSupabase()
    return st.session_state.nucleo_supabase


def carregar_perfil_usuario(nucleo: NucleoSupabase, usuario_id: str):
    resposta = (
        nucleo.db.table("usuarios_perfis")
        .select("id, nome_completo, nivel_acesso, status")
        .eq("id", usuario_id)
        .limit(1)
        .execute()
    )
    if resposta.data:
        return resposta.data[0]
    return {}


def verificar_admin(usuario_id: str) -> bool:
    try:
        gestao = GestaoAdministrativa()
        gestao.validar_admin(usuario_id)
        return True
    except Exception:
        return False


def registrar_login(nucleo: NucleoSupabase):
    usuario = nucleo.sessao_atual
    if not usuario:
        raise ValueError("Sessão de utilizador não encontrada após o login.")

    perfil = carregar_perfil_usuario(nucleo, usuario.id)

    st.session_state.autenticado = True
    st.session_state.usuario_id = usuario.id
    st.session_state.usuario_email = getattr(usuario, "email", None)
    st.session_state.usuario_nome = perfil.get("nome_completo") or getattr(usuario, "email", "Utilizador")
    st.session_state.usuario_admin = verificar_admin(usuario.id)
    st.session_state.mensagem_login = None


def limpar_estado_autenticacao():
    for chave, valor in {
        "autenticado": False,
        "usuario_id": None,
        "usuario_email": None,
        "usuario_nome": None,
        "usuario_admin": False,
        "menu_atual": "Construtor Inteligente",
        "nucleo_supabase": None,
        "resultado_sourcing": None,
        "radar_resultados": [],
        "vaga_ativa_id": None,
        "abordagem_pendente": None,
        "query_manual_editor": "",
        "contatos_temporarios": {},
        "input_localizacao": "",
    }.items():
        st.session_state[chave] = valor


def fazer_logout():
    nucleo = st.session_state.get("nucleo_supabase")
    if nucleo is not None:
        try:
            nucleo.db.auth.sign_out()
        except Exception:
            pass

    limpar_estado_autenticacao()
    st.session_state.mensagem_login = "Sessão encerrada com sucesso."
    st.rerun()


def tela_login():
    renderizar_login_hero()
    st.markdown("### Acesso ao sistema")
    st.caption("Entre com a sua conta para continuar o fluxo de recrutamento.")

    if st.session_state.mensagem_login:
        st.info(st.session_state.mensagem_login)
        st.session_state.mensagem_login = None

    with st.form("form_login", clear_on_submit=False):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        enviado = st.form_submit_button("Entrar", use_container_width=True)

    if enviado:
        if not email or not senha:
            st.error("Preencha o e-mail e a senha para entrar.")
            return

        try:
            nucleo = NucleoSupabase()
            autenticado = nucleo.login(email=email, senha=senha)
            if not autenticado:
                mensagem_erro = nucleo.ultimo_erro_login or "Não foi possível autenticar. Verifique as credenciais informadas."
                st.error(f"Falha no login: {mensagem_erro}")
                return

            st.session_state.nucleo_supabase = nucleo
            registrar_login(nucleo)
            st.success("Login realizado com sucesso.")
            st.rerun()
        except Exception as erro:
            st.error(f"Erro ao realizar login: {erro}")
    fechar_login_hero()


def renderizar_sidebar():
    with st.sidebar:
        st.title("Navegação")
        st.caption(f"Utilizador: {st.session_state.usuario_nome}")
        if st.session_state.usuario_email:
            st.caption(f"E-mail: {st.session_state.usuario_email}")
        st.caption(f"Perfil: {'Admin' if st.session_state.usuario_admin else 'Recrutador'}")

        opcoes = [
            "Construtor Inteligente",
            "Radar de Talentos",
            "Pipeline de Vagas",
            "Automação de Abordagem",
        ]
        if st.session_state.usuario_admin:
            opcoes.append("Painel Admin")

        indice_atual = opcoes.index(st.session_state.menu_atual) if st.session_state.menu_atual in opcoes else 0
        st.session_state.menu_atual = st.radio(
            "Escolha uma tela",
            options=opcoes,
            index=indice_atual,
        )

        st.divider()
        if st.button("Sair", use_container_width=True):
            fazer_logout()


def criar_vaga_rapida(nucleo: NucleoSupabase, titulo, localizacao):
    localizacao = (localizacao or "").strip()
    cidade = "Remoto"
    estado = "RM"
    if localizacao and localizacao.lower() != "remoto":
        partes = [parte.strip() for parte in localizacao.split(",")]
        cidade = partes[0] if partes else localizacao
        estado = (partes[1].upper()[:2] if len(partes) > 1 else "SP")

    resposta = (
        nucleo.db.table("vagas")
        .insert(
            {
                "titulo": titulo,
                "cidade": cidade,
                "estado": estado,
                "status": "Aberta",
            }
        )
        .execute()
    )
    if resposta.data:
        return resposta.data[0]["id"]
    return None


def salvar_resultado_no_funil(nucleo: NucleoSupabase, vaga_id: str, resultado: dict, competencias: list):
    dados_perfil = {
        "nome": resultado["nome"],
        "titulo_profissional": resultado["titulo_profissional"],
        "empresa_atual": resultado["empresa_atual"],
        "localizacao": resultado["localizacao"],
        "email": resultado.get("email"),
        "telefone": resultado.get("telefone"),
        "whatsapp": resultado.get("telefone"),
        "url_perfil": resultado["url_perfil"],
        "fonte_origem": resultado["fonte_origem"],
    }
    return nucleo.salvar_candidato_pipeline(vaga_id, dados_perfil, competencias)


def atualizar_etapa_pipeline(nucleo: NucleoSupabase, vaga_id: str, candidato_id: str, nova_etapa: str):
    (
        nucleo.db.table("pipeline_recrutamento")
        .update({"etapa": nova_etapa})
        .eq("vaga_id", vaga_id)
        .eq("candidato_id", candidato_id)
        .execute()
    )


def montar_preview_construtor():
    motor = obter_motor()
    col_form, col_preview = st.columns([1.3, 0.9], gap="large")
    with col_form:
        abrir_layout_panel("Parâmetros da busca", "Defina profissão, geografia, competências e exclusões em um único bloco.")
        st.markdown('<div class="section-label">Dados da posição</div>', unsafe_allow_html=True)
        cargo_label = st.selectbox("Cargo Principal", options=list(CARGOS_DISPONIVEIS.keys()))
        cargo_personalizado = ""
        if cargo_label == "Outra profissão":
            cargo_personalizado = st.text_input(
                "Profissão personalizada",
                placeholder="Ex.: Enfermeiro do Trabalho, Fisioterapeuta, Psicólogo Organizacional",
            )
        localizacao = st.text_input(
            "Localização",
            key="input_localizacao",
            placeholder="Cidade, Estado ou Remoto",
        )
        cidades_vizinhas = normalizar_lista_texto(
            st.text_input(
                "Cidades vizinhas",
                placeholder="Ex.: Barueri, Osasco, Itapevi",
            )
        )
        abrangencia = st.radio(
            "Abrangência geográfica",
            options=["Somente local informado", "Raio aproximado de 15 km / cidades próximas"],
            horizontal=True,
        )

        st.markdown('<div class="section-label">Fontes</div>', unsafe_allow_html=True)
        opcoes_fontes = obter_opcoes_fontes_sourcing()
        fontes_selecionadas = st.multiselect(
            "Fontes de captação",
            options=list(opcoes_fontes.keys()),
            default=["linkedin", "doctoralia"],
            format_func=lambda fonte_id: opcoes_fontes[fonte_id],
        )

        st.markdown('<div class="section-label">Prompt da IA</div>', unsafe_allow_html=True)
        empresa_alvo = st.text_input("Empresa-alvo ou segmento", placeholder="Ex.: hospitais, indústria, clínicas ocupacionais")
        contexto_vaga = st.text_area(
            "Contexto da vaga",
            placeholder="Ex.: foco em PCMSO, atendimento ocupacional, operação regional e interface com SESMT.",
            height=90,
        )
        termos_prioritarios = normalizar_lista_texto(
            st.text_area(
                "Termos prioritários para ranking",
                placeholder="Ex.: PCMSO, ambulatório, enfermagem do trabalho, eSocial",
                height=90,
            )
        )
        col_pesquisa_1, col_pesquisa_2 = st.columns(2)
        with col_pesquisa_1:
            limite_por_fonte = st.slider("Resultados por fonte", min_value=2, max_value=8, value=4)
            usar_tavily = st.toggle("Enriquecer com Tavily", value=True)
        with col_pesquisa_2:
            max_enriquecimento = st.slider("Perfis com enriquecimento IA", min_value=1, max_value=6, value=4)
            usar_groq = st.toggle("Pontuar com Groq", value=True)

    inclusoes_final = combinar_tags(
        termos_prioritarios,
        [empresa_alvo.strip()] if empresa_alvo.strip() else [],
    )
    exclusoes_final = []
    cargo_id = CARGOS_DISPONIVEIS[cargo_label]
    incluir_cidades_proximas = abrangencia == "Raio aproximado de 15 km / cidades próximas"
    localizacao_limpa = (localizacao or st.session_state.get("input_localizacao") or "").strip()
    localizacao_exibicao = normalizar_localizacao_texto(localizacao_limpa)
    busca_preview = motor.gerar_busca_completa(
        id_cargo=cargo_id,
        local=localizacao_limpa,
        fontes_selecionadas=fontes_selecionadas,
        inclusoes_extras=inclusoes_final,
        exclusoes_extras=exclusoes_final,
        cargo_personalizado=cargo_personalizado.strip() if cargo_label == "Outra profissão" else None,
        incluir_cidades_proximas=incluir_cidades_proximas,
        cidades_vizinhas_extras=cidades_vizinhas,
    )

    preview_string = busca_preview.get("query_preview", "")
    with col_preview:
        abrir_layout_panel("Preview operacional", "Acompanhe a query final, revise as fontes e dispare a varredura quando estiver pronto.")
        renderizar_pills(
            [
                cargo_personalizado.strip() if cargo_label == "Outra profissão" else cargo_label,
                localizacao_exibicao or "Sem local definido",
                abrangencia,
                f"{len(cidades_vizinhas)} cidade(s) vizinha(s)" if cidades_vizinhas else None,
            ]
        )
        renderizar_pills(
            [
                empresa_alvo.strip() or None,
                "Tavily ativo" if usar_tavily else "Sem Tavily",
                "Groq ativo" if usar_groq else "Sem Groq",
            ]
        )
        mostrar_preview = st.toggle("Mostrar preview avançado", value=True)
        editar_manual = st.checkbox("Permitir edição manual da string", value=False)

        if not editar_manual:
            st.session_state.query_manual_editor = preview_string
        elif not st.session_state.query_manual_editor:
            st.session_state.query_manual_editor = preview_string

        query_operacional = preview_string
        if mostrar_preview:
            if editar_manual:
                query_operacional = st.text_area(
                    "Preview da string",
                    key="query_manual_editor",
                    height=220,
                )
            else:
                st.code(preview_string or "Defina os filtros para visualizar a string.", language=None)
        renderizar_pills(inclusoes_final[:6])
        iniciar_varredura = st.button("Iniciar Varredura", type="primary", use_container_width=True)

    return {
        "motor": motor,
        "cargo_label": cargo_personalizado.strip() if cargo_label == "Outra profissão" and cargo_personalizado.strip() else cargo_label,
        "cargo_id": cargo_id,
        "cargo_personalizado": cargo_personalizado.strip() if cargo_label == "Outra profissão" else None,
        "localizacao": localizacao_limpa,
        "localizacao_exibicao": localizacao_exibicao,
        "abrangencia": abrangencia,
        "incluir_cidades_proximas": incluir_cidades_proximas,
        "cidades_vizinhas_extras": cidades_vizinhas,
        "inclusoes": inclusoes_final,
        "exclusoes": exclusoes_final,
        "fontes_selecionadas": fontes_selecionadas,
        "empresa_alvo": empresa_alvo.strip(),
        "contexto_vaga": contexto_vaga.strip(),
        "termos_prioritarios": termos_prioritarios,
        "limite_por_fonte": limite_por_fonte,
        "max_enriquecimento": max_enriquecimento,
        "usar_tavily": usar_tavily,
        "usar_groq": usar_groq,
        "preview": busca_preview,
        "query_operacional": query_operacional.strip(),
        "iniciar_varredura": iniciar_varredura,
    }


def tela_construtor():
    abrir_container_pagina(
        "Construtor Inteligente de Busca",
        "Transforme critérios simples em buscas X-Ray avançadas com preview imediato e filtros mais claros.",
    )
    col_intro_1, col_intro_2, col_intro_3 = st.columns(3)
    with col_intro_1:
        abrir_soft_card("Cargo flexível", "Use o dicionário existente ou pesquise qualquer profissão livremente.")
    with col_intro_2:
        abrir_soft_card("Busca geográfica", "Amplie o alcance com cidades próximas quando fizer sentido para a vaga.")
    with col_intro_3:
        abrir_soft_card("Preview operacional", "Veja a query antes de disparar a varredura nas fontes selecionadas.")

    estado = montar_preview_construtor()
    if estado["iniciar_varredura"]:
        if not estado["cargo_label"] or estado["cargo_label"] == "Outra profissão":
            st.error("Informe uma profissão válida para iniciar a varredura.")
            return
        if not estado["fontes_selecionadas"]:
            st.error("Selecione pelo menos uma fonte de captação.")
            return

        preview = estado["preview"]
        if not preview or not preview.get("query_base"):
            st.error("Não foi possível gerar a string com os dados informados no prompt.")
            return

        radar = estado["motor"].buscar_resultados_higienizados(
            id_cargo=estado["cargo_id"],
            local=estado["localizacao"],
            fontes_selecionadas=estado["fontes_selecionadas"],
            inclusoes_extras=estado["inclusoes"],
            exclusoes_extras=[],
            cargo_personalizado=estado["cargo_personalizado"],
            incluir_cidades_proximas=estado["incluir_cidades_proximas"],
            cidades_vizinhas_extras=estado["cidades_vizinhas_extras"],
            contexto_vaga=estado["contexto_vaga"],
            empresa_alvo=estado["empresa_alvo"],
            termos_prioritarios=estado["termos_prioritarios"],
            limite_por_fonte=estado["limite_por_fonte"],
            usar_tavily=estado["usar_tavily"],
            usar_groq=estado["usar_groq"],
            max_enriquecimento=estado["max_enriquecimento"],
        )

        st.session_state.resultado_sourcing = {
            "cargo": estado["cargo_label"],
            "cargo_id": estado["cargo_id"],
            "cargo_personalizado": estado["cargo_personalizado"],
            "localizacao": estado["localizacao"],
            "localizacao_exibicao": estado["localizacao_exibicao"],
            "abrangencia": estado["abrangencia"],
            "cidades_vizinhas_extras": estado["cidades_vizinhas_extras"],
            "inclusoes": estado["inclusoes"],
            "exclusoes": estado["exclusoes"],
            "fontes_selecionadas": estado["fontes_selecionadas"],
            "empresa_alvo": estado["empresa_alvo"],
            "contexto_vaga": estado["contexto_vaga"],
            "termos_prioritarios": estado["termos_prioritarios"],
            "limite_por_fonte": estado["limite_por_fonte"],
            "max_enriquecimento": estado["max_enriquecimento"],
            "usar_tavily": estado["usar_tavily"],
            "usar_groq": estado["usar_groq"],
            "query_base": preview["query_base"],
            "query_preview": preview["query_preview"],
            "query_operacional": estado["query_operacional"] or preview["query_operacional"],
            "fontes": preview["fontes"],
            "busca_api_configurada": estado["motor"].busca_api_configurada(),
            "provedores_busca": estado["motor"].descrever_provedores_busca(),
        }
        st.session_state.radar_resultados = radar
        st.session_state.contatos_temporarios = {
            item["url_perfil"]: {
                "email": item.get("email"),
                "telefone": item.get("telefone"),
            }
            for item in radar
            if item.get("url_perfil")
        }
        st.session_state.menu_atual = "Radar de Talentos"
        st.success("Varredura iniciada. Abrindo o Radar de Talentos.")
        st.rerun()


def renderizar_resumo_busca(resultado_sourcing, total_encontrados):
    st.markdown('<div class="section-label">Resumo da busca</div>', unsafe_allow_html=True)
    st.write(
        f"Encontrados {total_encontrados} perfis para {resultado_sourcing['cargo']} "
        f"em {resultado_sourcing.get('localizacao_exibicao') or resultado_sourcing.get('localizacao') or 'qualquer localidade'}."
    )
    renderizar_pills(
        [
            f"Fontes ativas: {len(resultado_sourcing['fontes_selecionadas'])}",
            f"Abrangência: {resultado_sourcing.get('abrangencia', 'Somente local informado')}",
            f"Competências: {len(resultado_sourcing.get('inclusoes', []))}",
            f"Resultados/fonte: {resultado_sourcing.get('limite_por_fonte', 0)}",
            f"Cidades vizinhas: {len(resultado_sourcing.get('cidades_vizinhas_extras', []))}" if resultado_sourcing.get("cidades_vizinhas_extras") else None,
        ]
    )
    renderizar_pills(
        [
            f"Empresa-alvo: {resultado_sourcing.get('empresa_alvo')}" if resultado_sourcing.get("empresa_alvo") else None,
            "Tavily ativo" if resultado_sourcing.get("usar_tavily") else None,
            "Groq ativo" if resultado_sourcing.get("usar_groq") else None,
        ]
    )
    with st.expander("Ver string da busca", expanded=False):
        st.code(resultado_sourcing["query_operacional"], language=None)
        for item in resultado_sourcing["fontes"]:
            st.markdown(f"**{item['nome']}**")
            st.code(item["query"], language=None)
            if item.get("url"):
                st.link_button(
                    f"Abrir busca em {item['nome']}",
                    item["url"],
                    key=f'fonte_resumo_{item["id"]}',
                    use_container_width=True,
                )


def renderizar_gestao_vagas():
    nucleo = obter_nucleo()
    vagas = consultar_vagas_recrutador(nucleo, st.session_state.usuario_id)
    if vagas and not st.session_state.vaga_ativa_id:
        st.session_state.vaga_ativa_id = vagas[0]["id"]

    with st.expander("Vaga alvo do funil", expanded=not bool(vagas)):
        if vagas:
            mapa_vagas = {
                vaga["id"]: f'{vaga["titulo"]} | {vaga["cidade"]}/{vaga["estado"]}'
                for vaga in vagas
            }
            st.session_state.vaga_ativa_id = st.selectbox(
                "Selecione a vaga ativa",
                options=list(mapa_vagas.keys()),
                index=list(mapa_vagas.keys()).index(st.session_state.vaga_ativa_id)
                if st.session_state.vaga_ativa_id in mapa_vagas
                else 0,
                format_func=lambda vaga_id: mapa_vagas[vaga_id],
                key="vaga_ativa_selector",
            )
        else:
            st.info("Nenhuma vaga encontrada. Crie uma vaga rápida para salvar candidatos no funil.")

        resultado = st.session_state.get("resultado_sourcing")
        titulo_sugerido = obter_titulo_vaga(resultado)
        with st.form("form_vaga_rapida"):
            titulo = st.text_input("Título da vaga", value=titulo_sugerido)
            local = st.text_input("Local da vaga", value=(resultado or {}).get("localizacao_exibicao") or (resultado or {}).get("localizacao", "São Paulo, SP"))
            criar = st.form_submit_button("Criar vaga rápida", use_container_width=True)
        if criar:
            try:
                vaga_id = criar_vaga_rapida(nucleo, titulo, local)
                st.session_state.vaga_ativa_id = vaga_id
                st.success("Vaga criada com sucesso.")
                st.rerun()
            except Exception as erro:
                st.error(f"Erro ao criar vaga: {erro}")


def tela_radar():
    abrir_container_pagina(
        "Radar de Talentos",
        "Veja os perfis higienizados, compare aderência e envie para o funil somente os candidatos relevantes.",
    )
    resultado_sourcing = st.session_state.get("resultado_sourcing")
    radar_resultados = st.session_state.get("radar_resultados", [])

    if not resultado_sourcing:
        st.info("Inicie uma varredura no Construtor Inteligente para ver os resultados higienizados.")
        return

    if not resultado_sourcing.get("busca_api_configurada"):
        st.warning(
            "Nenhum provedor de busca real está configurado. O radar deixa de inventar candidatos e "
            "exibe apenas as queries e links por fonte. Configure no `.env` pelo menos um destes pares: "
            "`SERPER_API_KEY`, `SERPAPI_API_KEY` ou o legado `GOOGLE_CSE_API_KEY` + `GOOGLE_CSE_CX`."
        )
        renderizar_resumo_busca(resultado_sourcing, 0)
        st.info("Sem resultados reais disponíveis enquanto a API de busca não estiver configurada.")
        return

    if not radar_resultados:
        renderizar_resumo_busca(resultado_sourcing, 0)
        if resultado_sourcing.get("provedores_busca"):
            st.caption(f"Provedores ativos: {', '.join(resultado_sourcing['provedores_busca'])}")
        st.info("Nenhum perfil aderente foi encontrado com os filtros atuais. Tente ampliar fontes, localização ou palavras-chave.")
        return

    resultados_visiveis = [item for item in radar_resultados if item.get("status_radar") != "descartado"]
    renderizar_resumo_busca(resultado_sourcing, len(resultados_visiveis))
    renderizar_gestao_vagas()

    nucleo = obter_nucleo()
    colunas_radar = st.columns(2, gap="large")
    coluna_idx = 0
    for indice, candidato in enumerate(radar_resultados):
        if candidato.get("status_radar") == "descartado":
            continue
        with colunas_radar[coluna_idx]:
            abrir_candidate_card(candidato)
            with st.container(border=True):
                st.caption(
                    f'Fonte: {candidato["fonte_nome"]} | '
                    f'Domínio: {candidato.get("dominio", "não identificado")}'
                )
                if candidato.get("resumo_ia"):
                    st.markdown(f"**Resumo IA:** {candidato['resumo_ia']}")
                if candidato.get("motivo_aderencia"):
                    st.caption(f"Motivo de aderência: {candidato['motivo_aderencia']}")
                st.markdown(destacar_termos(candidato["snippet"], resultado_sourcing["inclusoes"]))
                st.markdown("**Contacto do candidato**")
                contato_1, contato_2 = st.columns(2)
                with contato_1:
                    st.caption(f"E-mail: {candidato.get('email') or 'não identificado'}")
                with contato_2:
                    st.caption(f"Telefone: {candidato.get('telefone') or 'não identificado'}")

                whatsapp_link = montar_link_whatsapp(
                    candidato.get("telefone"),
                    f"Olá {candidato.get('nome', '')}, gostaria de falar sobre uma oportunidade.",
                )
                contato_acoes = st.columns(2)
                with contato_acoes[0]:
                    if candidato.get("email"):
                        st.link_button(
                            "Abrir E-mail",
                            f"mailto:{candidato['email']}",
                            use_container_width=True,
                            key=f"email_radar_{indice}",
                        )
                with contato_acoes[1]:
                    if whatsapp_link:
                        st.link_button(
                            "Abrir WhatsApp",
                            whatsapp_link,
                            use_container_width=True,
                            key=f"whatsapp_radar_{indice}",
                        )
                if not candidato.get("email") and not candidato.get("telefone"):
                    st.caption("Contacto não capturado na fonte pública.")

                met1, met2 = st.columns(2)
                with met1:
                    st.metric("Aderência IA", candidato.get("score_ia", candidato.get("aderencia_score", 0)))
                with met2:
                    st.metric("Fonte", candidato["fonte_nome"])
                if candidato.get("registro_profissional"):
                    st.caption(f"Registro profissional: {candidato['registro_profissional']}")
                if candidato.get("sinais_publicos"):
                    with st.expander("Sinais públicos", expanded=False):
                        for sinal in candidato["sinais_publicos"]:
                            st.write(f"- {sinal}")
                if candidato.get("fontes_enriquecimento"):
                    with st.expander("Fontes de enriquecimento", expanded=False):
                        for fonte in candidato["fontes_enriquecimento"]:
                            if fonte.get("url"):
                                st.markdown(f"- [{fonte.get('titulo') or fonte.get('url')}]({fonte['url']})")
                            else:
                                st.write(f"- {fonte.get('titulo')}")

                acao1, acao2, acao3 = st.columns(3)
                with acao1:
                    if st.button("Salvar no Funil", key=f"salvar_funil_{indice}", use_container_width=True):
                        if not st.session_state.vaga_ativa_id:
                            st.error("Crie ou selecione uma vaga antes de salvar candidatos.")
                        else:
                            try:
                                candidato_id = salvar_resultado_no_funil(
                                    nucleo,
                                    st.session_state.vaga_ativa_id,
                                    candidato,
                                    resultado_sourcing["inclusoes"],
                                )
                                st.session_state.contatos_temporarios[candidato["url_perfil"]] = {
                                    "candidato_id": candidato_id,
                                    "email": candidato.get("email"),
                                    "telefone": candidato.get("telefone"),
                                }
                                candidato["status_radar"] = "salvo"
                                st.success("Candidato salvo no funil.")
                            except Exception as erro:
                                mensagem = str(erro)
                                if "row-level security" in mensagem.lower() or "42501" in mensagem:
                                    st.error(
                                        "Erro ao salvar no funil: a política RLS do Supabase está a bloquear a inserção em "
                                        "`candidatos` ou `pipeline_recrutamento`. Aplique o script "
                                        "`database/fix_rls_funil.sql` no banco e tente novamente."
                                    )
                                else:
                                    st.error(f"Erro ao salvar no funil: {erro}")
                with acao2:
                    if st.button("Descartar", key=f"descartar_{indice}", use_container_width=True):
                        candidato["status_radar"] = "descartado"
                        st.rerun()
                with acao3:
                    st.link_button(
                        "Abrir Perfil Original",
                        candidato["url_perfil"],
                        use_container_width=True,
                        key=f"abrir_{indice}",
                    )
        coluna_idx = 1 - coluna_idx


def consultar_vagas_recrutador(nucleo: NucleoSupabase, usuario_id: str):
    resposta = (
        nucleo.db.table("vagas")
        .select("id, titulo, cidade, estado, status")
        .eq("recrutador_id", usuario_id)
        .order("data_criacao", desc=True)
        .execute()
    )
    return resposta.data or []


def consultar_pipeline(nucleo: NucleoSupabase, vaga_ids):
    if not vaga_ids:
        return []

    resposta = (
        nucleo.db.table("pipeline_recrutamento")
        .select("id, vaga_id, candidato_id, etapa, data_atualizacao")
        .in_("vaga_id", vaga_ids)
        .order("data_atualizacao", desc=True)
        .execute()
    )
    return resposta.data or []


def consultar_candidatos(nucleo: NucleoSupabase, candidato_ids):
    if not candidato_ids:
        return []

    resposta = (
        nucleo.db.table("candidatos")
        .select("id, nome, titulo_profissional, empresa_atual, localizacao, email, telefone, whatsapp, url_perfil, fonte_origem")
        .in_("id", candidato_ids)
        .execute()
    )
    return resposta.data or []


def gerar_excel_pipeline(nucleo: NucleoSupabase, usuario_id: str):
    linhas = nucleo.consultar_pipeline_exportacao(usuario_id)
    if not linhas:
        return None
    df = pd.DataFrame(linhas)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="pipeline")
    buffer.seek(0)
    return buffer.getvalue()


def montar_kanban(nucleo: NucleoSupabase, usuario_id: str):
    vagas = consultar_vagas_recrutador(nucleo, usuario_id)
    if not vagas:
        return {etapa: [] for etapa in ETAPAS_KANBAN}, []

    vaga_por_id = {vaga["id"]: vaga for vaga in vagas}
    pipeline = consultar_pipeline(nucleo, list(vaga_por_id.keys()))
    candidato_ids = list({item["candidato_id"] for item in pipeline if item.get("candidato_id")})
    candidatos = consultar_candidatos(nucleo, candidato_ids)
    candidato_por_id = {candidato["id"]: candidato for candidato in candidatos}
    contatos_temporarios = st.session_state.get("contatos_temporarios", {})

    kanban = {etapa: [] for etapa in ETAPAS_KANBAN}
    for item in pipeline:
        etapa = item.get("etapa", "Mapeado")
        candidato = candidato_por_id.get(item.get("candidato_id"))
        vaga = vaga_por_id.get(item.get("vaga_id"))

        if not candidato or etapa not in kanban:
            continue

        kanban[etapa].append(
            {
                "candidato_id": candidato.get("id"),
                "vaga_id": item.get("vaga_id"),
                "nome": candidato.get("nome", "Sem nome"),
                "titulo_profissional": candidato.get("titulo_profissional") or "Título não informado",
                "empresa_atual": candidato.get("empresa_atual") or "Empresa não informada",
                "localizacao": candidato.get("localizacao") or "Localização não informada",
                "fonte_origem": candidato.get("fonte_origem") or "Origem não informada",
                "url_perfil": candidato.get("url_perfil"),
                "vaga_titulo": vaga.get("titulo") if vaga else "Vaga não identificada",
                "email": candidato.get("email") or (contatos_temporarios.get(candidato.get("url_perfil")) or {}).get("email"),
                "telefone": candidato.get("telefone") or (contatos_temporarios.get(candidato.get("url_perfil")) or {}).get("telefone"),
                "whatsapp": candidato.get("whatsapp") or candidato.get("telefone") or (contatos_temporarios.get(candidato.get("url_perfil")) or {}).get("telefone"),
            }
        )

    return kanban, vagas


def avancar_etapa(atual):
    fluxo = {
        "Mapeado": "Contatado",
        "Contatado": "Triagem",
        "Triagem": "Aprovado",
    }
    return fluxo.get(atual)


def exibir_card_candidato(candidato: dict, etapa_atual: str):
    abrir_candidate_card(candidato)
    renderizar_pills([candidato["vaga_titulo"], candidato["localizacao"], candidato["fonte_origem"]])
    st.caption(f"E-mail: {candidato.get('email') or 'não identificado'}")
    st.caption(f"Telefone: {candidato.get('telefone') or 'não identificado'}")
    contato_col_1, contato_col_2 = st.columns(2)
    with contato_col_1:
        if candidato.get("email"):
            st.link_button(
                "Abrir e-mail",
                f"mailto:{candidato['email']}",
                use_container_width=True,
                key=f'email_pipeline_{candidato["candidato_id"]}_{etapa_atual}',
            )
    with contato_col_2:
        whatsapp_link = montar_link_whatsapp(candidato.get("whatsapp") or candidato.get("telefone"))
        if whatsapp_link:
            st.link_button(
                "Abrir WhatsApp",
                whatsapp_link,
                use_container_width=True,
                key=f'whatsapp_pipeline_{candidato["candidato_id"]}_{etapa_atual}',
            )
    if candidato.get("url_perfil"):
        st.link_button("Abrir perfil", candidato["url_perfil"], use_container_width=True, key=f'perfil_{candidato["candidato_id"]}_{etapa_atual}')

    nucleo = obter_nucleo()
    proxima = avancar_etapa(etapa_atual)
    if proxima:
        if st.button(
            f"Mover para {ETAPAS_VISUAIS[proxima]}",
            key=f'mover_{candidato["candidato_id"]}_{etapa_atual}',
            use_container_width=True,
        ):
            try:
                atualizar_etapa_pipeline(nucleo, candidato["vaga_id"], candidato["candidato_id"], proxima)
                if proxima == "Contatado":
                    st.session_state.abordagem_pendente = candidato
                    st.session_state.menu_atual = "Automação de Abordagem"
                st.rerun()
            except Exception as erro:
                st.error(f"Erro ao mover candidato: {erro}")

    if etapa_atual != "Recusado":
        if st.button(
            "Marcar como Recusado",
            key=f'recusar_{candidato["candidato_id"]}_{etapa_atual}',
            use_container_width=True,
        ):
            try:
                atualizar_etapa_pipeline(nucleo, candidato["vaga_id"], candidato["candidato_id"], "Recusado")
                st.rerun()
            except Exception as erro:
                st.error(f"Erro ao recusar candidato: {erro}")
    st.divider()


def tela_pipeline():
    abrir_container_pagina(
        "Pipeline de Vagas",
        "Organize os talentos por etapa e mova candidatos entre os estágios do processo.",
    )

    try:
        nucleo = obter_nucleo()
        kanban, vagas = montar_kanban(nucleo, st.session_state.usuario_id)

        if not vagas:
            st.info("Nenhuma vaga foi encontrada. Use o Radar de Talentos para criar uma vaga rápida e alimentar o funil.")
            return

        st.caption(f"Vagas encontradas: {len(vagas)}")
        arquivo_excel = gerar_excel_pipeline(nucleo, st.session_state.usuario_id)
        if arquivo_excel:
            st.download_button(
                "Exportar pipeline para Excel",
                data=arquivo_excel,
                file_name="pipeline_recrutamento.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        colunas = st.columns(len(ETAPAS_KANBAN))

        for indice, etapa in enumerate(ETAPAS_KANBAN):
            with colunas[indice]:
                candidatos = kanban.get(etapa, [])
                st.markdown(
                    f"""
                    <div class="kanban-column">
                        <h4>{ETAPAS_VISUAIS[etapa]}</h4>
                        <p>{len(candidatos)} candidato(s)</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if not candidatos:
                    st.info("Sem candidatos nesta etapa.")
                    continue
                for candidato in candidatos:
                    exibir_card_candidato(candidato, etapa)
    except Exception as erro:
        st.error(f"Erro ao carregar o pipeline: {erro}")


def gerar_mensagem_abordagem(template, candidato, cargo):
    mensagem = template
    substituicoes = {
        "[NOME]": candidato.get("nome", "Profissional"),
        "[EMPRESA]": candidato.get("empresa_atual", "empresa atual"),
        "[CARGO]": cargo or candidato.get("titulo_profissional", "oportunidade"),
    }
    for chave, valor in substituicoes.items():
        mensagem = mensagem.replace(chave, valor)
    return mensagem


def tela_automacao():
    abrir_container_pagina(
        "Automação de Abordagem",
        "Padronize o primeiro contacto com templates, variáveis dinâmicas e atalhos para envio.",
    )

    candidato = st.session_state.get("abordagem_pendente")
    resultado = st.session_state.get("resultado_sourcing") or {}
    if not candidato:
        st.info("Mova um candidato para Contatados no Pipeline para preparar a abordagem.")
        return

    col_contexto, col_editor = st.columns([0.85, 1.15], gap="large")
    with col_contexto:
        abrir_layout_panel("Contexto do candidato", "Revise rapidamente o perfil antes de personalizar a mensagem.")
        abrir_candidate_card(candidato)
        renderizar_pills([candidato["empresa_atual"], candidato["fonte_origem"], resultado.get("cargo")])
    with col_editor:
        abrir_layout_panel("Mensagem de abordagem", "Escolha um template e ajuste a comunicação antes de enviar.")
        template_nome = st.selectbox("Template de mensagem", options=list(TEMPLATES_ABORDAGEM.keys()))
        mensagem_base = gerar_mensagem_abordagem(
            TEMPLATES_ABORDAGEM[template_nome],
            candidato,
            resultado.get("cargo"),
        )
        mensagem_final = st.text_area("Mensagem final", value=mensagem_base, height=220)

        col1, col2 = st.columns(2)
        with col1:
            if candidato.get("telefone"):
                texto_whats = urllib.parse.quote_plus(mensagem_final)
                st.link_button(
                    "Abrir WhatsApp Web",
                    f'https://wa.me/{candidato["telefone"]}?text={texto_whats}',
                    use_container_width=True,
                )
            else:
                st.info("Telefone não disponível para este candidato.")
        with col2:
            if candidato.get("email"):
                assunto = urllib.parse.quote_plus(f'Convite para conversar sobre oportunidade: {resultado.get("cargo", "vaga")}')
                corpo = urllib.parse.quote_plus(mensagem_final)
                st.link_button(
                    "Abrir E-mail",
                    f'mailto:{candidato["email"]}?subject={assunto}&body={corpo}',
                    use_container_width=True,
                )
            else:
                st.info("E-mail não disponível para este candidato.")

    if st.button("Concluir abordagem", use_container_width=True):
        st.session_state.abordagem_pendente = None
        st.success("Contexto de abordagem concluído.")
        st.rerun()


def tela_admin():
    abrir_container_pagina(
        "Painel Admin",
        "Cadastre recrutadores e mantenha a operação centralizada em um único painel.",
    )

    if not st.session_state.usuario_admin:
        st.error("Acesso restrito a administradores.")
        return

    with st.form("form_cadastro_recrutador", clear_on_submit=True):
        nome_completo = st.text_input("Nome completo")
        email = st.text_input("E-mail do recrutador")
        senha = st.text_input("Senha provisória", type="password")
        enviado = st.form_submit_button("Cadastrar recrutador", use_container_width=True)

    if enviado:
        if not nome_completo or not email or not senha:
            st.error("Preencha nome, e-mail e senha para cadastrar o recrutador.")
            return

        try:
            gestao = GestaoAdministrativa()
            novo_usuario_id = gestao.cadastrar_recrutador(
                admin_id=st.session_state.usuario_id,
                email=email.strip(),
                senha=senha,
                nome_completo=nome_completo.strip(),
            )
            st.success(f"Recrutador cadastrado com sucesso. ID do utilizador: {novo_usuario_id}")
        except Exception as erro:
            st.error(f"Erro ao cadastrar recrutador: {erro}")


def tela_principal():
    renderizar_sidebar()
    renderizar_topbar()

    if st.session_state.menu_atual == "Construtor Inteligente":
        tela_construtor()
    elif st.session_state.menu_atual == "Radar de Talentos":
        tela_radar()
    elif st.session_state.menu_atual == "Pipeline de Vagas":
        tela_pipeline()
    elif st.session_state.menu_atual == "Automação de Abordagem":
        tela_automacao()
    elif st.session_state.menu_atual == "Painel Admin":
        tela_admin()


def main():
    inicializar_estado()
    aplicar_estilos_globais()

    if st.session_state.autenticado:
        nucleo = st.session_state.get("nucleo_supabase")
        if nucleo is None or not nucleo.esta_autenticado():
            limpar_estado_autenticacao()
            st.session_state.mensagem_login = "A sessão expirou ou foi reiniciada. Entre novamente."
            st.rerun()

    if not st.session_state.autenticado:
        tela_login()
        return

    tela_principal()


if __name__ == "__main__":
    main()
