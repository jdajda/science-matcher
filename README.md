# Mapa badawcza — Wydział Informatyki AGH

Statystyczna, interaktywna mapa badawcza pracowników Wydziału Informatyki AGH: osoby, obszary zainteresowań badawczych, publikacje (BadAP) oraz graf współpracy. Całość to **jeden statyczny plik `index.html`** — brak zależności, builda i backendu.

## Funkcje

| Zakładka | Opis |
|---|---|
| **Pracownicy** | Lista 175 pracowników z wyszukiwarką (nazwisko, imię, słowo kluczowe), filtrowaniem wg obszarów badawczych i domyślnym sortowaniem „najlepiej publikujący" oraz opcjami: liczba publikacji, nazwisko, ostatnia publikacja. Kliknięcie karty otwiera panel profilu: stopień, jednostka, e-mail, linki do profili SKOS i BadAP, obszary badawcze, słowa kluczowe, wybrane publikacje i współautorzy (wewnętrzni/zewnętrzni). |
| **Obszary badawcze** | 22 obszary badawcze: opis potencjału badawczego, 88 klikalnych osiągnięć i najważniejsze publikacje obszaru, ranking pracowników oraz udziały procentowe. Kliknięcie osiągnięcia wysuwa panel z opisem, streszczeniem, zespołem (linki do profili) i publikacjami (linki do prac). |
| **Dobierz zespół** | Wklejasz tytuł lub opis projektu (streszczenie z zadaniami), a system porównuje tekst z tytułami publikacji, słowami kluczowymi i obszarami badawczymi — otrzymujesz ranking najlepiej dopasowanych osób. |
| **Graf powiązań** | Interaktywny graf (canvas): węzły pracowników i obszarów, krawędzie współpracy naukowej (wspólne publikacje) i przynależności do obszarów. Cztery układy do wyboru, filtrowanie minimalnej liczby wspólnych publikacji, wyszukiwanie osoby, reset widoku. |

## Dane

- Źródła: **BadAP AGH** (badap.agh.edu.pl) oraz strona Wydziału (informatyka.agh.edu.pl)
- Stan danych: 01.10.2026, wygenerowane: 2026-10-02
- Zapis: dane w osobnym pliku **`data.json`** (kopia 1:1 osadzona w `index.html` w bloku `<script id="app-data" type="application/json">`, dzięki czemu strona działa też przy otwarciu pliku lokalnie)
- Zakres: 175 pracowników (115 z publikacjami), 8265 publikacji, 22 obszary badawcze

Każdy pracownik ma: identyfikator, imię i nazwisko, stopień naukowy, kategorię (dydaktyczno-naukowi / inżynieryjno-techniczni / administracyjni / emerytowani), jednostkę, e-mail, linki SKOS i BadAP, liczbę publikacji, przypisane obszary z wagami, słowa kluczowe, tytuły publikacji oraz listę współautorów z wagą i oznaczeniem współpracowników zewnętrznych.

### Filtrowanie i sortowanie pracowników

Lista jest domyślnie ustawiona na **„Najlepiej publikujący"**, a nie alfabetycznie. Zaznaczenie obszaru na pasku nad listą zawęża ją i od razu porządkuje według aktywności właśnie w tych obszarach:

- bez zaznaczenia — liczba publikacji łącznie (Malawski 734, Kitowski 547, Grzanka 515)
- „Bezpieczeństwo i kryptografia" — suma wag w tym obszarze (Ogiela Lidia 180, Ogiela Urszula 87, Służalec 22)
- „Obliczenia kwantowe" — 3 osoby (Rycerz, Długopolski, Capała)
- „Obliczenia kwantowe" + „HPC" — 35 osób, suma wag z obu obszarów

Filtr działa niezależnie od trybu sortowania, a chipsy można łączyć (logika „lub" — ktoś jest w jednym z zaznaczonych obszarów). Pozostałe tryby: „Liczba publikacji łącznie", „Nazwisko (A–Z)", „Ostatnia publikacja". Wszystkie są stabilne — przy remisie rozstrzyga nazwisko.

### Wskaźniki aktywności

Wagi publikacji zapisane w danych to suma punktów za przypisanie prac do obszaru — wartość wewnętrzna, bezużyteczna dla czytelnika. Interfejs pokazuje zawsze **procenty**:

- **Ranking kadry** (lista w obszarze) — udział pracownika w aktywności obszaru względem jego lidera; 100% = najbardziej aktywny badacz w danym obszarze. Idzie w parze z paskiem i tooltipem.
- **Lista obszarów** (lewy panel) — udział obszaru w aktywności całego wydziału, np. „17 os. · 17% aktywności”. Pasek obok pokazuje skalę względem największego obszaru.
- **Panel „Publikacje w tym obszarze"** — udział pracownika w tym obszarze, w procentach.

Wartości w procentach liczone są na bieżąco z wag, więc nie ma w UI żadnej surowej liczby wewnętrznej.

### Linki do publikacji

Tytuły publikacji w profilu pracownika, w profilu obszaru i w sekcji „Ważniejsze publikacje" są odnośnikami do właściwych prac. Mapa `pubLinks` (klucz = znormalizowany tytuł) została rozwiązana offline przez `tools/resolve_dois.py` (OpenAlex + Crossref) i trzymana w `data.json`:

- **475 tytułów** → link bezpośredni: DOI (`https://doi.org/...`) lub strona artykułu
- **274 tytuły** → link zastępczy do wyszukiwarki Google Scholar z dokładnym cytowaniem tytułu (przypadki bez DOI, np. polskie czasopisma, materiały konferencyjne)

Dopasowanie akceptowane jest tylko przy zgodności ≥ 0,82, żeby nie podlinkować cudzej pracy. Wygenerowanie mapy od nowa:

```sh
python3 tools/resolve_dois_parallel.py   # pobiera DOI do .doi_cache.json
python3 tools/build_publinks.py          # zapisuje pubLinks do data.json + index.html
python3 tools/build_achievements.py      # strukturyzuje osiągnięcia (zespół + publikacje)
python3 tools/extract_data.py            # wyrównuje data.json z index.html
```

### Układy grafu

Wybór w polu „Układ" zmienia rozmieszczenie węzłów bez zmiany danych:

| Układ | Jak wygląda | Symulacja |
|---|---|---|
| **Siłowy (spiralny)** | pierścień obszarów, pracownicy rozproszeni wokół własnego obszaru — domyślny, „organiczny” | tak |
| **Grupowy wg obszarów** | każdy obszar to osobna wyspa w siatce komórek; wyspy sortowane malejąco po liczbie osób, więc duże i małe obszary nie zjadają miejsca | nie |
| **Tarczowy (kołowy)** | pracownicy leżą na łukach w sektorach swoich obszarów, współpraca rysowana jako łuki koncentryczne zamiast prostych odcinków | nie |
| **Siatka uporządkowana** | kwadratowa siatka dla wszystkich węzłów, odstęp liczony z realnych promieni; obszary w górnych wierszach, potem pracownicy wg liczby publikacji | nie |

Trzy uporządkowane układy są „sztywne": węzły siedzą dokładnie na wyznaczonych pozycjach (kolizje i sprężyny nie rozrzucają ich), a przeciąganie działa natychmiast. Siłowy układ jest symulacją dynamiczną. Po zmianie układu graf automatycznie dopasowuje powiększenie, a legendą podpowiada, co widać.

Etykiety rysowane są w osobnej pętli z wykrywaniem kolizji: podpis pojawia się tylko wtedy, gdy nie nachodzi na inny. Etykiety pracowników pojawiają się dopiero przy wyraźnym przybliżeniu (k > 2.2) albo po wskazaniu węzła, dzięki czemu graf pozostaje czytelny.

### Osiągnięcia badawcze

Wszystkie 88 osiągnięć (22 obszary × 4) ma strukturę: nazwa, typ, opis, streszczenie, powiązany zespół oraz publikacje. Zespół i publikacje są wiązane automatycznie (`tools/build_achievements.py`) na podstawie rzeczywistych danych — pracownicy muszą należeć do danego obszaru, a tytuły publikacji pochodzą z rekordów BadAP. Każdy skrypt jest idempotentny, więc można go uruchamiać wielokrotnie.

Testy (headless Chrome):

| Skrypt | Co sprawdza |
|---|---|
| `smoke_test.py` | render strony, 22 obszary, linki do publikacji, brak błędów JS |
| `test_achievements.py` | klika przez wszystkie 88 osiągnięć, sprawdza panel, zespół i publikacje |
| `test_layouts.py` | przełącza 4 układy grafu, pozycje węzłów, przeciąganie, filtry obszarów |
| `test_staff_sort.py` | filtr obszarów w każdym trybie sortowania, domyślna kolejność, brak wag na kartach |
| `measure_spacing.py` | odległości między węzłami i nachodzenie na siebie w każdym układzie |
| `shoot_layouts.py` | zrzuca każdy układ grafu do PNG w `/tmp/layout_shots` (ocena czytelności) |

## Struktura plików

| Plik | Rola |
|---|---|
| `index.html` | cała aplikacja: dane (JSON), style, logika (vanilla JS), graf na canvas |
| `data.json` | te same dane w osobnym pliku — źródło do dalszej edycji i analizy |
| `tools/` | skrypty pomocnicze: DOI, synchronizacja danych, testy headless, zrzuty układów grafu |

## Uruchomienie

```sh
open index.html
```

Wystarczy otworzyć plik `index.html` w przeglądarce (Chrome, Firefox, Safari). Brak wymagań — aplikacja działa w pełni offline.

Repozytorium: [github.com/jdajda/science-matcher](https://github.com/jdajda/science-matcher)
