import { useEffect, useState } from "react";
import {
  buildWhatsAppLink,
  generateOutreachMessage,
  generateOutreachSubject,
  sendLeadEmail,
} from "../services/outreachService";

function PriorityBadge({ value }) {
  const className =
    value === "HIGH"
      ? "bg-red-50 text-accepthigh ring-1 ring-red-200"
      : value === "MEDIUM"
        ? "bg-amber-50 text-amber-700 ring-1 ring-amber-200"
        : "bg-emerald-50 text-acceptlow ring-1 ring-emerald-200";

  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${className}`}>{value}</span>;
}

function WebsiteQualityBadge({ value }) {
  const className =
    value === "NO_WEBSITE"
      ? "bg-red-50 text-accepthigh ring-1 ring-red-200"
      : value === "WEAK_WEBSITE"
        ? "bg-amber-50 text-amber-700 ring-1 ring-amber-200"
        : "bg-emerald-50 text-acceptlow ring-1 ring-emerald-200";

  const label =
    value === "NO_WEBSITE"
      ? "No Website"
      : value === "WEAK_WEBSITE"
        ? "Weak"
        : "Good";

  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${className}`}>{label}</span>;
}

function EmailConfidenceBadge({ value }) {
  const className =
    value === "HIGH"
      ? "bg-emerald-50 text-acceptlow ring-1 ring-emerald-200"
      : value === "MEDIUM"
        ? "bg-amber-50 text-amber-700 ring-1 ring-amber-200"
        : "bg-slate-100 text-slate-600 ring-1 ring-slate-200 dark:bg-slate-700 dark:text-slate-200 dark:ring-slate-600";

  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${className}`}>{value}</span>;
}

function formatEmailType(value) {
  if (!value || value === "missing") {
    return "-";
  }
  if (value === "generated") {
    return "Generated";
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function Toast({ toast }) {
  if (!toast) {
    return null;
  }

  const tone =
    toast.type === "error"
      ? "border-rose-200 bg-rose-50 text-rose-700"
      : "border-emerald-200 bg-emerald-50 text-emerald-700";

  return (
    <div className={`rounded-xl border px-4 py-3 text-sm font-medium shadow-sm transition-colors duration-200 ${tone}`}>
      {toast.message}
    </div>
  );
}

function MailIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 6h16v12H4z" />
      <path d="m4 8 8 6 8-6" />
    </svg>
  );
}

function WhatsAppIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 21a8.5 8.5 0 1 0-4.7-1.4L4 21l1.6-3.1A8.5 8.5 0 0 0 12 21Z" />
      <path d="M9.4 8.8c.2-.5.4-.5.6-.5h.5c.2 0 .4 0 .5.3l.6 1.4c.1.2.1.4 0 .6l-.5.8c-.1.1-.1.3 0 .4.4.8 1.1 1.5 1.9 1.9.1.1.3.1.4 0l.8-.5c.2-.1.4-.1.6 0l1.4.6c.3.1.3.3.3.5v.5c0 .2 0 .4-.5.6a4.6 4.6 0 0 1-4.7-1 9 9 0 0 1-2.7-4.1 4.6 4.6 0 0 1 .8-4.5Z" />
    </svg>
  );
}

function LeadsTable({ leads, loading, loadingStage }) {
  const [sentStatus, setSentStatus] = useState({});
  const [sendingRows, setSendingRows] = useState({});
  const [messageCache, setMessageCache] = useState({});
  const [toast, setToast] = useState(null);
  const [rowStatus, setRowStatus] = useState({});

  useEffect(() => {
    if (!toast) {
      return undefined;
    }

    const timer = setTimeout(() => setToast(null), 3200);
    return () => clearTimeout(timer);
  }, [toast]);

  const getLeadKey = (lead, index) => `${lead.name}-${lead.email || lead.phoneNumber || index}`;

  const handleSendEmail = async (lead, index) => {
    if (!lead.email) {
      return;
    }

    const leadKey = getLeadKey(lead, index);
    setRowStatus((prev) => ({ ...prev, [leadKey]: "Generating message..." }));
    const message = messageCache[leadKey] || generateOutreachMessage(lead);
    const subject = generateOutreachSubject(lead);

    setMessageCache((prev) => ({ ...prev, [leadKey]: message }));
    setSendingRows((prev) => ({ ...prev, [leadKey]: true }));
    setRowStatus((prev) => ({ ...prev, [leadKey]: "Sending email..." }));

    try {
      await sendLeadEmail({
        email: lead.email,
        subject,
        message,
      });
      setSentStatus((prev) => ({ ...prev, [leadKey]: "sent" }));
      setToast({ type: "success", message: `Email sent to ${lead.name}.` });
    } catch (error) {
      setToast({ type: "error", message: error.message || "Email delivery failed." });
    } finally {
      setSendingRows((prev) => ({ ...prev, [leadKey]: false }));
      setRowStatus((prev) => ({ ...prev, [leadKey]: "" }));
    }
  };

  const handleWhatsApp = (lead, index) => {
    if (!lead.phoneNumber) {
      return;
    }

    const leadKey = getLeadKey(lead, index);
    setRowStatus((prev) => ({ ...prev, [leadKey]: "Generating message..." }));
    const message = messageCache[leadKey] || generateOutreachMessage(lead);
    setMessageCache((prev) => ({ ...prev, [leadKey]: message }));

    const whatsappUrl = buildWhatsAppLink(lead.phoneNumber, message);
    if (!whatsappUrl) {
      setRowStatus((prev) => ({ ...prev, [leadKey]: "" }));
      setToast({ type: "error", message: "This phone number is not valid for WhatsApp." });
      return;
    }

    setRowStatus((prev) => ({ ...prev, [leadKey]: "" }));
    window.open(whatsappUrl, "_blank", "noopener,noreferrer");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 rounded-xl border border-slate-200 bg-gray-50 p-10 text-center text-sm text-slate-600 shadow-card transition-colors duration-200 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900" />
        {loadingStage || "Fetching leads..."}
      </div>
    );
  }

  if (!leads.length) {
    return (
      <div className="rounded-xl border border-slate-200 bg-gray-50 p-8 text-center text-sm text-slate-600 shadow-card transition-colors duration-200 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300">
        No leads found. Try a different location or business type.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <Toast toast={toast} />
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-gray-50 shadow-card transition-colors duration-200 dark:border-slate-800 dark:bg-slate-800">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 transition-colors duration-200 dark:bg-slate-900">
              <tr className="text-left text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <th className="px-4 py-3">Business</th>
                <th className="px-4 py-3">Address</th>
                <th className="px-4 py-3">Phone</th>
                <th className="px-4 py-3">Website</th>
                <th className="px-4 py-3">Website Quality</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead, index) => (
                <tr
                  key={`${lead.name}-${index}`}
                  className={`border-t border-slate-100 transition-colors duration-200 hover:bg-gray-100 dark:border-slate-700 dark:hover:bg-gray-800 ${
                    lead.isHotLead ? "bg-amber-50/40 dark:bg-amber-950/20" : ""
                  }`}
                >
                  <td className="px-4 py-3 font-semibold text-slate-900 dark:text-slate-100">
                    <div className="flex items-center gap-2">
                      <span>{lead.name}</span>
                      {lead.isHotLead ? (
                        <>
                          <span className="text-sm" aria-hidden="true">
                            🔥
                          </span>
                          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold tracking-wide text-amber-800 ring-1 ring-amber-300">
                            HOT
                          </span>
                        </>
                      ) : null}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{lead.address || "-"}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{lead.phoneNumber || "-"}</td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {lead.website ? (
                      <a
                        href={lead.website}
                        target="_blank"
                        rel="noreferrer"
                        className="font-semibold text-indigo-600 underline-offset-2 transition-colors duration-200 hover:text-indigo-700 hover:underline dark:text-indigo-400 dark:hover:text-indigo-300"
                      >
                        Visit
                      </a>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <WebsiteQualityBadge value={lead.websiteQuality} />
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {lead.email ? (
                      <div className="flex flex-col gap-1">
                        <a
                          href={`mailto:${lead.email}`}
                          className="font-semibold text-indigo-600 underline-offset-2 transition-colors duration-200 hover:text-indigo-700 hover:underline dark:text-indigo-400 dark:hover:text-indigo-300"
                        >
                          {lead.email}
                        </a>
                        {lead.emailType === "generated" ? (
                          <span className="text-[11px] text-slate-500 dark:text-slate-400">Fallback generated email</span>
                        ) : null}
                      </div>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{formatEmailType(lead.emailType)}</td>
                  <td className="px-4 py-3">
                    <EmailConfidenceBadge value={lead.emailConfidence || "LOW"} />
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge value={lead.priorityScore} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleSendEmail(lead, index)}
                        disabled={!lead.email || sendingRows[getLeadKey(lead, index)]}
                        className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-3 py-2 text-xs font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300 disabled:hover:translate-y-0 dark:disabled:bg-indigo-900"
                      >
                        <MailIcon />
                        {sendingRows[getLeadKey(lead, index)] ? "Sending..." : "Send Email"}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleWhatsApp(lead, index)}
                        disabled={!lead.phoneNumber}
                        className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-3 py-2 text-xs font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-emerald-200 disabled:hover:translate-y-0 dark:disabled:bg-emerald-900"
                      >
                        <WhatsAppIcon />
                        WhatsApp
                      </button>
                      {rowStatus[getLeadKey(lead, index)] ? (
                        <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
                          {rowStatus[getLeadKey(lead, index)]}
                        </span>
                      ) : null}
                      {sentStatus[getLeadKey(lead, index)] === "sent" ? (
                        <span className="rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-emerald-700 ring-1 ring-emerald-200">
                          Sent
                        </span>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default LeadsTable;
