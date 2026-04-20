import { useEffect, useId, useState } from "react";
import {
  buildWhatsAppLink,
  generateOutreachMessage,
  generateOutreachSubject,
  sendLeadEmail,
} from "../services/outreachService";
import { analyzeLead, chatWithLeadAssistant } from "../services/leadService";

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

function SentimentBadge({ value }) {
  const className =
    value === "positive"
      ? "bg-emerald-50 text-acceptlow ring-1 ring-emerald-200"
      : value === "negative"
        ? "bg-red-50 text-accepthigh ring-1 ring-red-200"
        : "bg-slate-100 text-slate-700 ring-1 ring-slate-200 dark:bg-slate-700 dark:text-slate-200 dark:ring-slate-600";

  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${className}`}>{value}</span>;
}

function RecommendationBadge({ value }) {
  const className =
    value === "contact"
      ? "bg-emerald-50 text-acceptlow ring-1 ring-emerald-200"
      : value === "skip"
        ? "bg-red-50 text-accepthigh ring-1 ring-red-200"
        : "bg-amber-50 text-amber-700 ring-1 ring-amber-200";

  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${className}`}>{value}</span>;
}

function HeaderCell({ title, helper, className = "" }) {
  return (
    <th className={`px-4 py-3 align-top ${className}`}>
      <div className="space-y-0.5">
        <div>{title}</div>
        <div className="text-[10px] font-medium normal-case tracking-normal text-slate-400 dark:text-slate-500">{helper}</div>
      </div>
    </th>
  );
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

function SocialLink({ href, label }) {
  if (!href) return <span className="text-slate-400">-</span>;
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="font-semibold text-indigo-600 underline-offset-2 transition-colors duration-200 hover:text-indigo-700 hover:underline dark:text-indigo-400 dark:hover:text-indigo-300"
    >
      {label}
    </a>
  );
}

function LeadAssistantModal({
  lead,
  open,
  onClose,
  analysis,
  analysisLoading,
  chatMessages,
  chatInput,
  setChatInput,
  onSendChat,
  chatLoading,
}) {
  const chatInputId = `${useId()}-lead-assistant-chat`;
  if (!open || !lead) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="max-h-[92vh] w-full max-w-4xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Lead AI Assistant</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">{lead.name}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Close
          </button>
        </div>

        <div className="grid max-h-[78vh] gap-4 overflow-y-auto p-5 lg:grid-cols-2">
          <section className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/60">
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">AI Analysis</h4>
            {analysisLoading ? (
              <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-800" />
                Analyzing...
              </div>
            ) : analysis ? (
              <div className="space-y-3 text-xs text-slate-700 dark:text-slate-300">
                <div>
                  <p className="font-semibold text-slate-900 dark:text-slate-100">Overview</p>
                  <p>{analysis.overview}</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-900 dark:text-slate-100">Strengths</p>
                  <ul className="space-y-1">
                    {(analysis.strengths || []).map((item, idx) => (
                      <li key={idx}>+ {item}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="font-semibold text-slate-900 dark:text-slate-100">Weaknesses</p>
                  <ul className="space-y-1">
                    {(analysis.weaknesses || []).map((item, idx) => (
                      <li key={idx}>- {item}</li>
                    ))}
                  </ul>
                </div>
                <p>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">Customer perception:</span>{" "}
                  {analysis.customerPerception}
                </p>
                <p>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">What to sell:</span>{" "}
                  {analysis.whatToSell}
                </p>
                <p>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">Outreach angle:</span>{" "}
                  {analysis.outreachAngle}
                </p>
              </div>
            ) : (
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Click Analyze to generate live AI insights for this lead.
              </p>
            )}
          </section>

          <section className="flex min-h-[380px] flex-col rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/60">
            <label htmlFor={chatInputId} className="mb-2 block text-sm font-semibold text-slate-900 dark:text-slate-100">
              Chat
            </label>
            <div className="mb-3 flex-1 space-y-2 overflow-y-auto rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
              {chatMessages.length ? (
                chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`rounded-lg px-3 py-2 text-xs ${
                      msg.role === "user"
                        ? "ml-8 bg-indigo-50 text-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-200"
                        : "mr-8 bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200"
                    }`}
                  >
                    {msg.content}
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400">Ask about objections, pricing angle, offer positioning, or next best step.</p>
              )}
              {chatLoading ? (
                <p className="text-xs italic text-slate-500 dark:text-slate-400">AI is thinking...</p>
              ) : null}
            </div>
            <div className="flex gap-2">
              <input
                id={chatInputId}
                name="leadAssistantChat"
                type="text"
                autoComplete="off"
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") onSendChat();
                }}
                placeholder="Ask AI: what should I pitch first?"
                className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none ring-indigo-400 focus:ring-2 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
              />
              <button
                type="button"
                onClick={onSendChat}
                disabled={!chatInput.trim() || chatLoading}
                className="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:bg-indigo-300"
              >
                {chatLoading ? "Sending..." : "Send"}
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function LeadsTable({ leads, loading, loadingStage }) {
  const [sentStatus, setSentStatus] = useState({});
  const [sendingRows, setSendingRows] = useState({});
  const [messageCache, setMessageCache] = useState({});
  const [toast, setToast] = useState(null);
  const [rowStatus, setRowStatus] = useState({});
  const [activeLead, setActiveLead] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisCache, setAnalysisCache] = useState({});
  const [chatByLead, setChatByLead] = useState({});
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

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

  const handleOpenAssistant = async (lead, index) => {
    const leadKey = getLeadKey(lead, index);
    setActiveLead({ ...lead, leadKey });
    setChatInput("");

    if (analysisCache[leadKey]) {
      return;
    }

    setAnalysisLoading(true);
    try {
      console.log("Lead analyze request payload", {
        name: lead.name,
        type: lead.businessType || "business",
        websiteContent: lead.websiteContent || "",
        rating: lead.rating || null,
        reviews: lead.googleReviews || [],
      });
      const result = await analyzeLead({
        name: lead.name,
        businessType: lead.businessType || "business",
        websiteContent: lead.websiteContent || "",
        website: lead.website || null,
        rating: lead.rating ?? null,
        reviews: lead.googleReviews || [],
      });
      console.log("Lead analyze response payload", result);
      setAnalysisCache((prev) => ({ ...prev, [leadKey]: result }));
    } catch (error) {
      setToast({ type: "error", message: error.message || "Analysis failed." });
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleSendChat = async () => {
    if (!activeLead || !chatInput.trim()) return;

    const leadKey = activeLead.leadKey;
    const currentMessages = chatByLead[leadKey] || [];
    const nextUserMessage = { role: "user", content: chatInput.trim() };
    const nextMessages = [...currentMessages, nextUserMessage];
    setChatByLead((prev) => ({ ...prev, [leadKey]: nextMessages }));
    setChatInput("");
    setChatLoading(true);
    try {
      const analysis = analysisCache[leadKey];
      const chatPayload = {
        messages: nextMessages,
        lead: {
          name: activeLead.name,
          businessType: activeLead.businessType || "business",
          websiteContent: activeLead.websiteContent || "",
          rating: activeLead.rating ?? null,
          reviews: activeLead.googleReviews || [],
          overview: analysis?.overview || "",
          whatToSell: analysis?.whatToSell || "",
          outreachAngle: analysis?.outreachAngle || "",
          email: activeLead.email || null,
          phoneNumber: activeLead.phoneNumber || null,
          website: activeLead.website || null,
        },
      };
      console.log("Lead chat request payload", chatPayload);
      const response = await chatWithLeadAssistant({
        ...chatPayload,
      });
      console.log("Lead chat response payload", response);
      setChatByLead((prev) => ({
        ...prev,
        [leadKey]: [...(prev[leadKey] || nextMessages), { role: "assistant", content: response.response }],
      }));
    } catch (error) {
      setToast({ type: "error", message: error.message || "Chat failed." });
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 rounded-2xl border border-slate-200/90 bg-white/80 p-12 text-center text-sm font-medium text-slate-600 shadow-glow backdrop-blur-sm dark:border-slate-700/90 dark:bg-slate-900/70 dark:text-slate-300">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600 dark:border-indigo-900 dark:border-t-indigo-400" />
        {loadingStage || "Fetching leads..."}
      </div>
    );
  }

  if (!leads.length) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300/90 bg-slate-50/80 p-10 text-center dark:border-slate-600 dark:bg-slate-900/50">
        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">No leads in this view yet.</p>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">Run a search above, or widen your filters.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <Toast toast={toast} />
      <div className="overflow-hidden rounded-2xl border border-slate-200/90 bg-white/90 shadow-glow-lg backdrop-blur-sm transition-colors duration-200 dark:border-slate-700/90 dark:bg-slate-900/80">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gradient-to-b from-slate-100 to-slate-50/90 dark:from-slate-900 dark:to-slate-950/90">
              <tr className="border-b border-slate-200/90 text-left text-[10px] font-bold uppercase tracking-[0.12em] text-slate-600 dark:border-slate-700 dark:text-slate-400">
                <th className="px-4 py-2" colSpan={7}>
                  Basic Info
                </th>
                <th className="px-4 py-2" colSpan={3}>
                  Business Insights
                </th>
                <th className="px-4 py-2" colSpan={3}>
                  Sales
                </th>
                <th className="px-4 py-2" colSpan={1}>
                  Outreach
                </th>
              </tr>
              <tr className="text-left text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                <HeaderCell title="Name" helper="Business name from search source" />
                <HeaderCell title="Phone" helper="Primary contact number if available" />
                <HeaderCell title="Email" helper="Best email found across website pages" />
                <HeaderCell title="Website" helper="Detected business website URL" />
                <HeaderCell title="Instagram" helper="Discovered Instagram business profile" />
                <HeaderCell title="YouTube" helper="Discovered YouTube business channel" />
                <HeaderCell title="Confidence" helper="Data accuracy score based on available info" />

                <HeaderCell title="Analysis" helper="Click to open AI sales assistant" />
                <HeaderCell title="Sentiment" helper="Customer tone inferred from review signals" />
                <HeaderCell title="Reviews" helper="Google rating and review count snapshot" />

                <HeaderCell title="Priority" helper="How likely this lead needs a website/app" />
                <HeaderCell title="Recommendation" helper="AI contact decision for outreach focus" />
                <HeaderCell title="Pitch" helper="Most relevant offer: website/app/automation" />

                <HeaderCell title="Actions" helper="Direct outreach shortcuts" />
              </tr>
            </thead>
            <tbody>
              {leads.map((lead, index) => (
                <tr
                  key={`${lead.name}-${index}`}
                  className={`border-t border-slate-100/90 transition-colors duration-200 hover:bg-indigo-50/40 dark:border-slate-800 dark:hover:bg-slate-800/80 ${
                    lead.isHotLead ? "bg-amber-50/50 dark:bg-amber-950/25" : ""
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
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{lead.phoneNumber || "-"}</td>
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
                        <span className="text-[10px] uppercase tracking-wide text-slate-400 dark:text-slate-500">
                          source: {lead.emailSource || "missing"}
                        </span>
                      </div>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    {lead.website ? (
                      <div className="flex flex-col gap-1">
                        <a
                          href={lead.website}
                          target="_blank"
                          rel="noreferrer"
                          className="font-semibold text-indigo-600 underline-offset-2 transition-colors duration-200 hover:text-indigo-700 hover:underline dark:text-indigo-400 dark:hover:text-indigo-300"
                        >
                          Visit
                        </a>
                        <WebsiteQualityBadge value={lead.websiteQuality} />
                      </div>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    <SocialLink href={lead.instagramUrl} label="View" />
                  </td>
                  <td className="px-4 py-3 text-slate-700 dark:text-slate-300">
                    <SocialLink href={lead.youtubeUrl} label="View" />
                  </td>
                  <td className="px-4 py-3">
                    <div className="space-y-1">
                      <EmailConfidenceBadge value={lead.emailConfidence || "LOW"} />
                      <div className="text-[10px] text-slate-400 dark:text-slate-500">{formatEmailType(lead.emailType)}</div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={() => handleOpenAssistant(lead, index)}
                      className="rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 transition-colors hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200 dark:hover:bg-indigo-900/50"
                    >
                      Click to Analyze
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <SentimentBadge value={lead.customerSentiment || "neutral"} />
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                    {lead.rating ? `${lead.rating.toFixed(1)} / 5` : "-"}
                    <div className="text-[11px] text-slate-500 dark:text-slate-400">{lead.reviewCount || 0} reviews</div>
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge value={lead.priorityScore} />
                  </td>
                  <td className="px-4 py-3">
                    <RecommendationBadge value={lead.recommendedAction || "manual review"} />
                  </td>
                  <td className="max-w-xs px-4 py-3 text-xs text-slate-700 dark:text-slate-300">
                    {lead.pitchSuggestion || "Not available"}
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
      <LeadAssistantModal
        lead={activeLead}
        open={Boolean(activeLead)}
        onClose={() => setActiveLead(null)}
        analysis={activeLead ? analysisCache[activeLead.leadKey] : null}
        analysisLoading={analysisLoading}
        chatMessages={activeLead ? chatByLead[activeLead.leadKey] || [] : []}
        chatInput={chatInput}
        setChatInput={setChatInput}
        onSendChat={handleSendChat}
        chatLoading={chatLoading}
      />
    </div>
  );
}

export default LeadsTable;
