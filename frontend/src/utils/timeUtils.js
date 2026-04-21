import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";

dayjs.extend(utc);
dayjs.extend(timezone);

export const COUNTRY_TIMEZONES = {
  "United States": "America/New_York",
  "India": "Asia/Kolkata",
  "United Kingdom": "Europe/London",
  "Canada": "America/Toronto",
  "Australia": "Australia/Sydney",
  "Germany": "Europe/Berlin",
  "France": "Europe/Paris",
  "UAE": "Asia/Dubai",
  "Singapore": "Asia/Singapore"
};

export function getTimeData(country) {
  const tz = COUNTRY_TIMEZONES[country];

  if (!tz) return null;

  const nowIST = dayjs().tz("Asia/Kolkata");
  const countryTime = dayjs().tz(tz);

  const hourIST = nowIST.hour();

  // Business hours assumption: 9 AM – 6 PM (local)
  const businessStart = 9;
  const businessEnd = 18;

  const countryHour = countryTime.hour();

  const isBusinessTime = countryHour >= businessStart && countryHour <= businessEnd;

  // Convert business hours to IST
  const startIST = dayjs().tz(tz).hour(businessStart).tz("Asia/Kolkata");
  const endIST = dayjs().tz(tz).hour(businessEnd).tz("Asia/Kolkata");

  let status = "";
  let waitTime = "";

  if (isBusinessTime) {
    status = "🟢 Perfect time to contact NOW";
  } else {
    const nextStart = countryTime.hour() < businessStart
      ? countryTime.hour(businessStart)
      : countryTime.add(1, "day").hour(businessStart);

    const diff = nextStart.diff(countryTime, "minute");

    const hours = Math.floor(diff / 60);
    const minutes = diff % 60;

    waitTime = `${hours}h ${minutes}m`;
    status = `🔴 Not the right time. Wait ${waitTime}`;
  }

  return {
    countryTime: countryTime.format("hh:mm A"),
    istTime: nowIST.format("hh:mm A"),
    bestStart: startIST.format("hh:mm A"),
    bestEnd: endIST.format("hh:mm A"),
    isBusinessTime,
    status
  };
}