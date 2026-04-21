import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
import tzlookup from "tz-lookup";

dayjs.extend(utc);
dayjs.extend(timezone);

function isWeekend(day) {
  return day === 0 || day === 6;
}

export function getTimeData({ country, lat, lng }) {
  let tz = null;

  // 🔥 1. BEST: detect using lat/lng
  if (lat && lng) {
    try {
      tz = tzlookup(lat, lng);
    } catch (err) {
      console.warn("tz lookup failed:", err);
    }
  }

  // 🔥 2. fallback using country
  if (!tz && country) {
    tz = "UTC"; // safe fallback
  }

  const nowIST = dayjs().tz("Asia/Kolkata");
  const countryTime = dayjs().tz(tz);

  const countryHour = countryTime.hour();
  const day = countryTime.day();

  const businessStart = 9;
  const businessEnd = 18;

  const isWeekendDay = isWeekend(day);

  const isBusinessTime =
    !isWeekendDay &&
    countryHour >= businessStart &&
    countryHour <= businessEnd;

  const startIST = dayjs().tz(tz).hour(businessStart).tz("Asia/Kolkata");
  const endIST = dayjs().tz(tz).hour(businessEnd).tz("Asia/Kolkata");

  let waitTime = "";

  if (!isBusinessTime) {
    let nextStart = countryTime;

    if (countryHour < businessStart) {
      nextStart = countryTime.hour(businessStart);
    } else {
      nextStart = countryTime.add(1, "day").hour(businessStart);
    }

    while (isWeekend(nextStart.day())) {
      nextStart = nextStart.add(1, "day").hour(businessStart);
    }

    const diff = nextStart.diff(countryTime, "minute");

    const hours = Math.floor(diff / 60);
    const minutes = diff % 60;

    waitTime = `${hours}h ${minutes}m`;
  }

  return {
    countryTime: countryTime.format("hh:mm A"),
    istTime: nowIST.format("hh:mm A"),
    bestStart: startIST.format("hh:mm A"),
    bestEnd: endIST.format("hh:mm A"),
    isBusinessTime,
    waitTime,
    isWeekendDay,
  };
}