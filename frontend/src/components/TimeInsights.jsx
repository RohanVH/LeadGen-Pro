import React from "react";
import { getTimeData } from "../utils/timeUtils";
import { getAISuggestion } from "../utils/aiSuggestion";
import { getCountryInsight } from "../utils/countryInsights";

// ✅ Strength logic (kept your function)
function getCurrencyStrength(rate) {
  if (!rate) return "Unknown";

  if (rate > 80) return "Strong";
  if (rate > 20) return "Moderate";
  return "Weak";
}

const TimeInsights = ({ country, businessType, lat, lng }) => {
  const [, setTick] = React.useState(0);

  // ✅ NEW STATES
  const [currencyData, setCurrencyData] = React.useState(null);
  const [rate, setRate] = React.useState(null);
  const [strength, setStrength] = React.useState(null);
  const [loadingCurrency, setLoadingCurrency] = React.useState(false);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setTick((t) => t + 1);
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  // ✅ NEW EFFECT (FETCH CURRENCY)
  React.useEffect(() => {
    if (!country) return;

    async function loadCurrency() {
      try {
        setLoadingCurrency(true);

        // 1️⃣ Get currency from country
        const res = await fetch(`https://restcountries.com/v3.1/name/${country}`);
        const data = await res.json();

        const currencyObj = data[0]?.currencies;
        const code = currencyObj ? Object.keys(currencyObj)[0] : null;

        if (!code) return;

        const currency = {
          code,
          name: currencyObj[code].name,
          symbol: currencyObj[code].symbol,
        };

        setCurrencyData(currency);

        // 2️⃣ Convert to INR
        const rateRes = await fetch(`https://open.er-api.com/v6/latest/${code}`);
        const rateData = await rateRes.json();

        const inrRate = rateData?.rates?.INR;

        setRate(inrRate);

        // 3️⃣ Strength
        const strengthValue = getCurrencyStrength(inrRate);
        setStrength(strengthValue);

      } catch (err) {
        console.error("Currency fetch failed:", err);
      } finally {
        setLoadingCurrency(false);
      }
    }

    loadCurrency();
  }, [country]);

  if (!country) return null;

  const data = getTimeData({ country, lat, lng });
  const aiSuggestion = getAISuggestion(businessType, data.isBusinessTime);
  const insight = getCountryInsight(country);

  if (!data) {
    return (
      <div className="mt-4 p-4 rounded-lg bg-gray-800 text-white">
        ❌ No timezone data available
      </div>
    );
  }

  return (
    <div className="mt-4 p-5 rounded-2xl bg-gradient-to-r from-gray-900 to-gray-800 text-white shadow-xl border border-gray-700">

      <h2 className="text-lg font-semibold mb-3">🌍 {country}</h2>

      {/* Time */}
      <div className="space-y-1 text-sm">
        <p>🕒 Current Time: <b>{data.countryTime}</b></p>
        <p>🇮🇳 Your Time (IST): <b>{data.istTime}</b></p>
      </div>

      {/* Best Time */}
      <div className="mt-3 text-sm">
        <p className="text-green-400 font-medium">🟢 Best Time (IST):</p>
        <p className="ml-2">{data.bestStart} – {data.bestEnd}</p>

        <p className="text-red-400 mt-1">
          ⚠️ Avoid: Late night / early morning
        </p>
      </div>

      {/* STATUS */}
      <div className="mt-4 text-sm font-semibold">
        {data.isBusinessTime ? (
          <p className="text-green-400">
            🟢 Perfect time to contact {country} clients NOW
          </p>
        ) : (
          <p className="text-red-400">
            🔴 Not the right time
            <br />
            ⏳ Wait {data.waitTime} to reach business hours
          </p>
        )}
      </div>

      {/* Strategy */}
      <div className="mt-4 border-t border-gray-700 pt-3 text-sm space-y-1">
        <p>📅 Best Day: Weekdays (Mon–Fri)</p>

        {data.isWeekendDay && (
          <p className="text-yellow-400">
            ⚠️ Today is weekend — response rate may be low
          </p>
        )}

        <p>🚫 Avoid: Sunday / holidays</p>

        {businessType && (
          <p>
            🧠 Tip:{" "}
            {businessType.toLowerCase().includes("restaurant") ||
            businessType.toLowerCase().includes("cafe")
              ? "Contact before lunch (11 AM) or after 3 PM."
              : businessType.toLowerCase().includes("clinic")
              ? "Best in morning or late evening."
              : "Best during working hours (10 AM – 5 PM)."}
          </p>
        )}
      </div>

      {/* 💰 NEW CURRENCY SECTION */}
      <div className="mt-4 border-t border-gray-700 pt-3 text-sm space-y-1">
        <p className="text-indigo-400 font-semibold">💰 Market Currency Insight</p>

        {loadingCurrency && <p>Fetching currency data...</p>}

        {currencyData && (
          <>
            <p>
              💰 Currency: {currencyData.name} ({currencyData.code})
            </p>

            {rate && (
              <p>
                💱 1 {currencyData.code} = ₹{rate.toFixed(2)}
              </p>
            )}

            {strength && (
              <p>
                📊 Strength:{" "}
                <span
                  className={
                    strength === "Strong"
                      ? "text-green-400"
                      : strength === "Moderate"
                      ? "text-yellow-400"
                      : "text-red-400"
                  }
                >
                  {strength === "Strong" && "🟢 Strong"}
                  {strength === "Moderate" && "🟡 Moderate"}
                  {strength === "Weak" && "🔴 Weak"}
                </span>
              </p>
            )}
          </>
        )}
      </div>

      {/* 🤖 EXISTING AI (UNCHANGED) */}
      <div className="mt-4 border-t border-gray-700 pt-3 text-sm space-y-1">
        <p className="text-indigo-400 font-semibold">🤖 AI Market Insight</p>

        <p>🌍 Mindset: {insight.mindset}</p>
        <p>💡 {insight.tip}</p>
      </div>

    </div>
  );
};

export default TimeInsights;