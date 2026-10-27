# Role i dostęp: podział widoków

Stan na 27.10.2026 (po uproszczeniu menu). Decyzje: logowanie przez SSO AGH, ok. 6 użytkowników biura (w tym 1 koordynator), naukowiec nie loguje się, chyba że przez SSO.

## Role

| Rola | Kto | Logowanie | Dostęp |
|---|---|---|---|
| **Gość** | partnerzy zewnętrzni, osoby spoza uczelni | brak | publiczny katalog |
| **Naukowiec** | pracownicy WI z profilem | opcjonalnie (SSO) lub link z zaproszenia | własny profil, własne zaproszenia, publiczny katalog |
| **Biuro** | ok. 5 pracowników biura projektowego | SSO AGH | nabory, dobór zespołu, projekty, zaproszenia, statystyki |
| **Koordynator** | 1 osoba z biura | SSO AGH | jak biuro, plus zatwierdzanie wysyłek, zarządzanie rolami biura, dziennik zmian |
| **Administrator techniczny** | IT / wdrożenie | SSO AGH | konfiguracja, kopie zapasowe, logi; bez dostępu do danych projektowych |

## Menu według roli

**Gość:** Naukowcy (publiczny katalog) · Oferta zespołów

**Naukowiec:** Naukowcy · Zaproszenia · Mój profil

**Biuro:** Naukowcy (z podzakładkami: Lista, Obszary, Dobierz zespół, Graf; z linkiem do Wyszukiwarki) · Nabory · Projekty (z tablicą, CSV i statystykami na dole) · Zaproszenia

**Koordynator:** jak biuro, plus Zatwierdzanie · Użytkownicy biura · Dziennik zmian

**Administrator:** Ustawienia · Kopie zapasowe · Logi

## Macierz uprawnień

| Działanie | Gość | Naukowiec | Biuro | Koordynator | Admin |
|---|---|---|---|---|---|
| Przeglądać publiczny katalog | tak | tak | tak | tak | tak |
| Przeglądać dane robocze (notatki, dostępność) | nie | własne | tak | tak | nie |
| Edytować własny profil | nie | tak | nie | nie | nie |
| Edytować cudzy profil | nie | nie | nie (tylko zgłoszenie korekty) | tak, po potwierdzeniu właściciela | nie |
| Tworzyć projekt i dobierać zespół | nie | nie | tak | tak | nie |
| Utworzyć szkic zaproszenia | nie | nie | tak | tak | nie |
| Zatwierdzić wysyłkę zaproszenia | nie | nie | nie | tak (inna osoba niż twórca, W11) | nie |
| Odpowiedzieć na zaproszenie | nie | tak | nie | nie | nie |
| Eksport CSV i statystyki | nie | nie | tak | tak | nie |
| Zarządzać rolami biura | nie | nie | nie | tak | tak |
| Przeglądać dziennik zmian | nie | nie | nie | tak | tak |

## Zasady

1. **Uprawnienia są sprawdzane na serwerze**, nie tylko ukrywane w przeglądarce.
2. **Każdy zapis ma autora i datę** (dziennik zmian, W9).
3. **Zaproszenie wymaga zatwierdzenia przez inną osobę** niż ta, która je utworzyła (W11). Przy 6 użytkownikach wystarczy, że koordynator zatwierdza, a twórca nie.
4. **Naukowiec nie widzi cudzych danych roboczych.** Zmiany w jego profilu, które zrobi biuro, wymagają jego potwierdzenia.
5. **Brak logowania nie oznacza brak prawa do odpowiedzi.** Zaproszenie zawiera jednorazowy link z terminem ważności.

## Otwarte pytania do IT AGH

- Protokół SSO: **OIDC** czy **SAML**? Jakie atrybuty są dostępne (e-mail, jednostka, identyfikator)?
- Czy SSO zwraca grupy lub role? Jeśli tak, role biura można przypisać z grup uczelni.
- Gdzie będzie serwer (hosting w infrastrukturze AGH czy w chmurze UE) i kto ma dostęp administracyjny?
- Czy serwer pocztowy AGH pozwoli wysyłać zaproszenia z aplikacji?

## Kolejność wdrożenia

1. **Serwer i SSO** dla biura (koordynator + 5 osób). Dane w bazie zamiast przeglądarki.
2. **Uprawnienia po rolach** i dziennik zmian.
3. **Naukowiec:** profil i odpowiedź na zaproszenie (SSO lub link).
4. **Gość:** publiczny katalog jako osobna, statyczna strona.

## Co nie jest jeszcze zrobione

- Brak kont i sesji. Obecne strony zapisują dane w przeglądarce.
- Brak rozdzielenia widoków według roli. Wszyscy widzą wszystkie strony.
- Brak zgody i informacji dla osób z WI (osobny wymóg przed startem).
