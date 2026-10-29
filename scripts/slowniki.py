"""Strona Słowniki: pojęcia dla naukowców i dla biura oraz poziomy TRL.

Zapisuje slowniki.html w katalogu głównym projektu.
"""
import html as h
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import biuro as bz  # noqa: E402
import dopasowanie as dp  # noqa: E402

DLA_NAUKOWCOW = [
    ("Nabór", "Ogłoszenie konkursu w programie Horizon Europe z tematami i terminami. Dane pochodzą z SEDIA."),
    ("Temat naboru", "Konkretny zakres w naborze, do którego składa się wniosek."),
    ("Dopasowanie", "Lista osób z dowodami z publikacji. To sugestia dla biura, a nie decyzja o udziale."),
    ("Dowód", "Publikacja lub inne źródło, na którym oparto dopasowanie."),
    ("Zaproszenie", "Wiadomość biura z opisem projektu i rolą. Odpowiedź możesz dać bez logowania."),
    ("Propozycja", "Propozycja współpracownika zgłoszona przez Ciebie. Biuro ją sprawdza, zanim wyśle zaproszenie."),
    ("Rola w projekcie", "Funkcja w zespole, np. wykonawca, kierownik zadania, ekspert doradczy."),
    ("Profil", "Dane z BaDAP i OpenAlex. Zgłoś korektę, jeśli coś jest nieaktualne lub błędne."),
    ("Poziom TRL", "Dojrzałość technologii lub rezultatu. Dotyczy projektu, nie osoby. Legenda poniżej."),
]

DLA_BIURA = [
    ("Etap projektu", "Wnioski, Odrzucone wnioski, W trakcie realizacji albo Zakończone."),
    ("Status naboru", "Planowany, otwarty, zamknięty albo sprawdzić. Opisuje sam konkurs, nie projekt."),
    ("Pula", "Projekty WI albo Unijne. Przeciągnij kafel na pulę, żeby ją zmienić."),
    ("Opiekun projektu", "Osoba z biura przypisana do projektu przez koordynatora."),
    ("Zatwierdzenie", "Zaproszenie zatwierdza inna osoba niż autor szkicu (W11). Serwer tego pilnuje."),
    ("Szkic, zatwierdzone, wysłane", "Kolejne stany zaproszenia. Wysyłka otwiera wiadomość w programie pocztowym."),
    ("Pokrycie wymogów", "Ile tematów naboru ma potwierdzenie w tematyce osoby. To orientacja, nie ocena kompetencji."),
    ("Zleceniodawca", "Organizacja finansująca projekt, np. Komisja Europejska."),
    ("Kierownik (WI)", "Pracownik WI wskazany jako kierownik projektu. Może różnić się od kierownika w umowie."),
]


def terms(items):
    return '<dl class="sl-list">' + "".join(f"<div><dt>{h.escape(t)}</dt><dd>{h.escape(d)}</dd></div>" for t, d in items) + "</dl>"


def trl_block():
    return bz.trl_legend().replace('<details class="trl-legend"><summary>Legenda poziomów TRL</summary>', '<div class="trl-legend">', 1).replace("</details>", "</div>")


def render():
    head, header, theme_js = dp.site_parts()
    head = head.replace("Dopasowanie do naboru · Mapa badawcza WI AGH", "Słowniki · Mapa badawcza WI AGH")
    tabs = dp.nav_html("slowniki")
    hero = """  <section class="hero-simple">
    <div class="eyebrow">Słowniki</div>
    <h1 class="hero-title">Słownik pojęć</h1>
    <p class="hero-sub">Najważniejsze pojęcia z aplikacji. Osobno dla naukowców i dla biura projektowego.</p>
  </section>
"""
    body = f"""<section class="sl-sec" aria-labelledby="sl-n">
    <h2 id="sl-n">Dla naukowców</h2>
    {terms(DLA_NAUKOWCOW)}
  </section>
  <section class="sl-sec" aria-labelledby="sl-b" data-role-only="biuro">
    <h2 id="sl-b">Dla biura projektowego</h2>
    {terms(DLA_BIURA)}
  </section>
  <section class="sl-sec" aria-labelledby="sl-t">
    <h2 id="sl-t">Poziomy TRL</h2>
    <p class="pj-small">Skala dojrzałości technologii od 1 do 9. Poziom przypisuje się konkretnej technologii lub rezultatowi wniosku, nie osobie.</p>
    {trl_block()}
  </section>"""
    css = """<style>
.sl-sec { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.2rem; margin-top: 1rem; }
.sl-sec h2 { font-size: 1.1rem; margin: 0 0 .6rem; }
.sl-list { margin: 0; display: grid; gap: .6rem; }
.sl-list > div { border-top: 1px solid var(--border); padding-top: .5rem; }
.sl-list dt { font-weight: 600; color: var(--text); }
.sl-list dd { margin: .15rem 0 0; color: var(--text2); font-size: .92rem; }
</style>"""
    return f"""{head}
{css}
</head>
<body>
{header}
{tabs}

<main class="container">
  {hero}
  {body}
</main>
{theme_js}
</body>
</html>
"""


def main():
    out = ROOT / "slowniki.html"
    out.write_text(render(), encoding="utf-8")
    print(f"zapisano: {out}")


if __name__ == "__main__":
    main()
