/* Wspólny pasek konta: ikona profilu, menu i dzwonek powiadomień.
   Działa na wszystkich stronach. Dane czyta z tych samych kluczy co strony
   (bm-panel-v2 i bm-projekty-v1), z serwera albo z przeglądarki. */
(function () {
  var ME_KEY = 'bm-me';
  var PANEL_KEY = 'bm-panel-v2';
  var BIURO_KEY = 'bm-projekty-v1';
  var ANSWERS = ['odpowiedź: tak', 'odpowiedź: nie', 'brak odpowiedzi'];

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function initials(n) {
    return String(n || '?').split(/\s+/).filter(Boolean).slice(0, 2).map(function (p) { return p[0]; }).join('').toUpperCase();
  }
  function readLocal(key, fb) {
    try { return JSON.parse(localStorage.getItem(key) || 'null') || fb; } catch (e) { return fb; }
  }
  function loadRemote(key) {
    return fetch('/api/kv/' + encodeURIComponent(key), { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }
  function me() {
    return readLocal(ME_KEY, { role: 'biuro', name: '' });
  }
  function setMe(v) {
    try { localStorage.setItem(ME_KEY, JSON.stringify(v)); } catch (e) {}
  }

  function notifications(panel, biuro, user) {
    var out = [];
    var invites = (panel && panel.invites) || [];
    if (user.role === 'naukowiec') {
      invites.filter(function (i) { return i.person === user.name && i.status !== 'szkic' && ANSWERS.indexOf(i.status) === -1; })
        .forEach(function (i) {
          out.push({ text: 'Zaproszenie do naboru ' + i.nabor, sub: 'rola: ' + i.rola + ' · odpowiedz w profilu', href: 'profil.html?osoba=' + encodeURIComponent(i.person) });
        });
    } else {
      invites.filter(function (i) { return i.status === 'szkic'; }).forEach(function (i) {
        out.push({ text: 'Szkic do zatwierdzenia: ' + i.person, sub: 'nabór ' + i.nabor + ' · zatwierdź w Panelu', href: 'panel.html' });
      });
      invites.filter(function (i) { return ANSWERS.indexOf(i.status) !== -1; }).forEach(function (i) {
        out.push({ text: i.person + ': ' + i.status.replace('odpowiedź: ', 'odpowiedź ') , sub: 'nabór ' + i.nabor, href: 'profil.html?osoba=' + encodeURIComponent(i.person) });
      });
    }
    return out;
  }

  function render(slot, panel, biuro) {
    var user = me();
    var notes = notifications(panel, biuro, user);
    var label = user.role === 'naukowiec' ? (user.name || 'Naukowiec') : 'Biuro projektowe';
    var profileHref = user.role === 'naukowiec'
      ? 'profil.html?osoba=' + encodeURIComponent(user.name || '')
      : 'profil.html';
    slot.innerHTML =
      '<button class="acc-bell" type="button" aria-label="Powiadomienia" aria-expanded="false" aria-controls="acc-notes">' +
        '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/></svg>' +
        (notes.length ? '<span class="acc-badge" aria-label="' + notes.length + ' nowych">' + notes.length + '</span>' : '') +
      '</button>' +
      '<div class="acc-notes" id="acc-notes" hidden>' +
        '<div class="acc-title">Wiadomości i powiadomienia</div>' +
        (notes.length ? notes.map(function (n) {
          return '<a class="acc-note" href="' + esc(n.href) + '"><b>' + esc(n.text) + '</b><span>' + esc(n.sub) + '</span></a>';
        }).join('') : '<div class="acc-empty">Brak nowych powiadomień.</div>') +
      '</div>' +
      '<button class="acc-me" type="button" aria-label="Konto: ' + esc(label) + '" aria-expanded="false" aria-controls="acc-menu">' +
        '<span class="acc-av">' + esc(user.role === 'naukowiec' ? (user.name ? initials(user.name) : 'N') : 'BP') + '</span>' +
        '<span class="acc-name">' + esc(label) + '</span>' +
      '</button>' +
      '<div class="acc-menu" id="acc-menu" hidden>' +
        '<a href="' + esc(profileHref) + '">Mój profil</a>' +
        '<a href="panel.html">Zaproszenia i panel</a>' +
        '<div class="acc-sep"></div>' +
        '<div class="acc-title">Przełącz widok (test)</div>' +
        '<button type="button" data-role="biuro">Biuro projektowe</button>' +
        '<button type="button" data-role="naukowiec">Naukowiec</button>' +
        (user.role === 'naukowiec'
          ? '<label class="acc-pick">Osoba<select id="acc-person"></select></label>'
          : '') +
      '</div>';
    wire(slot, panel, biuro);
  }

  function wire(slot, panel, biuro) {
    var bell = slot.querySelector('.acc-bell'), notes = slot.querySelector('#acc-notes');
    var me_ = slot.querySelector('.acc-me'), menu = slot.querySelector('#acc-menu');
    function closeAll() {
      notes.hidden = true; menu.hidden = true;
      bell.setAttribute('aria-expanded', 'false'); me_.setAttribute('aria-expanded', 'false');
    }
    bell.addEventListener('click', function (e) {
      e.stopPropagation(); var open = notes.hidden; closeAll();
      notes.hidden = !open; bell.setAttribute('aria-expanded', String(open));
    });
    me_.addEventListener('click', function (e) {
      e.stopPropagation(); var open = menu.hidden; closeAll();
      menu.hidden = !open; me_.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('click', closeAll);
    notes.addEventListener('click', function (e) { e.stopPropagation(); });
    menu.addEventListener('click', function (e) { e.stopPropagation(); });
    menu.querySelectorAll('[data-role]').forEach(function (b) {
      b.addEventListener('click', function () {
        var role = b.getAttribute('data-role');
        var name = role === 'naukowiec' ? (me().name || firstName(panel)) : '';
        setMe({ role: role, name: name });
        location.reload();
      });
    });
    var sel = slot.querySelector('#acc-person');
    if (sel) {
      var people = names(panel);
      sel.innerHTML = people.map(function (n) {
        return '<option value="' + esc(n) + '"' + (n === me().name ? ' selected' : '') + '>' + esc(n) + '</option>';
      }).join('');
      sel.addEventListener('change', function () { setMe({ role: 'naukowiec', name: sel.value }); location.reload(); });
    }
  }

  function names(panel) {
    var set = {};
    ((panel && panel.invites) || []).forEach(function (i) { set[i.person] = true; });
    Object.keys((panel && panel.profiles) || {}).forEach(function (n) { set[n] = true; });
    return Object.keys(set).sort();
  }
  function firstName(panel) { return names(panel)[0] || ''; }

  var BIURO_PAGES = ['biuro.html', 'biuro_przyklad.html', 'wyszukiwarka.html', 'dopasowanie.html', 'raport_dopasowanie_tematy.html'];

  function currentPage() {
    var p = location.pathname.split('/').pop();
    return p || 'index.html';
  }

  function applyRole(panel) {
    var user = me();
    var naukowiec = user.role === 'naukowiec';
    var role = naukowiec ? 'naukowiec' : 'biuro';
    document.querySelectorAll('[data-role-only]').forEach(function (el) {
      el.hidden = el.getAttribute('data-role-only') !== role;
    });
    if (naukowiec) {
      document.querySelectorAll('.tabs a.tab[href="panel.html"]').forEach(function (a) { a.textContent = 'Zaproszenia'; });
      document.querySelectorAll('.tabs a.tab[href="index.html"]').forEach(function (a) { a.textContent = 'Naukowcy'; });
      document.querySelectorAll('.tabs a.tab[href="profil.html"]').forEach(function (a) {
        if (user.name) a.setAttribute('href', 'profil.html?osoba=' + encodeURIComponent(user.name));
      });
    }
    var page = currentPage();
    var heroT = document.querySelector('.hero-simple .hero-title');
    var heroS = document.querySelector('.hero-simple .hero-sub');
    if (page === 'index.html' && naukowiec && heroT) {
      heroT.textContent = 'Naukowcy';
      if (heroS) heroS.textContent = 'Przeglądaj osoby, obszary i powiązania. Swój profil i zaproszenia znajdziesz w menu.';
    }
    if (page === 'panel.html' && heroT) {
      heroT.textContent = naukowiec ? 'Moje zaproszenia' : 'Panel biura';
      if (heroS) heroS.textContent = naukowiec
        ? 'Zaproszenia do naborów i Twoje odpowiedzi.'
        : 'Przegląd naborów, zaproszeń i odpowiedzi. Zatwierdzenie wysyłki wymaga innej osoby niż ta, która utworzyła szkic.';
    }
    if (naukowiec && BIURO_PAGES.indexOf(page) !== -1) {
      location.replace('profil.html' + (user.name ? '?osoba=' + encodeURIComponent(user.name) : ''));
      return;
    }
    if (naukowiec && page === 'profil.html' && !new URLSearchParams(location.search).get('osoba') && user.name) {
      location.replace('profil.html?osoba=' + encodeURIComponent(user.name));
      return;
    }
    if (naukowiec && !user.name) {
      var first = names(panel)[0];
      if (first) { setMe({ role: 'naukowiec', name: first }); location.reload(); return; }
    }
    if (page === 'panel.html') {
      document.querySelectorAll('.pn-view').forEach(function (v) { v.classList.toggle('active', v.id === (naukowiec ? 'view-nauk' : 'view-biuro')); });
      if (naukowiec && user.name) {
        var who = document.getElementById('pn-who');
        if (who) who.textContent = 'Moje dane';
        var sel = document.getElementById('pn-person');
        if (sel) {
          if (!Array.prototype.some.call(sel.options, function (o) { return o.value === user.name; })) {
            sel.insertAdjacentHTML('beforeend', '<option value="' + esc(user.name) + '">' + esc(user.name) + '</option>');
          }
          sel.value = user.name;
          sel.dispatchEvent(new Event('change'));
        }
      }
    }
    if (page === 'profil.html') {
      document.querySelectorAll('.page-view').forEach(function (v) { v.classList.toggle('active', v.id === (naukowiec ? 'view-naukowiec' : 'view-biuro')); });
      var pick = document.getElementById('pf-person');
      if (pick && naukowiec) pick.hidden = true;
    }
  }

  function start() {
    var slot = document.getElementById('account-slot');
    if (!slot) return;
    Promise.all([loadRemote(PANEL_KEY), loadRemote(BIURO_KEY)]).then(function (r) {
      var panel = r[0] || readLocal(PANEL_KEY, { profiles: {}, invites: [] });
      var biuro = r[1] || readLocal(BIURO_KEY, { cards: {}, custom: [] });
      render(slot, panel, biuro);
      applyRole(panel);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
