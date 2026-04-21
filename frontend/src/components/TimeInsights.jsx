import React from "react";
import { getTimeData } from "../utils/timeUtils";
import { getAISuggestion } from "../utils/aiSuggestion";

const TimeInsights = ({ country, businessType, lat, lng }) => {
    const [, setTick] = React.useState(0);

    React.useEffect(() => {
        const interval = setInterval(() => {
            setTick((t) => t + 1);
        }, 60000);

        return () => clearInterval(interval);
    }, []);

    if (!country) return null;

    const data = getTimeData({ country, lat, lng });
    const aiSuggestion = getAISuggestion(businessType, data.isBusinessTime);

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
                <p> &npbs; 🇮🇳  &npbs;Your Time (IST): <b>{data.istTime}</b></p>
            </div>

            {/* Best Time */}
            <div className="mt-3 text-sm">
                <p className="text-green-400 font-medium">
                    🟢 Best Time (IST):
                </p>
                <p className="ml-2">
                    {data.bestStart} – {data.bestEnd}
                </p>

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

                {/* Business-specific logic */}
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
            <div className="mt-4 border-t border-gray-700 pt-3 text-sm">
                <p className="text-indigo-400 font-semibold">🤖 AI Suggestion</p>
                <p className="mt-1 text-gray-300 italic">
                    {aiSuggestion}
                </p>
            </div>
        </div>
    );
};

export default TimeInsights;