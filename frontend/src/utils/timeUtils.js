import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
import ct from "countries-and-timezones";

dayjs.extend(utc);
dayjs.extend(timezone);

// 🔥 AUTO DETECT TIMEZONE FROM COUNTRY
function getTimezoneFromCountry(countryName) {
  const countries = ct.getAllCountries();

  const country = Object.values(countries).find(
    (c) => c.name.toLowerCase() === countryName.toLowerCase()
  );

  if (!country) return null;

  // take first timezone
  return country.timezones[0];
}

function isWeekend(day) {
  return day === 0 || day === 6;
}

export function getTimeData(country) {
  let tz = getTimezoneFromCountry(country);

  // fallback
  if (!tz) {
    console.warn("Timezone not found for:", country);
    tz = "UTC";
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