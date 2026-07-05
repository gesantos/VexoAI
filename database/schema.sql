create extension if not exists "uuid-ossp";

-- 1. NÚCLEO DE USUÁRIOS E PERFIS
create table usuarios_perfis (
    id uuid references auth.users on delete cascade primary key,
    nome_completo text not null,
    nivel_acesso text default 'Recrutador' check (nivel_acesso in ('Admin', 'Recrutador')),
    status text default 'Ativo' check (status in ('Ativo', 'Bloqueado')),
    data_criacao timestamptz default now()
);

create or replace function public.handle_novo_usuario() returns trigger as $$
begin
  insert into public.usuarios_perfis (id, nome_completo, nivel_acesso)
  values (new.id, coalesce(new.raw_user_meta_data->>'nome_completo', 'Usuário Padrão'), 'Recrutador');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users for each row execute procedure public.handle_novo_usuario();

-- 2. TABELAS DE NEGÓCIO (RH)
create table vagas (
    id uuid primary key default gen_random_uuid(),
    recrutador_id uuid references usuarios_perfis(id) not null default auth.uid(),
    titulo text not null,
    cidade text not null,
    estado varchar(2) not null,
    status text default 'Aberta' check (status in ('Aberta', 'Pausada', 'Fechada')),
    data_criacao timestamptz default now()
);

create table candidatos (
    id uuid primary key default gen_random_uuid(),
    nome text not null,
    titulo_profissional text,
    empresa_atual text,
    localizacao text,
    email text,
    telefone text,
    whatsapp text,
    url_perfil text not null unique,
    fonte_origem text not null,
    data_captura timestamptz default now()
);

create table competencias (
    id uuid primary key default gen_random_uuid(),
    nome text not null unique,
    tipo text check (tipo in ('Norma Regulamentadora', 'Software', 'Especialidade'))
);

create table candidato_competencias (
    candidato_id uuid references candidatos(id) on delete cascade,
    competencia_id uuid references competencias(id) on delete cascade,
    primary key (candidato_id, competencia_id)
);

create table pipeline_recrutamento (
    id uuid primary key default gen_random_uuid(),
    vaga_id uuid references vagas(id) on delete cascade,
    candidato_id uuid references candidatos(id) on delete cascade,
    etapa text default 'Mapeado' check (etapa in ('Mapeado', 'Contatado', 'Triagem', 'Aprovado', 'Recusado')),
    data_atualizacao timestamptz default now(),
    unique (vaga_id, candidato_id)
);

-- 3. POLÍTICAS DE SEGURANÇA (RLS)
alter table vagas enable row level security;
alter table usuarios_perfis enable row level security;
alter table candidatos enable row level security;
alter table competencias enable row level security;
alter table candidato_competencias enable row level security;
alter table pipeline_recrutamento enable row level security;

create policy "Admins veem todas as vagas" on vagas for all to authenticated using ((select nivel_acesso from usuarios_perfis where id = auth.uid()) = 'Admin');
create policy "Recrutadores gerenciam as suas vagas" on vagas for all to authenticated using (recrutador_id = auth.uid());
create policy "Leitura publica de perfis" on usuarios_perfis for select to authenticated using (true);
create policy "Edicao de perfis apenas por Admin" on usuarios_perfis for update to authenticated using ((select nivel_acesso from usuarios_perfis where id = auth.uid()) = 'Admin');

create policy "Perfis de candidatos podem ser lidos por autenticados"
on candidatos for select to authenticated
using (true);

create policy "Perfis de candidatos podem ser inseridos por autenticados"
on candidatos for insert to authenticated
with check (true);

create policy "Perfis de candidatos podem ser atualizados por autenticados"
on candidatos for update to authenticated
using (true)
with check (true);

create policy "Competencias podem ser lidas por autenticados"
on competencias for select to authenticated
using (true);

create policy "Competencias podem ser inseridas por autenticados"
on competencias for insert to authenticated
with check (true);

create policy "Relacionamentos candidato_competencias podem ser lidos por autenticados"
on candidato_competencias for select to authenticated
using (true);

create policy "Relacionamentos candidato_competencias podem ser inseridos por autenticados"
on candidato_competencias for insert to authenticated
with check (true);

create policy "Pipeline pode ser lido por recrutadores da vaga ou admin"
on pipeline_recrutamento for select to authenticated
using (
  exists (
    select 1
    from vagas
    where vagas.id = pipeline_recrutamento.vaga_id
      and (
        vagas.recrutador_id = auth.uid()
        or (select nivel_acesso from usuarios_perfis where id = auth.uid()) = 'Admin'
      )
  )
);

create policy "Pipeline pode ser inserido por recrutadores da vaga ou admin"
on pipeline_recrutamento for insert to authenticated
with check (
  exists (
    select 1
    from vagas
    where vagas.id = pipeline_recrutamento.vaga_id
      and (
        vagas.recrutador_id = auth.uid()
        or (select nivel_acesso from usuarios_perfis where id = auth.uid()) = 'Admin'
      )
  )
);

create policy "Pipeline pode ser atualizado por recrutadores da vaga ou admin"
on pipeline_recrutamento for update to authenticated
using (
  exists (
    select 1
    from vagas
    where vagas.id = pipeline_recrutamento.vaga_id
      and (
        vagas.recrutador_id = auth.uid()
        or (select nivel_acesso from usuarios_perfis where id = auth.uid()) = 'Admin'
      )
  )
)
with check (
  exists (
    select 1
    from vagas
    where vagas.id = pipeline_recrutamento.vaga_id
      and (
        vagas.recrutador_id = auth.uid()
        or (select nivel_acesso from usuarios_perfis where id = auth.uid()) = 'Admin'
      )
  )
);
