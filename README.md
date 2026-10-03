# Mapa badawcza — Wydział Informatyki AGH

Statystyczna, interaktywna mapa badawcza pracowników Wydziału Informatyki AGH: osoby, obszary zainteresowań badawczych, publikacje (BadAP) oraz graf współpracy. Całość to **jeden statyczny plik `index.html`** — brak zależności, builda i backendu.

## Funkcje

| Zakładka | Opis |
|---|---|
| **Pracownicy** | Lista 175 pracowników z wyszukiwarką (nazwisko, imię, słowo kluczowe), filtrowaniem wg obszarów badawczych i sortowaniem (nazwisko / liczba publikacji / ostatnia publikacja). Kliknięcie karty otwiera panel profilu: stopień, jednostka, e-mail, linki do profili SKOS i BadAP, obszary badawcze, słowa kluczowe, wybrane publikacje i współautorzy (wewnętrzni/zewnętrzni). |
| **Obszary badawcze** | 22 obszary badawcze z paskiem aktywności, rankingu pracowników wg liczby publikacji w obszarze i listą kluczowych prac. |
| **Dobierz zespół** | Wklejasz tytuł lub opis projektu (streszczenie z zadaniami), a system porównuje tekst z tytułami publikacji, słowami kluczowymi i obszarami badawczymi — otrzymujesz ranking najlepiej dopasowanych osób. |
| **Graf powiązań** | Interaktywny graf siłowy (canvas): węzły pracowników i obszarów, krawędzie współpracy naukowej (wspólne publikacje) i przynależności do obszarów. Filtrowanie minimalnej liczby wspólnych publikacji, wyszukiwanie osoby, reset widoku. |

## Dane

- Źródła: **BadAP AGH** (badap.agh.edu.pl) oraz strona Wydziału (informatyka.agh.edu.pl)
- Stan danych: 01.10.2026, wygenerowane: 2026-10-02
- Zapis: dane osadzone jako JSON w bloku `<script id="app-data" type="application/json">` wewnątrz `index.html`
- Zakres: 175 pracowników (115 z publikacjami), 8265 publikacji, 22 obszary badawcze

Każdy pracownik ma: identyfikator, imię i nazwisko, stopień naukowy, kategorię (dydaktyczno-naukowi / inżynieryjno-techniczni / administracyjni / emerytowani), jednostkę, e-mail, linki SKOS i BadAP, liczbę publikacji, przypisane obszary z wagami, słowa kluczowe, tytuły publikacji oraz listę współautorów z wagą i oznaczeniem współpracowników zewnętrznych.

## Uruchomienie

```sh
open index.html
```

Wystarczy otworzyć plik `index.html` w przeglądarce (Chrome, Firefox, Safari). Brak wymagań — aplikacja działa w pełni offline.

## Struktura

```
index.html   # cała aplikacja: dane (JSON), style, logika (vanilla JS), graf na canvas
```

Repozytorium: [github.com/jdajda/science-matcher](https://github.com/jdajda/science-matcher)
