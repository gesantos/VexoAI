import json
import re
import urllib.parse
from urllib.parse import urlparse

import requests

from .config import (
    GOOGLE_CSE_API_KEY,
    GOOGLE_CSE_CX,
    GROQ_API_KEY,
    SERPAPI_API_KEY,
    SERPER_API_KEY,
    TAVILY_API_KEY,
)


class MotorBuscaSourcing:
    def __init__(self):
        self.dicionario = {
            "medico_trabalho": {
                "sinonimos": ["Médico do Trabalho", "Medicina do Trabalho", "Coordenador PCMSO"],
                "obrigatorios": ["PCMSO", "ASO", "SESMT"],
                "exclusoes": ["Pediatra", "Cirurgião", "Plantonista"],
            },
            "tecnico_seguranca": {
                "sinonimos": ["Técnico de Segurança do Trabalho", "TST"],
                "obrigatorios": ["PGR", "CIPA", "EPI"],
                "exclusoes": ["Vigilante", "Porteiro"],
            },
        }
        self.localidades_proximas = {
            "são paulo": ["Osasco", "Santo André", "São Bernardo do Campo", "São Caetano do Sul", "Guarulhos", "Taboão da Serra"],
            "rio de janeiro": ["Niterói", "Duque de Caxias", "Nova Iguaçu", "São João de Meriti"],
            "campinas": ["Valinhos", "Vinhedo", "Sumaré", "Paulínia"],
            "cotia": ["Barueri", "Itapevi", "Jandira", "Osasco", "Carapicuíba", "Taboão da Serra", "Vargem Grande Paulista", "Embu das Artes"],
            "santo andré": ["São Bernardo do Campo", "São Caetano do Sul", "Mauá", "Diadema"],
            "guarulhos": ["São Paulo", "Arujá", "Itaquaquecetuba"],
            "curitiba": ["São José dos Pinhais", "Colombo", "Pinhais", "Araucária"],
            "belo horizonte": ["Contagem", "Betim", "Nova Lima"],
            "porto alegre": ["Canoas", "Novo Hamburgo", "São Leopoldo"],
        }
        self.senioridades = {
            "Júnior": ["Júnior", "Junior", "Assistente", "Trainee"],
            "Pleno": ["Pleno", "Analista"],
            "Sênior": ["Sênior", "Senior", "Especialista"],
            "Coordenador": ["Coordenador", "Coordenação", "Liderança"],
        }
        self.fontes = {
            "linkedin": {
                "nome": "LinkedIn",
                "alvo": "site:br.linkedin.com/in/",
                "categoria": "Redes Profissionais",
                "url_base": "https://br.linkedin.com/in/",
            },
            "lattes": {
                "nome": "Plataforma Lattes",
                "alvo": "site:buscatextual.cnpq.br",
                "categoria": "Bases Académicas e Governamentais",
                "url_base": "https://buscatextual.cnpq.br/buscatextual/visualizacv.do?id=",
            },
            "doctoralia": {
                "nome": "Doctoralia",
                "alvo": "site:doctoralia.com.br",
                "categoria": "Plataformas Médicas e de Saúde",
                "url_base": "https://www.doctoralia.com.br/",
            },
            "bancos_curriculos": {
                "nome": "Bancos de Currículos",
                "alvo": "(site:trabalhabrasil.com.br OR site:catho.com.br/profissionais/)",
                "categoria": "Portais de Vagas e Currículos",
                "url_base": "https://www.trabalhabrasil.com.br/",
            },
            "arquivos_publicos": {
                "nome": "Arquivos Públicos",
                "alvo": "(filetype:pdf OR filetype:doc OR filetype:docx)",
                "categoria": "Busca por Arquivos Públicos",
                "url_base": "https://www.google.com/search?q=",
            },
        }
        self.empresas = [
            "Vexo Saúde",
            "Grupo Labor",
            "Clínica Integrar",
            "SEGMED Brasil",
            "Vida Ocupacional",
            "PrevCare",
            "Ambimed",
            "Segura RH",
        ]
        self.nomes = [
            "Ana Paula Ribeiro",
            "Bruno Martins",
            "Carla Menezes",
            "Daniel Rocha",
            "Eduarda Lima",
            "Felipe Nascimento",
            "Gabriela Torres",
            "Henrique Alves",
            "Isabela Costa",
            "João Pedro Santos",
            "Larissa Moura",
            "Marcos Vinícius",
            "Natália Freitas",
            "Otávio Barros",
            "Priscila Campos",
            "Rafael Duarte",
        ]

    def busca_api_configurada(self):
        return bool(self.listar_provedores_busca_configurados())

    def listar_provedores_busca_configurados(self):
        provedores = []
        if SERPER_API_KEY:
            provedores.append("serper")
        if SERPAPI_API_KEY:
            provedores.append("serpapi")
        if GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX:
            provedores.append("google_cse")
        return provedores

    def descrever_provedores_busca(self):
        nomes = {
            "google_cse": "Google CSE",
            "serper": "Serper",
            "serpapi": "SerpAPI",
        }
        return [nomes[provedor] for provedor in self.listar_provedores_busca_configurados()]

    def tavily_configurado(self):
        return bool(TAVILY_API_KEY)

    def groq_configurado(self):
        return bool(GROQ_API_KEY)

    def _limpar_lista(self, itens):
        resultado = []
        vistos = set()
        for item in itens or []:
            valor = str(item).strip()
            if not valor:
                continue
            chave = valor.lower()
            if chave in vistos:
                continue
            vistos.add(chave)
            resultado.append(valor)
        return resultado

    def _compor_clausula(self, lista, operador="OR", negacao=False):
        lista = self._limpar_lista(lista)
        if not lista:
            return ""
        termos = [f'"{t}"' for t in lista]
        bloco = f"({f' {operador} '.join(termos)})"
        return f"-{bloco}" if negacao else bloco

    def _clausula_localizacao(self, local):
        local = (local or "").strip()
        if not local:
            return ""
        if local.lower() == "remoto":
            return '("Remoto" OR "Home Office" OR "Híbrido")'
        return f'"{local}"'

    def listar_fontes(self):
        return self.fontes

    def obter_ids_fontes(self):
        return list(self.fontes.keys())

    def obter_dados_cargo(self, id_cargo):
        return self.dicionario.get(id_cargo, {})

    def obter_sinonimos_cargo(self, id_cargo):
        return self.obter_dados_cargo(id_cargo).get("sinonimos", [])

    def construir_dados_cargo_personalizado(self, cargo):
        cargo = (cargo or "").strip()
        if not cargo:
            return {}
        return {
            "sinonimos": [cargo],
            "obrigatorios": [],
            "exclusoes": [],
        }

    def resolver_id_cargo(self, cargo):
        cargo_normalizado = (cargo or "").strip().lower()
        if not cargo_normalizado:
            return None

        for cargo_id, dados in self.dicionario.items():
            termos = [cargo_id.replace("_", " ")] + dados.get("sinonimos", [])
            if any(cargo_normalizado == termo.strip().lower() for termo in termos):
                return cargo_id

        for cargo_id, dados in self.dicionario.items():
            termos = [cargo_id.replace("_", " ")] + dados.get("sinonimos", [])
            if any(cargo_normalizado in termo.strip().lower() for termo in termos):
                return cargo_id
        return None

    def _normalizar_chave_localidade(self, local):
        local = (local or "").strip()
        if not local:
            return ""
        return local.split(",")[0].strip().lower()

    def expandir_localizacao(self, local, incluir_proximas=False, cidades_vizinhas_extras=None):
        local = (local or "").strip()
        if not local:
            return []
        if local.lower() == "remoto":
            return ["Remoto", "Home Office", "Híbrido"]

        base = local.split(",")[0].strip()
        localidades = [base]
        if incluir_proximas:
            proximas = self.localidades_proximas.get(self._normalizar_chave_localidade(local), [])
            localidades.extend(proximas)
        localidades.extend(cidades_vizinhas_extras or [])
        return self._limpar_lista(localidades)

    def gerar_string(
        self,
        id_cargo=None,
        local="",
        senioridade=None,
        inclusoes_extras=None,
        exclusoes_extras=None,
        cargo_personalizado=None,
        incluir_cidades_proximas=False,
        cidades_vizinhas_extras=None,
    ):
        dados = self.dicionario.get(id_cargo) if id_cargo else None
        if not dados and cargo_personalizado:
            dados = self.construir_dados_cargo_personalizado(cargo_personalizado)
        if not dados:
            return ""

        cargos = self._compor_clausula(dados["sinonimos"])
        skills = self._compor_clausula(dados["obrigatorios"] + (inclusoes_extras or []))
        senioridade_clausula = self._compor_clausula(self.senioridades.get(senioridade, []))
        localizacoes = self.expandir_localizacao(
            local,
            incluir_proximas=incluir_cidades_proximas,
            cidades_vizinhas_extras=cidades_vizinhas_extras,
        )
        localizacao_clausula = self._compor_clausula(localizacoes) if localizacoes else ""
        exclusao = self._compor_clausula(dados["exclusoes"] + (exclusoes_extras or []), negacao=True)

        partes = [parte for parte in [cargos, skills, senioridade_clausula, localizacao_clausula] if parte]
        if not partes:
            return ""

        query = " AND ".join(partes)
        if exclusao:
            query += f" {exclusao}"
        return query

    def gerar_string_xray(self, query_base, fontes_selecionadas=None):
        fontes_ativas = fontes_selecionadas or self.obter_ids_fontes()
        alvos = [self.fontes[fonte_id]["alvo"] for fonte_id in fontes_ativas if fonte_id in self.fontes]
        if not query_base:
            return ""
        if not alvos:
            return query_base
        alvos_clausula = f"({' OR '.join(alvos)})" if len(alvos) > 1 else alvos[0]
        return f"{alvos_clausula} {query_base}"

    def construir_query_segura(
        self,
        cargo,
        local,
        nrs=None,
        senioridade=None,
        exclusoes_extras=None,
        fontes_selecionadas=None,
    ):
        cargo_id = self.resolver_id_cargo(cargo)
        if not cargo_id:
            return ""
        query_base = self.gerar_string(
            id_cargo=cargo_id,
            local=local,
            senioridade=senioridade,
            inclusoes_extras=nrs or [],
            exclusoes_extras=exclusoes_extras or [],
            cargo_personalizado=cargo if not cargo_id else None,
        )
        return self.gerar_string_xray(query_base, fontes_selecionadas)

    def gerar_query_por_fonte(self, query_base, fonte_id):
        fonte = self.fontes.get(fonte_id)
        if not fonte or not query_base:
            return ""
        return f'{fonte["alvo"]} {query_base}'

    def obter_urls_raspagem(self, query_base, fontes_selecionadas=None):
        urls = {}
        fontes_ativas = fontes_selecionadas or self.obter_ids_fontes()
        for fonte_id in fontes_ativas:
            fonte = self.fontes.get(fonte_id)
            if not fonte:
                continue
            query_fonte = self.gerar_query_por_fonte(query_base, fonte_id)
            urls[fonte_id] = f"https://www.google.com/search?q={urllib.parse.quote_plus(query_fonte)}"
        return urls

    def gerar_busca_completa(
        self,
        id_cargo=None,
        local="",
        senioridade=None,
        fontes_selecionadas=None,
        inclusoes_extras=None,
        exclusoes_extras=None,
        query_manual=None,
        cargo_personalizado=None,
        incluir_cidades_proximas=False,
        cidades_vizinhas_extras=None,
    ):
        fontes_ativas = fontes_selecionadas or self.obter_ids_fontes()
        query_base = self.gerar_string(
            id_cargo=id_cargo,
            local=local,
            senioridade=senioridade,
            inclusoes_extras=inclusoes_extras,
            exclusoes_extras=exclusoes_extras,
            cargo_personalizado=cargo_personalizado,
            incluir_cidades_proximas=incluir_cidades_proximas,
            cidades_vizinhas_extras=cidades_vizinhas_extras,
        )
        query_preview = self.gerar_string_xray(query_base, fontes_ativas)
        query_operacional = (query_manual or "").strip() or query_preview
        if not query_base:
            return {}

        resultados = []
        urls = self.obter_urls_raspagem(query_base, fontes_ativas)

        for fonte_id in fontes_ativas:
            fonte = self.fontes.get(fonte_id)
            if not fonte:
                continue
            resultados.append(
                {
                    "id": fonte_id,
                    "nome": fonte["nome"],
                    "categoria": fonte["categoria"],
                    "query": self.gerar_query_por_fonte(query_base, fonte_id),
                    "url": urls.get(fonte_id),
                }
            )

        return {
            "query_base": query_base,
            "query_preview": query_preview,
            "query_operacional": query_operacional,
            "fontes": resultados,
        }

    def _extrair_contactos(self, texto):
        texto = texto or ""
        email = None
        telefone = None

        match_email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", texto, re.IGNORECASE)
        if match_email:
            email = match_email.group(0)

        match_tel = re.search(r"(\+?55\s?)?(\(?\d{2}\)?\s?)?\d{4,5}[-\s]?\d{4}", texto)
        if match_tel:
            telefone = re.sub(r"\D", "", match_tel.group(0))
            if telefone and not telefone.startswith("55"):
                telefone = f"55{telefone}"

        return email, telefone

    def _extrair_registro_profissional(self, texto):
        texto = texto or ""
        padroes = [
            r"\bCRM[\s:/-]*[A-Z]{0,2}[\s-]*\d{3,10}\b",
            r"\bCOREN[\s:/-]*[A-Z]{0,2}[\s-]*\d{3,10}\b",
            r"\bCREA[\s:/-]*[A-Z]{0,2}[\s-]*\d{3,10}\b",
        ]
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

    def _extrair_empresa(self, texto):
        texto = texto or ""
        padroes = [
            r"(?:na|no|em)\s+([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇáàâãéèêíìîóòôõúùûç&\.\-\s]{2,60})",
            r"empresa atual[:\s]+([A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇáàâãéèêíìîóòôõúùûç&\.\-\s]{2,60})",
        ]
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                return match.group(1).strip(" .,-")
        return None

    def _normalizar_nome(self, titulo):
        titulo = re.sub(r"\s*[-|–].*$", "", (titulo or "")).strip()
        if len(titulo.split()) > 8:
            return "Profissional identificado"
        return titulo or "Profissional identificado"

    def _texto_resultado(self, item):
        partes = [
            item.get("title", ""),
            item.get("snippet", ""),
        ]
        pagemap = item.get("pagemap") or {}
        for chave in ["metatags", "person", "hcard"]:
            for bloco in pagemap.get(chave, []):
                if isinstance(bloco, dict):
                    partes.extend([str(valor) for valor in bloco.values() if valor])
        return " ".join(partes)

    def _resultado_elegivel(self, texto, sinonimos, palavras_chave, exclusoes):
        texto_normalizado = (texto or "").lower()
        if exclusoes and any(termo.lower() in texto_normalizado for termo in exclusoes):
            return False

        if sinonimos and not any(termo.lower() in texto_normalizado for termo in sinonimos):
            return False

        if palavras_chave and not any(termo.lower() in texto_normalizado for termo in palavras_chave):
            return False

        return True

    def _buscar_google_cse(self, query, limite=5):
        resposta = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": GOOGLE_CSE_API_KEY,
                "cx": GOOGLE_CSE_CX,
                "q": query,
                "num": min(max(limite, 1), 10),
            },
            timeout=20,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        return dados.get("items", [])

    def _buscar_serper(self, query, limite=5):
        resposta = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "q": query,
                "num": min(max(limite, 1), 10),
                "gl": "br",
                "hl": "pt-br",
            },
            timeout=20,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        itens = []
        for item in dados.get("organic", []) or []:
            itens.append(
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                }
            )
        return itens

    def _buscar_serpapi(self, query, limite=5):
        resposta = requests.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google",
                "q": query,
                "num": min(max(limite, 1), 10),
                "google_domain": "google.com.br",
                "hl": "pt-br",
                "gl": "br",
                "api_key": SERPAPI_API_KEY,
            },
            timeout=20,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        itens = []
        for item in dados.get("organic_results", []) or []:
            itens.append(
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                }
            )
        return itens

    def _buscar_resultados_provedor(self, provedor, query, limite):
        if provedor == "google_cse":
            return self._buscar_google_cse(query, limite=limite)
        if provedor == "serper":
            return self._buscar_serper(query, limite=limite)
        if provedor == "serpapi":
            return self._buscar_serpapi(query, limite=limite)
        return []

    def _buscar_tavily_contexto(
        self,
        candidato,
        cargo_referencia=None,
        empresa_alvo=None,
        contexto_vaga=None,
        termos_prioritarios=None,
        max_resultados=3,
    ):
        if not self.tavily_configurado():
            return []

        partes_query = [
            candidato.get("nome"),
            candidato.get("titulo_profissional"),
            candidato.get("empresa_atual"),
            cargo_referencia,
            empresa_alvo,
            " ".join(termos_prioritarios or []),
        ]
        query = " ".join(parte for parte in partes_query if parte)
        resposta = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "advanced",
                "max_results": max(1, min(max_resultados, 5)),
                "include_answer": False,
                "include_raw_content": False,
                "topic": "general",
            },
            timeout=25,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        resultados = []
        for item in dados.get("results", []) or []:
            resultados.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content"),
                }
            )
        return resultados

    def _extrair_json_llm(self, texto):
        texto = (texto or "").strip()
        if not texto:
            return {}
        if texto.startswith("```"):
            texto = re.sub(r"^```(?:json)?", "", texto).strip()
            texto = re.sub(r"```$", "", texto).strip()
        try:
            return json.loads(texto)
        except Exception:
            match = re.search(r"\{[\s\S]*\}", texto)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    return {}
        return {}

    def _analisar_candidato_com_groq(
        self,
        candidato,
        cargo_referencia=None,
        contexto_vaga=None,
        empresa_alvo=None,
        termos_prioritarios=None,
        contexto_web=None,
    ):
        if not self.groq_configurado():
            return {}

        prompt = {
            "cargo_referencia": cargo_referencia,
            "contexto_vaga": contexto_vaga,
            "empresa_alvo": empresa_alvo,
            "termos_prioritarios": termos_prioritarios or [],
            "candidato": {
                "nome": candidato.get("nome"),
                "titulo_profissional": candidato.get("titulo_profissional"),
                "empresa_atual": candidato.get("empresa_atual"),
                "localizacao": candidato.get("localizacao"),
                "snippet": candidato.get("snippet"),
                "fonte": candidato.get("fonte_nome"),
                "aderencia_base": candidato.get("aderencia_score"),
                "email": candidato.get("email"),
                "telefone": candidato.get("telefone"),
                "registro_profissional": candidato.get("registro_profissional"),
            },
            "contexto_web": contexto_web or [],
        }
        resposta = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é um assistente de recrutamento. Analise o perfil recebido e devolva APENAS JSON com as chaves: "
                            "score_aderencia, resumo_ia, motivo_aderencia, recomendacao."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(prompt, ensure_ascii=False),
                    },
                ],
            },
            timeout=30,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        conteudo = (
            (((dados.get("choices") or [{}])[0]).get("message") or {}).get("content")
            or ""
        )
        return self._extrair_json_llm(conteudo)

    def _enriquecer_resultado(
        self,
        candidato,
        cargo_referencia=None,
        contexto_vaga=None,
        empresa_alvo=None,
        termos_prioritarios=None,
        usar_tavily=True,
        usar_groq=True,
    ):
        contexto_web = []
        if usar_tavily and self.tavily_configurado():
            try:
                contexto_web = self._buscar_tavily_contexto(
                    candidato,
                    cargo_referencia=cargo_referencia,
                    empresa_alvo=empresa_alvo,
                    contexto_vaga=contexto_vaga,
                    termos_prioritarios=termos_prioritarios,
                )
            except Exception:
                contexto_web = []

        if contexto_web:
            candidato["fontes_enriquecimento"] = [
                {
                    "titulo": item.get("title"),
                    "url": item.get("url"),
                }
                for item in contexto_web[:3]
            ]
            candidato["sinais_publicos"] = [
                (item.get("content") or "")[:220]
                for item in contexto_web[:2]
                if item.get("content")
            ]
        else:
            candidato["fontes_enriquecimento"] = []
            candidato["sinais_publicos"] = []

        if usar_groq and self.groq_configurado():
            try:
                analise = self._analisar_candidato_com_groq(
                    candidato,
                    cargo_referencia=cargo_referencia,
                    contexto_vaga=contexto_vaga,
                    empresa_alvo=empresa_alvo,
                    termos_prioritarios=termos_prioritarios,
                    contexto_web=contexto_web,
                )
            except Exception:
                analise = {}
        else:
            analise = {}

        score_ia = analise.get("score_aderencia", candidato.get("aderencia_score", 0) * 10)
        try:
            score_ia = float(score_ia)
            if 0 <= score_ia <= 1:
                score_ia *= 100
            elif 0 < score_ia <= 10:
                score_ia *= 10
        except Exception:
            score_ia = candidato.get("aderencia_score", 0) * 10
        candidato["score_ia"] = round(score_ia, 1)
        candidato["resumo_ia"] = analise.get(
            "resumo_ia",
            candidato.get("snippet", "Sem resumo disponível."),
        )
        candidato["motivo_aderencia"] = analise.get(
            "motivo_aderencia",
            "Perfil encontrado com aderência inicial baseada nos termos da busca.",
        )
        candidato["recomendacao_ia"] = analise.get(
            "recomendacao",
            "Validar perfil original e decidir se segue para o funil.",
        )
        return candidato

    def buscar_resultados_higienizados(
        self,
        id_cargo=None,
        local="",
        fontes_selecionadas=None,
        inclusoes_extras=None,
        exclusoes_extras=None,
        limite_por_fonte=3,
        cargo_personalizado=None,
        incluir_cidades_proximas=False,
        cidades_vizinhas_extras=None,
        contexto_vaga=None,
        empresa_alvo=None,
        termos_prioritarios=None,
        usar_tavily=True,
        usar_groq=True,
        max_enriquecimento=4,
    ):
        if not self.busca_api_configurada():
            return []

        dados_cargo = self.obter_dados_cargo(id_cargo) if id_cargo else {}
        if not dados_cargo and cargo_personalizado:
            dados_cargo = self.construir_dados_cargo_personalizado(cargo_personalizado)
        if not dados_cargo:
            return []

        localizacao = (local or "").strip() or "Brasil"
        palavras_chave = self._limpar_lista(dados_cargo["obrigatorios"] + (inclusoes_extras or []))
        fontes_ativas = fontes_selecionadas or self.obter_ids_fontes()
        sinonimos = self._limpar_lista(dados_cargo["sinonimos"])
        exclusoes = self._limpar_lista(dados_cargo["exclusoes"] + (exclusoes_extras or []))

        resultados = []
        urls_vistos = set()
        provedores = self.listar_provedores_busca_configurados()
        for fonte_id in fontes_ativas:
            fonte = self.fontes.get(fonte_id)
            if not fonte:
                continue
            query_fonte = self.gerar_query_por_fonte(
                self.gerar_string(
                    id_cargo=id_cargo,
                    local=localizacao,
                    inclusoes_extras=inclusoes_extras,
                    exclusoes_extras=exclusoes_extras,
                    cargo_personalizado=cargo_personalizado,
                    incluir_cidades_proximas=incluir_cidades_proximas,
                    cidades_vizinhas_extras=cidades_vizinhas_extras,
                ),
                fonte_id,
            )
            itens = []
            for provedor in provedores:
                try:
                    itens = self._buscar_resultados_provedor(provedor, query_fonte, limite=limite_por_fonte)
                    if itens:
                        break
                except Exception:
                    continue
            if not itens:
                continue

            for indice_local, item in enumerate(itens):
                texto_completo = self._texto_resultado(item)
                if not self._resultado_elegivel(texto_completo, sinonimos, palavras_chave, exclusoes):
                    continue

                email, telefone = self._extrair_contactos(texto_completo)
                registro_profissional = self._extrair_registro_profissional(texto_completo)
                url = item.get("link")
                if not url or url in urls_vistos:
                    continue
                urls_vistos.add(url)
                dominio = urlparse(url).netloc if url else ""
                resultados.append(
                    {
                        "id": f"{fonte_id}_{indice_local}_{abs(hash(url or texto_completo))}",
                        "nome": self._normalizar_nome(item.get("title", "")),
                        "titulo_profissional": item.get("title", "") or dados_cargo["sinonimos"][0],
                        "empresa_atual": self._extrair_empresa(texto_completo) or "Não identificado",
                        "fonte_id": fonte_id,
                        "fonte_nome": fonte["nome"],
                        "fonte_categoria": fonte["categoria"],
                        "fonte_origem": fonte["nome"],
                        "snippet": item.get("snippet", "") or "Sem resumo disponível.",
                        "url_perfil": url,
                        "localizacao": localizacao,
                        "palavras_chave": palavras_chave,
                        "email": email,
                        "telefone": telefone,
                        "registro_profissional": registro_profissional,
                        "status_radar": "novo",
                        "dominio": dominio,
                        "aderencia_score": sum(
                            1 for termo in self._limpar_lista(sinonimos + palavras_chave) if termo.lower() in texto_completo.lower()
                        ),
                    }
                )

        resultados.sort(key=lambda item: item.get("aderencia_score", 0), reverse=True)
        for indice, candidato in enumerate(resultados):
            if indice >= max_enriquecimento:
                candidato["score_ia"] = candidato.get("aderencia_score", 0) * 10
                candidato["resumo_ia"] = candidato.get("snippet", "Sem resumo disponível.")
                candidato["motivo_aderencia"] = "Pontuação inicial baseada na busca e nos termos encontrados."
                candidato["recomendacao_ia"] = "Abrir o perfil original para análise detalhada."
                candidato["fontes_enriquecimento"] = []
                candidato["sinais_publicos"] = []
                continue
            self._enriquecer_resultado(
                candidato,
                cargo_referencia=cargo_personalizado or (dados_cargo.get("sinonimos") or [""])[0],
                contexto_vaga=contexto_vaga,
                empresa_alvo=empresa_alvo,
                termos_prioritarios=termos_prioritarios or palavras_chave,
                usar_tavily=usar_tavily,
                usar_groq=usar_groq,
            )
        return resultados

    def candidato_tem_contato_ou_registro(self, candidato):
        return bool(
            (candidato or {}).get("email")
            or (candidato or {}).get("telefone")
            or (candidato or {}).get("registro_profissional")
        )
