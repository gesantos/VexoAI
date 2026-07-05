alter table if exists candidatos add column if not exists email text;
alter table if exists candidatos add column if not exists telefone text;
alter table if exists candidatos add column if not exists whatsapp text;

alter table if exists candidatos enable row level security;
alter table if exists competencias enable row level security;
alter table if exists candidato_competencias enable row level security;
alter table if exists pipeline_recrutamento enable row level security;

drop policy if exists "Perfis de candidatos podem ser lidos por autenticados" on candidatos;
create policy "Perfis de candidatos podem ser lidos por autenticados"
on candidatos for select to authenticated
using (true);

drop policy if exists "Perfis de candidatos podem ser inseridos por autenticados" on candidatos;
create policy "Perfis de candidatos podem ser inseridos por autenticados"
on candidatos for insert to authenticated
with check (true);

drop policy if exists "Perfis de candidatos podem ser atualizados por autenticados" on candidatos;
create policy "Perfis de candidatos podem ser atualizados por autenticados"
on candidatos for update to authenticated
using (true)
with check (true);

drop policy if exists "Competencias podem ser lidas por autenticados" on competencias;
create policy "Competencias podem ser lidas por autenticados"
on competencias for select to authenticated
using (true);

drop policy if exists "Competencias podem ser inseridas por autenticados" on competencias;
create policy "Competencias podem ser inseridas por autenticados"
on competencias for insert to authenticated
with check (true);

drop policy if exists "Relacionamentos candidato_competencias podem ser lidos por autenticados" on candidato_competencias;
create policy "Relacionamentos candidato_competencias podem ser lidos por autenticados"
on candidato_competencias for select to authenticated
using (true);

drop policy if exists "Relacionamentos candidato_competencias podem ser inseridos por autenticados" on candidato_competencias;
create policy "Relacionamentos candidato_competencias podem ser inseridos por autenticados"
on candidato_competencias for insert to authenticated
with check (true);

drop policy if exists "Pipeline pode ser lido por recrutadores da vaga ou admin" on pipeline_recrutamento;
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

drop policy if exists "Pipeline pode ser inserido por recrutadores da vaga ou admin" on pipeline_recrutamento;
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

drop policy if exists "Pipeline pode ser atualizado por recrutadores da vaga ou admin" on pipeline_recrutamento;
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
