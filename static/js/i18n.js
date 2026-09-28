/**
 * Farm Wise AI — Internationalization (i18n) Engine
 * Provides complete website-wide language translation support
 * for 12 Indian languages + English.
 *
 * Usage in HTML:
 *   <span data-i18n="key">English fallback</span>
 *   <input data-i18n-placeholder="key" placeholder="English fallback">
 *   <button data-i18n="key">English fallback</button>
 *   <option data-i18n="key">English fallback</option>
 *   <img data-i18n-alt="key" alt="English fallback">
 *
 * Usage in JavaScript:
 *   t("key")                  // returns translated string
 *   t("key", "fallback")     // returns translated string or fallback
 *   setLanguage("kn")        // switch to Kannada
 *   getCurrentLanguage()     // returns current lang code
 */

(function () {
  "use strict";

  const SUPPORTED_LANGS = {
    en: "English",
    kn: "ಕನ್ನಡ",
    hi: "हिन्दी",
    te: "తెలుగు",
    ta: "தமிழ்",
    mr: "मराठी",
    bn: "বাংলা",
    ml: "മലയാളം",
    gu: "ગુજરાતી",
    pa: "ਪੰਜਾਬੀ",
    or: "ଓଡ଼ିଆ",
    as: "অসমীয়া"
  };

  const STORAGE_KEY = "farmwise_lang";
  let _currentLang = "en";
  let _translations = {};
  let _cache = {};

  /** Get the currently active language code */
  function getCurrentLanguage() {
    return _currentLang;
  }

  /** Get the translation for a key. Returns fallback or key if not found. */
  function t(key, fallback) {
    if (_translations[key] !== undefined) return _translations[key];
    if (fallback !== undefined) return fallback;
    // Try English cache as secondary fallback
    if (_cache["en"] && _cache["en"][key] !== undefined) return _cache["en"][key];
    return key;
  }

  /** Apply all translations to the current DOM */
  function applyTranslations() {
    // Text content
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (key && _translations[key] !== undefined) {
        // For elements with child elements (like icons), only set text of text nodes
        if (el.childElementCount > 0) {
          // Find and replace only text nodes
          var nodes = el.childNodes;
          for (var i = 0; i < nodes.length; i++) {
            if (nodes[i].nodeType === Node.TEXT_NODE && nodes[i].textContent.trim()) {
              nodes[i].textContent = " " + _translations[key] + " ";
              break;
            }
          }
        } else {
          el.textContent = _translations[key];
        }
      }
    });

    // Placeholders
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-placeholder");
      if (key && _translations[key] !== undefined) {
        el.placeholder = _translations[key];
      }
    });

    // Alt text
    document.querySelectorAll("[data-i18n-alt]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-alt");
      if (key && _translations[key] !== undefined) {
        el.alt = _translations[key];
      }
    });

    // Title attributes
    document.querySelectorAll("[data-i18n-title]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-title");
      if (key && _translations[key] !== undefined) {
        el.title = _translations[key];
      }
    });

    // HTML lang attribute
    document.documentElement.lang = _currentLang;

    // Update language selector if present
    var selectors = document.querySelectorAll(".lang-selector");
    selectors.forEach(function (sel) {
      sel.value = _currentLang;
    });

    // Dispatch event for JS components to react
    document.dispatchEvent(new CustomEvent("languageChanged", {
      detail: { lang: _currentLang, translations: _translations }
    }));
  }

  /** Load a language JSON file and apply translations */
  function loadLanguage(lang) {
    if (!SUPPORTED_LANGS[lang]) lang = "en";

    // Use cache if available
    if (_cache[lang]) {
      _currentLang = lang;
      _translations = _cache[lang];
      applyTranslations();
      return Promise.resolve();
    }

    var url = "/static/translations/" + lang + ".json?v=" + Date.now();
    return fetch(url)
      .then(function (res) {
        if (!res.ok) throw new Error("Translation file not found: " + lang);
        return res.json();
      })
      .then(function (data) {
        _cache[lang] = data;
        _currentLang = lang;
        _translations = data;
        applyTranslations();
      })
      .catch(function (err) {
        console.warn("i18n: Failed to load " + lang + ", falling back to en.", err);
        if (lang !== "en") {
          return loadLanguage("en");
        }
      });
  }

  /** Set the language, save to localStorage, and apply */
  function setLanguage(lang) {
    localStorage.setItem(STORAGE_KEY, lang);
    return loadLanguage(lang);
  }

  /** Get supported languages object */
  function getSupportedLanguages() {
    return Object.assign({}, SUPPORTED_LANGS);
  }

  /** Create and inject language selector dropdown into a container */
  function createLanguageSelector(container) {
    if (!container) return;
    var select = document.createElement("select");
    select.className = "lang-selector";
    select.setAttribute("aria-label", "Select Language");

    Object.keys(SUPPORTED_LANGS).forEach(function (code) {
      var opt = document.createElement("option");
      opt.value = code;
      opt.textContent = SUPPORTED_LANGS[code];
      if (code === _currentLang) opt.selected = true;
      select.appendChild(opt);
    });

    select.addEventListener("change", function () {
      setLanguage(this.value);
    });

    container.appendChild(select);
    return select;
  }

  /** Initialize i18n on page load */
  function init() {
    // Restore saved language
    var saved = localStorage.getItem(STORAGE_KEY);
    var lang = saved && SUPPORTED_LANGS[saved] ? saved : "en";

    // Inject language selectors into designated containers
    document.querySelectorAll("[data-lang-selector]").forEach(function (el) {
      createLanguageSelector(el);
    });

    // Load language
    loadLanguage(lang);
  }

  // Auto-initialize when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expose global API
  window.t = t;
  window.setLanguage = setLanguage;
  window.getCurrentLanguage = getCurrentLanguage;
  window.getSupportedLanguages = getSupportedLanguages;
  window.applyTranslations = applyTranslations;
  window.createLanguageSelector = createLanguageSelector;
  window.i18n = {
    t: t,
    setLanguage: setLanguage,
    getCurrentLanguage: getCurrentLanguage,
    getSupportedLanguages: getSupportedLanguages,
    applyTranslations: applyTranslations,
    createLanguageSelector: createLanguageSelector
  };

})();
