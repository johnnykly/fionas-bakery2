/* Fiona's Bakery: navigation, scroll reveals and the order form. No dependencies. */
(function () {
  'use strict';

  /* ---------- Mobile menu ---------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    var label = toggle.querySelector('span');
    var setOpen = function (open) {
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
      label.textContent = open ? 'Stäng' : 'Meny';
    };
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') !== 'true';
      setOpen(open);
      if (open) nav.querySelector('a').focus();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        toggle.focus();
      }
    });
    nav.addEventListener('focusout', function (e) {
      if (toggle.getAttribute('aria-expanded') === 'true' && e.relatedTarget &&
          !nav.contains(e.relatedTarget) && e.relatedTarget !== toggle) {
        setOpen(false);
      }
    });
  }

  /* ---------- Soft reveals ---------- */
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var items = document.querySelectorAll('.reveal');
  if (reduce || !('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('is-visible'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Order form ---------- */
  var form = document.getElementById('order-form');
  if (!form) return;

  var EMAIL = 'kontakt@fionasbakery.se';
  var $ = function (id) { return document.getElementById(id); };
  var occasion = $('f-tillfalle');
  var date = $('f-datum');
  var dateNote = $('datum-notice');
  var addressField = $('leveransadress-field');
  var address = $('f-adress');

  // Pre-select occasion from ?tillfalle=
  var params = new URLSearchParams(window.location.search);
  var pre = params.get('tillfalle');
  if (pre && occasion.querySelector('option[value="' + pre.replace(/[^a-z-]/g, '') + '"]')) {
    occasion.value = pre;
  }

  // Earliest date: today
  var pad = function (n) { return String(n).padStart(2, '0'); };
  var today = new Date();
  today.setHours(0, 0, 0, 0);
  date.min = today.getFullYear() + '-' + pad(today.getMonth() + 1) + '-' + pad(today.getDate());

  function daysUntil(value) {
    var p = value.split('-');
    var d = new Date(+p[0], +p[1] - 1, +p[2]);
    return Math.round((d - today) / 86400000);
  }

  function updateDateNotice() {
    if (!date.value) { dateNote.hidden = true; return; }
    var days = daysUntil(date.value);
    var wedding = occasion.value === 'brollop';
    var limit = wedding ? 30 : 7;
    if (days >= 0 && days < limit) {
      dateNote.querySelector('span').textContent = wedding
        ? 'Det är mindre än en månad kvar. Tårtor med sockerblommor behöver helst en månad, men skicka gärna förfrågan ändå så ser jag vad som går.'
        : 'Det är mindre än en vecka kvar. Dekorerade tårtor beställs helst 1-2 veckor innan, men ibland går det med kort varsel. Skicka gärna förfrågan ändå.';
      dateNote.hidden = false;
    } else {
      dateNote.hidden = true;
    }
  }
  date.addEventListener('change', updateDateNotice);
  occasion.addEventListener('change', updateDateNotice);

  // Pickup / delivery
  function updateDelivery() {
    var delivery = form.querySelector('input[name="hamtning"]:checked');
    var show = delivery && delivery.value === 'Leverans';
    addressField.hidden = !show;
    address.required = show;
    if (!show) clearError(address);
  }
  form.querySelectorAll('input[name="hamtning"]').forEach(function (r) {
    r.addEventListener('change', updateDelivery);
  });
  updateDelivery();

  // Validation
  var messages = {
    'f-tillfalle': 'Välj vilket tillfälle tårtan är till.',
    'f-datum': 'Fyll i datum för festen.',
    'f-antal': 'Fyll i ungefär hur många gäster eller bitar det gäller.',
    'f-hamtning': 'Välj om du vill hämta eller ha leverans.',
    'f-adress': 'Skriv vart tårtan ska levereras.',
    'f-namn': 'Fyll i ditt namn.',
    'f-telefon': 'Fyll i ett telefonnummer så jag kan nå dig.',
    'f-epost': 'Fyll i din e-postadress.',
    'f-samtycke': 'Kryssa i rutan så att jag får använda uppgifterna för att svara dig.'
  };

  function errorEl(input) {
    var id = input.type === 'radio' ? 'f-hamtning' : input.id;
    return $(id + '-error');
  }
  function setError(input, msg) {
    var el = errorEl(input);
    if (input.type === 'radio') {
      form.querySelectorAll('input[name="' + input.name + '"]').forEach(function (r) { r.setAttribute('aria-invalid', 'true'); });
    } else {
      input.setAttribute('aria-invalid', 'true');
    }
    if (el) { el.querySelector('span').textContent = msg; el.hidden = false; }
  }
  function clearError(input) {
    var el = errorEl(input);
    if (input.type === 'radio') {
      form.querySelectorAll('input[name="' + input.name + '"]').forEach(function (r) { r.removeAttribute('aria-invalid'); });
    } else {
      input.removeAttribute('aria-invalid');
    }
    if (el) el.hidden = true;
  }
  function check(input) {
    var v = input.validity;
    if (v.valid) { clearError(input); return true; }
    var key = input.type === 'radio' ? 'f-hamtning' : input.id;
    var msg = messages[key] || 'Kontrollera fältet.';
    if (v.typeMismatch && input.type === 'email') msg = 'Skriv e-postadressen som namn@exempel.se.';
    if (v.typeMismatch && input.type === 'url') msg = 'Skriv en hel länk som börjar med https://';
    if (v.rangeUnderflow && input.type === 'number') msg = 'Antalet behöver vara minst 1.';
    if (v.rangeUnderflow && input.type === 'date') msg = 'Datumet har redan varit. Välj ett datum framåt i tiden.';
    if (v.patternMismatch && input.type === 'tel') msg = 'Skriv telefonnumret med siffror, till exempel 070-123 45 67.';
    setError(input, msg);
    return false;
  }

  var fields = Array.prototype.slice.call(form.querySelectorAll('input:not(.hp-input), select, textarea'));
  fields.forEach(function (input) {
    var evt = input.type === 'radio' || input.type === 'checkbox' || input.tagName === 'SELECT' ? 'change' : 'blur';
    input.addEventListener(evt, function () {
      if (input.value || input.getAttribute('aria-invalid') === 'true' || input.type === 'checkbox') check(input);
    });
    input.addEventListener('input', function () {
      if (input.getAttribute('aria-invalid') === 'true') check(input);
    });
  });

  // Submission
  var status = $('form-status');
  var submit = form.querySelector('button[type="submit"]');
  var success = $('form-success');

  function value(name) {
    var el = form.elements[name];
    if (!el) return '';
    if (el instanceof RadioNodeList) return el.value;
    return (el.value || '').trim();
  }
  function summary() {
    var occ = occasion.options[occasion.selectedIndex].text;
    var lines = [
      'Tillfälle: ' + occ,
      'Datum för festen: ' + value('datum'),
      'Antal gäster / bitar: ' + value('antal'),
      'Hämtning eller leverans: ' + value('hamtning')
    ];
    if (value('hamtning') === 'Leverans') lines.push('Leveransadress / ort: ' + value('leveransadress'));
    if (value('smaker')) lines.push('Önskade smaker: ' + value('smaker'));
    if (value('inspiration')) lines.push('Inspiration: ' + value('inspiration'));
    if (value('meddelande')) lines.push('', 'Meddelande:', value('meddelande'));
    lines.push('', 'Namn: ' + value('namn'), 'Telefon: ' + value('telefon'), 'E-post: ' + value('epost'));
    return { subject: 'Offertförfrågan: ' + occ + ', ' + value('datum'), body: lines.join('\n') };
  }

  function showSuccess(mode, text) {
    form.hidden = true;
    success.hidden = false;
    success.querySelector('[data-mode="sent"]').hidden = mode !== 'sent';
    success.querySelector('[data-mode="mail"]').hidden = mode !== 'mail';
    if (text) success.querySelector('pre').textContent = text;
    success.focus();
    success.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    status.hidden = true;
    var firstInvalid = null;
    var seenRadio = false;
    fields.forEach(function (input) {
      if (input.type === 'radio') { if (seenRadio) return; seenRadio = true; }
      if (input.closest('[hidden]')) return;
      if (!check(input) && !firstInvalid) firstInvalid = input;
    });
    if (firstInvalid) {
      status.textContent = 'Några uppgifter saknas. Se de markerade fälten.';
      status.hidden = false;
      firstInvalid.focus();
      return;
    }
    if (form.querySelector('.hp-input').value) return; // bot

    var s = summary();
    var endpoint = form.getAttribute('data-endpoint');
    if (!endpoint) {
      var href = 'mailto:' + EMAIL + '?subject=' + encodeURIComponent(s.subject) + '&body=' + encodeURIComponent(s.body);
      window.location.href = href;
      showSuccess('mail', s.body);
      return;
    }

    var data = new FormData(form);
    data.append('subject', s.subject);
    data.append('_subject', s.subject);
    var key = form.getAttribute('data-access-key');
    if (key) data.append('access_key', key);
    submit.disabled = true;
    submit.querySelector('span').textContent = 'Skickar…';
    fetch(endpoint, { method: 'POST', body: data, headers: { Accept: 'application/json' } })
      .then(function (res) {
        if (!res.ok) throw new Error(res.status);
        showSuccess('sent', s.body);
      })
      .catch(function () {
        status.innerHTML = 'Förfrågan kunde inte skickas just nu. Försök igen, eller mejla direkt till <a href="mailto:' + EMAIL +
          '?subject=' + encodeURIComponent(s.subject) + '&amp;body=' + encodeURIComponent(s.body) + '">' + EMAIL + '</a>.';
        status.hidden = false;
      })
      .then(function () {
        submit.disabled = false;
        submit.querySelector('span').textContent = 'Skicka förfrågan';
      });
  });
})();
