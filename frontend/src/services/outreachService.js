import { sendOutreachEmail } from "./leadService";

function buildLeadContext(lead) {
  const location = [lead.address, lead.city].filter(Boolean).join(", ");
  return location || "your market";
}

export function generateOutreachMessage(lead) {
  return [
    `Hi ${lead.name} team,`,
    "",
    `I came across your business in ${buildLeadContext(lead)} and noticed there may be an opportunity to strengthen your online presence.`,
    "We help businesses improve websites, lead capture flows, and digital customer acquisition with modern web and app experiences.",
    "",
    "If helpful, I can share 2-3 quick ideas tailored to your business with no obligation.",
    "",
    "Best regards,",
    "LeadGen Pro Outreach",
  ].join("\n");
}

export function generateOutreachSubject(lead) {
  return `Quick growth idea for ${lead.name}`;
}

export function buildWhatsAppLink(phoneNumber, message) {
  const digits = (phoneNumber || "").replace(/[^\d]/g, "");
  if (!digits) {
    return "";
  }
  return `https://wa.me/${digits}?text=${encodeURIComponent(message)}`;
}

export async function sendLeadEmail({ email, subject, message }) {
  return sendOutreachEmail({ email, subject, message });
}
