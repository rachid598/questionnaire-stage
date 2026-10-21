-- À coller dans Supabase > SQL Editor > Run
create table if not exists public.reponses (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  inscription_parents text not null check (inscription_parents in ('Oui','Non')),
  inscription_soi text not null check (inscription_soi in ('Oui','Non')),
  inscription_professeurs text not null check (inscription_professeurs in ('Oui','Non')),
  presence text not null check (presence in ('Oui','Non')),
  absence_raison text check (absence_raison in ('Rendez-vous médical','Pas motivé(e)','Raison personnelle')),
  ambiance text not null check (ambiance in ('À l’aise, l’ambiance était agréable','Pas à l’aise, j’avais du mal avec le groupe')),
  activites text not null check (activites in ('Oui','Non')),
  progres text not null check (progres in ('Oui','Non')),
  renouveler text not null check (renouveler in ('Oui','Non')),
  revenir text not null check (revenir in ('Oui','Non')),
  modifier text not null check (modifier in ('Oui','Non')),
  expliquer text check (char_length(expliquer) <= 1500),
  check ((presence = 'Non') = (absence_raison is not null)),
  check ((modifier = 'Oui') = (expliquer is not null))
);

alter table public.reponses enable row level security;

-- Envoi autorisé uniquement le 22/10/2026 entre 09h00 et 13h00 (heure de Paris). Aucune lecture publique.
drop policy if exists "envoi pendant la fenetre" on public.reponses;
create policy "envoi pendant la fenetre" on public.reponses
  for insert to anon
  with check (now() >= '2026-10-22T09:00:00+02:00'::timestamptz and now() < '2026-10-22T13:00:00+02:00'::timestamptz);

grant insert on public.reponses to anon;
