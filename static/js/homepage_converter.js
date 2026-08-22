(function () {
  const form = document.getElementById("homeConverterForm");
  if (!form) {
    return;
  }

  const sourceSelect = document.getElementById("sourceCurrency");
  const targetSelect = document.getElementById("targetCurrency");
  const amountInput = document.getElementById("sendAmount");
  const swapButton = document.getElementById("swapCorridor");
  const continueButton = document.getElementById("continueButton");
  const amountError = document.getElementById("amountError");
  const statusBox = document.getElementById("quoteStatus");
  const receivedAmount = document.getElementById("receivedAmount");
  const rateLine = document.getElementById("rateLine");
  const feeLine = document.getElementById("feeLine");
  const directionLine = document.getElementById("corridorLabel");
  const sourceCountry = document.getElementById("sourceCountry");
  const sourceCountryInline = document.getElementById("sourceCountryInline");
  const sourceCurrencyLabel = document.getElementById("sourceCurrencyLabel");
  const sourceFlag = document.getElementById("sourceFlag");
  const targetCountry = document.getElementById("targetCountry");
  const targetCountryInline = document.getElementById("targetCountryInline");
  const targetCurrencyLabel = document.getElementById("targetCurrencyLabel");
  const targetFlag = document.getElementById("targetFlag");
  const fromCurrencyInput = document.getElementById("fromCurrencyInput");
  const toCurrencyInput = document.getElementById("toCurrencyInput");

  const quoteDataNode = document.getElementById("homepageQuoteData");
  const corridorsNode = document.getElementById("homepageCorridorsData");

  let currentQuote = parseJson(quoteDataNode?.textContent, {});
  const corridors = parseJson(corridorsNode?.textContent, []);
  const corridorByKey = Object.fromEntries(
    corridors.map((corridor) => [buildKey(corridor.from_currency, corridor.to_currency), corridor]),
  );
  const sourceOptions = [];
  const sourceIndex = new Set();
  const currencyMetadata = {};

  corridors.forEach((corridor) => {
    if (!sourceIndex.has(corridor.from_currency)) {
      sourceIndex.add(corridor.from_currency);
      sourceOptions.push({
        currency: corridor.from_currency,
        country: corridor.from_country_name,
        flag: corridor.from_flag,
      });
    }

    currencyMetadata[corridor.from_currency] = {
      country: corridor.from_country_name,
      flag: corridor.from_flag,
    };
    currencyMetadata[corridor.to_currency] = {
      country: corridor.to_country_name,
      flag: corridor.to_flag,
    };
  });

  function parseJson(raw, fallback) {
    try {
      return raw ? JSON.parse(raw) : fallback;
    } catch (error) {
      return fallback;
    }
  }

  function buildKey(fromCurrency, toCurrency) {
    return `${fromCurrency}->${toCurrency}`;
  }

  function formatAmount(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return "--";
    }

    return new Intl.NumberFormat("fr-FR", {
      minimumFractionDigits: number % 1 === 0 ? 0 : 2,
      maximumFractionDigits: 2,
    }).format(number);
  }

  function setStatus(kind, message) {
    if (!message) {
      statusBox.className = "hidden rounded-2xl border px-4 py-3 text-sm";
      statusBox.textContent = "";
      return;
    }

    const styles = {
      loading: "rounded-2xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700",
      error: "rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700",
      warning: "rounded-2xl border border-yellow-200 bg-yellow-50 px-4 py-3 text-sm text-yellow-700",
    };

    statusBox.className = styles[kind] || styles.warning;
    statusBox.textContent = message;
  }

  function setAmountError(message) {
    if (!message) {
      amountError.classList.add("hidden");
      amountError.textContent = "";
      return;
    }

    amountError.classList.remove("hidden");
    amountError.textContent = message;
  }

  function metadataFor(currency) {
    return currencyMetadata[currency] || { country: currency, flag: "" };
  }

  function availableTargets(fromCurrency) {
    return corridors
      .filter((corridor) => corridor.from_currency === fromCurrency)
      .map((corridor) => ({
        currency: corridor.to_currency,
        country: corridor.to_country_name,
        flag: corridor.to_flag,
      }));
  }

  function populateSourceOptions(selectedCurrency) {
    sourceSelect.innerHTML = "";
    sourceOptions.forEach((option) => {
      const node = document.createElement("option");
      node.value = option.currency;
      node.textContent = option.currency;
      node.dataset.country = option.country;
      node.dataset.flag = option.flag;
      if (option.currency === selectedCurrency) {
        node.selected = true;
      }
      sourceSelect.appendChild(node);
    });
  }

  function populateTargetOptions(fromCurrency, selectedCurrency) {
    const targets = availableTargets(fromCurrency);
    targetSelect.innerHTML = "";

    targets.forEach((option) => {
      const node = document.createElement("option");
      node.value = option.currency;
      node.textContent = option.currency;
      node.dataset.country = option.country;
      node.dataset.flag = option.flag;
      if (option.currency === selectedCurrency) {
        node.selected = true;
      }
      targetSelect.appendChild(node);
    });

    if (targets.length === 0) {
      const node = document.createElement("option");
      node.value = "";
      node.textContent = "Indisponible";
      node.selected = true;
      targetSelect.appendChild(node);
      return "";
    }

    const selectedStillExists = targets.some((option) => option.currency === selectedCurrency);
    if (!selectedStillExists) {
      targetSelect.value = targets[0].currency;
    }

    return targetSelect.value;
  }

  function syncVisibleSelection(fromCurrency, toCurrency) {
    const sourceMeta = metadataFor(fromCurrency);
    const targetMeta = metadataFor(toCurrency);

    fromCurrencyInput.value = fromCurrency || "";
    toCurrencyInput.value = toCurrency || "";

    sourceFlag.textContent = sourceMeta.flag || "";
    sourceCountryInline.textContent = sourceMeta.country || "";
    sourceCountry.textContent = sourceMeta.country || "";
    sourceCurrencyLabel.textContent = fromCurrency || "";

    targetFlag.textContent = targetMeta.flag || "";
    targetCountryInline.textContent = targetMeta.country || "";
    targetCountry.textContent = targetMeta.country || "";
    targetCurrencyLabel.textContent = toCurrency || "";

    directionLine.textContent = `${fromCurrency || ""} → ${toCurrency || ""}`;
  }

  function applyQuote(quote) {
    currentQuote = quote;
    populateSourceOptions(quote.from_currency);
    populateTargetOptions(quote.from_currency, quote.to_currency);
    syncVisibleSelection(quote.from_currency, quote.to_currency);

    receivedAmount.textContent =
      quote.amount_received === null || quote.amount_received === undefined
        ? "--"
        : formatAmount(quote.amount_received);

    rateLine.textContent =
      quote.rate === null || quote.rate === undefined
        ? "Taux indisponible pour le moment"
        : `1 ${quote.from_currency} = ${quote.rate} ${quote.to_currency}`;

    feeLine.textContent = quote.fee_label || "Frais calculés à l'étape suivante";

    if (quote.ok) {
      continueButton.disabled = false;
      setStatus("success", "");
      return;
    }

    continueButton.disabled = true;
    if (quote.error_code === "corridor_unavailable") {
      setStatus("warning", "Ce sens de conversion n'est pas encore disponible.");
    } else {
      setStatus("error", "Impossible de récupérer le taux pour le moment. Réessayez.");
    }
  }

  function selectedPair() {
    const fromCurrency = sourceSelect.value;
    const toCurrency = targetSelect.value;
    return {
      fromCurrency,
      toCurrency,
      corridor: corridorByKey[buildKey(fromCurrency, toCurrency)] || null,
    };
  }

  function setLoading() {
    continueButton.disabled = true;
    rateLine.textContent = "Calcul du taux...";
    setStatus("loading", "Calcul du taux...");
  }

  async function requestQuote() {
    const amount = Number(amountInput.value);
    const { fromCurrency, toCurrency, corridor } = selectedPair();

    if (!Number.isFinite(amount) || amount <= 0) {
      setAmountError("Veuillez saisir un montant supérieur à 0.");
      continueButton.disabled = true;
      receivedAmount.textContent = "--";
      rateLine.textContent = "Taux indisponible pour le moment";
      setStatus("warning", "");
      return;
    }

    setAmountError("");
    syncVisibleSelection(fromCurrency, toCurrency);

    if (!fromCurrency || !toCurrency || !corridor) {
      applyQuote({
        ok: false,
        error_code: "corridor_unavailable",
        from_currency: fromCurrency,
        to_currency: toCurrency,
        amount_received: null,
        rate: null,
        fee_label: "Frais calculés à l'étape suivante",
      });
      return;
    }

    setLoading();

    try {
      const response = await fetch("/convert/api/convertir", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": window.CSRF_TOKEN || "",
        },
        body: JSON.stringify({
          montant: amount,
          from_currency: fromCurrency,
          to_currency: toCurrency,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        applyQuote({
          ok: false,
          error_code:
            data.error === "Ce corridor n'est pas encore disponible."
              ? "corridor_unavailable"
              : "rates_unavailable",
          from_currency: fromCurrency,
          to_currency: toCurrency,
          amount_received: null,
          rate: null,
          fee_label: "Frais calculés à l'étape suivante",
        });
        return;
      }

      applyQuote({
        ok: true,
        from_currency: data.from_currency,
        to_currency: data.to_currency,
        amount_received: data.montant_converti,
        rate: data.taux,
        fee_label: data.frais_label,
      });
    } catch (error) {
      applyQuote({
        ok: false,
        error_code: "rates_unavailable",
        from_currency: fromCurrency,
        to_currency: toCurrency,
        amount_received: null,
        rate: null,
        fee_label: "Frais calculés à l'étape suivante",
      });
    }
  }

  function handleSourceChange() {
    const nextSource = sourceSelect.value;
    const nextTarget = populateTargetOptions(nextSource, targetSelect.value);
    syncVisibleSelection(nextSource, nextTarget);
    requestQuote();
  }

  function handleTargetChange() {
    const { fromCurrency, toCurrency } = selectedPair();
    syncVisibleSelection(fromCurrency, toCurrency);
    requestQuote();
  }

  function invertPair() {
    const { fromCurrency, toCurrency } = selectedPair();
    const inverseKey = buildKey(toCurrency, fromCurrency);

    if (!corridorByKey[inverseKey]) {
      applyQuote({
        ok: false,
        error_code: "corridor_unavailable",
        from_currency: toCurrency,
        to_currency: fromCurrency,
        amount_received: null,
        rate: null,
        fee_label: "Frais calculés à l'étape suivante",
      });
      return;
    }

    populateSourceOptions(toCurrency);
    populateTargetOptions(toCurrency, fromCurrency);
    syncVisibleSelection(toCurrency, fromCurrency);
    requestQuote();
  }

  form.addEventListener("submit", (event) => {
    const amount = Number(amountInput.value);
    const { corridor } = selectedPair();
    if (!Number.isFinite(amount) || amount <= 0 || continueButton.disabled || !corridor) {
      event.preventDefault();
    }
  });

  amountInput.addEventListener("input", requestQuote);
  sourceSelect.addEventListener("change", handleSourceChange);
  targetSelect.addEventListener("change", handleTargetChange);
  swapButton.addEventListener("click", invertPair);

  if (currentQuote && currentQuote.from_currency) {
    applyQuote(currentQuote);
  }
})();
