import { AIMessage, Message, ToolMessage } from "@langchain/langgraph-sdk";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BadgeDollarSign,
  ChevronDown,
  ChevronUp,
  CircleAlert,
  ClipboardCheck,
  Clock3,
  MapPinned,
  PackageCheck,
  PackageSearch,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useStreamContext } from "@/providers/Stream";
import { ensureToolCallsHaveResponses } from "@/lib/ensure-tool-responses";
import { v4 as uuidv4 } from "uuid";

function isComplexValue(value: any): boolean {
  return Array.isArray(value) || (typeof value === "object" && value !== null);
}

function isRecord(value: unknown): value is Record<string, any> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

const BUSINESS_RESULT_TOOLS = new Set([
  "get_shipping_quote",
  "track_shipment",
  "create_shipment",
  "lookup_customer",
  "file_complaint",
  "get_shipment_details",
]);

function formatLabel(label: string) {
  return label
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function formatCurrency(value: unknown) {
  const amount = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(amount)) return formatValue(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(amount);
}

function formatDateTime(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";

  const date = value instanceof Date ? value : new Date(String(value));
  if (Number.isNaN(date.getTime())) {
    return formatValue(value);
  }

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit"
  }).format(date);
}

function statusTone(status: unknown) {
  const normalized = String(status ?? "").toLowerCase();
  if (["delivered", "active", "received", "resolved"].includes(normalized)) {
    return "bg-emerald-50 text-emerald-800 border-emerald-200";
  }
  if (["in_transit", "pending", "investigating"].includes(normalized)) {
    return "bg-amber-50 text-amber-900 border-amber-200";
  }
  if (["exception", "error", "rejected"].includes(normalized)) {
    return "bg-rose-50 text-rose-800 border-rose-200";
  }
  return "bg-slate-100 text-slate-700 border-slate-200";
}

function Metric({
  label,
  value,
  emphasis,
}: {
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-border/80 bg-white/85 px-4 py-3">
      <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </p>
      <p className={cn("mt-1 text-sm font-medium text-foreground", emphasis && "text-base")}>{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: unknown }) {
  return (
    <span
      className={cn(
        "inline-flex w-fit items-center rounded-full border px-2.5 py-1 text-xs font-medium capitalize",
        statusTone(status),
      )}
    >
      {String(status ?? "unknown").replace(/_/g, " ")}
    </span>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {title}
      </p>
      {children}
    </div>
  );
}

function GenericKeyValueGrid({
  data,
  preferCurrencyKeys = [],
}: {
  data: Record<string, any>;
  preferCurrencyKeys?: string[];
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {Object.entries(data).map(([key, value]) => (
        <Metric
          key={key}
          label={formatLabel(key)}
          value={
            preferCurrencyKeys.includes(key) ? formatCurrency(value) : formatValue(value)
          }
        />
      ))}
    </div>
  );
}

function useQuickSelectionSubmitter() {
  const stream = useStreamContext();

  const submitSelection = (content: string) => {
    if (!content.trim() || stream.isLoading) {
      return;
    }

    const newHumanMessage: Message = {
      id: uuidv4(),
      type: "human",
      content,
    };

    const toolMessages = ensureToolCallsHaveResponses(stream.messages);
    stream.submit(
      { messages: [...toolMessages, newHumanMessage] },
      {
        streamMode: ["values"],
        optimisticValues: (prev) => ({
          ...prev,
          messages: [
            ...(prev.messages ?? []),
            ...toolMessages,
            newHumanMessage,
          ],
        }),
      },
    );
  };

  return {
    canSubmit: !stream.isLoading,
    submitSelection,
  };
}

function QuoteResultCard({ result }: { result: Record<string, any> }) {
  const rates = Array.isArray(result.rates) ? result.rates : [];
  const { canSubmit, submitSelection } = useQuickSelectionSubmitter();
  const [selectedOptionKey, setSelectedOptionKey] = useState<string | null>(null);

  return (
    <Card className="w-full max-w-4xl rounded-[24px] border-sky-100 bg-[linear-gradient(180deg,rgba(248,252,255,0.98),rgba(240,249,255,0.96))] shadow-sm">
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <BadgeDollarSign className="size-5 text-sky-700" />
              Shipping Quote Options
            </CardTitle>
            <CardDescription>
              {formatValue(result.origin_zip)} to {formatValue(result.destination_zip)} for {formatValue(result.weight_lbs)} lbs
            </CardDescription>
          </div>
          <span className="inline-flex rounded-full border border-sky-200 bg-white px-3 py-1 text-xs font-medium text-sky-800">
            {rates.length} option{rates.length === 1 ? "" : "s"}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {rates.length > 0 ? (
          <div className="grid gap-3">
            {rates.map((rate, index) => {
              const option = isRecord(rate) ? rate : {};
              const serviceType = formatValue(option.service_type).toLowerCase();
              const carrier = formatValue(option.carrier ?? "Loomis");
              const cost = formatCurrency(option.cost);
              const days = formatValue(option.estimated_delivery_days);
              const optionKey = `${serviceType}-${carrier}-${cost}-${index}`;

              const selectionMessage =
                `I choose the ${serviceType} option with ${carrier} for ${cost} ` +
                `(${days} day estimate). Proceed with this option and continue shipment booking.`;

              return (
                <div
                  key={optionKey}
                  className="grid gap-3 rounded-2xl border border-sky-100 bg-white/90 p-4 sm:grid-cols-[1.2fr_0.8fr_0.8fr]"
                >
                  <div>
                    <p className="text-sm font-semibold text-foreground">
                      {formatLabel(serviceType)}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {carrier}
                    </p>
                  </div>
                  <Metric label="Estimated Days" value={days} />
                  <div className="space-y-2">
                    <Metric label="Cost" value={cost} emphasis />
                    <Button
                      type="button"
                      variant={selectedOptionKey === optionKey ? "secondary" : "brand"}
                      size="sm"
                      className="w-full"
                      disabled={!canSubmit}
                      onClick={() => {
                        setSelectedOptionKey(optionKey);
                        submitSelection(selectionMessage);
                      }}
                    >
                      {selectedOptionKey === optionKey ? "Selected" : "Choose This Option"}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <GenericKeyValueGrid data={result} preferCurrencyKeys={["quoted_total_cost", "cost", "total_cost"]} />
        )}
      </CardContent>
    </Card>
  );
}

function TrackingResultCard({ result }: { result: Record<string, any> }) {
  return (
    <Card className="w-full max-w-4xl rounded-[24px] border-amber-100 bg-[linear-gradient(180deg,rgba(255,252,245,0.98),rgba(255,247,237,0.96))] shadow-sm">
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <PackageSearch className="size-5 text-amber-700" />
              Tracking Update
            </CardTitle>
            <CardDescription>{formatValue(result.tracking_number)}</CardDescription>
          </div>
          <StatusBadge status={result.status} />
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Carrier" value={formatValue(result.carrier ?? "Loomis")} />
        <Metric label="Current Location" value={formatValue(result.current_location)} />
        <Metric label="Estimated Delivery" value={formatDateTime(result.estimated_delivery)} />
        <Metric label="Last Update" value={formatDateTime(result.last_update)} />
      </CardContent>
    </Card>
  );
}

function ShipmentCreatedCard({ result }: { result: Record<string, any> }) {
  return (
    <Card className="w-full max-w-4xl rounded-[24px] border-emerald-100 bg-[linear-gradient(180deg,rgba(245,255,250,0.98),rgba(236,253,245,0.96))] shadow-sm">
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <PackageCheck className="size-5 text-emerald-700" />
              Shipment Created
            </CardTitle>
            <CardDescription>Booking confirmed and ready for customer follow-up.</CardDescription>
          </div>
          <StatusBadge status="confirmed" />
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Tracking Number" value={formatValue(result.tracking_number)} emphasis />
        <Metric label="Confirmation ID" value={formatValue(result.confirmation_id)} />
        <Metric label="Estimated Delivery" value={formatValue(result.estimated_delivery)} />
        <Metric label="Total Cost" value={formatCurrency(result.total_cost)} emphasis />
      </CardContent>
    </Card>
  );
}

function CustomerLookupCard({ result }: { result: Record<string, any> }) {
  const shipments = Array.isArray(result.recent_shipments) ? result.recent_shipments : [];

  return (
    <Card className="w-full max-w-4xl rounded-[24px] border-violet-100 bg-[linear-gradient(180deg,rgba(251,248,255,0.98),rgba(245,243,255,0.96))] shadow-sm">
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <UserRound className="size-5 text-violet-700" />
              Customer Snapshot
            </CardTitle>
            <CardDescription>{formatValue(result.name)} • {formatValue(result.customer_id)}</CardDescription>
          </div>
          <StatusBadge status={result.account_status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Email" value={formatValue(result.email)} />
          <Metric label="Phone" value={formatValue(result.phone)} />
          <Metric label="Total Shipments" value={formatValue(result.total_shipments)} emphasis />
          <Metric label="Recent Records" value={String(shipments.length)} />
        </div>
        {shipments.length > 0 && (
          <Section title="Recent Shipments">
            <div className="grid gap-3">
              {shipments.map((shipment, index) => {
                const record = isRecord(shipment) ? shipment : {};
                return (
                  <div
                    key={`${record.tracking_number ?? "shipment"}-${index}`}
                    className="grid gap-3 rounded-2xl border border-violet-100 bg-white/90 p-4 sm:grid-cols-[1fr_0.9fr_1fr_0.9fr]"
                  >
                    <Metric label="Tracking" value={formatValue(record.tracking_number)} />
                    <Metric label="Status" value={formatValue(record.status)} />
                    <Metric label="Destination" value={`${formatValue(record.destination_city)}, ${formatValue(record.destination_state)}`} />
                    <Metric label="ETA" value={formatValue(record.estimated_delivery)} />
                  </div>
                );
              })}
            </div>
          </Section>
        )}
      </CardContent>
    </Card>
  );
}

function ComplaintCard({ result }: { result: Record<string, any> }) {
  return (
    <Card className="w-full max-w-4xl rounded-[24px] border-rose-100 bg-[linear-gradient(180deg,rgba(255,248,248,0.98),rgba(255,241,242,0.96))] shadow-sm">
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ClipboardCheck className="size-5 text-rose-700" />
              Complaint Filed
            </CardTitle>
            <CardDescription>{formatValue(result.ticket_id)}</CardDescription>
          </div>
          <StatusBadge status={result.status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <Metric label="Next Steps" value={formatValue(result.next_steps)} />
          <Metric label="Estimated Resolution" value={formatValue(result.estimated_resolution)} />
        </div>
      </CardContent>
    </Card>
  );
}

function ShipmentDetailsCard({ result }: { result: Record<string, any> }) {
  const senderEntries = Object.fromEntries(
    Object.entries(result).filter(([key]) => key.startsWith("sender_")),
  );
  const recipientEntries = Object.fromEntries(
    Object.entries(result).filter(([key]) => key.startsWith("recipient_")),
  );
  const summaryEntries = Object.fromEntries(
    Object.entries(result).filter(
      ([key]) => !key.startsWith("sender_") && !key.startsWith("recipient_"),
    ),
  );

  return (
    <Card className="w-full max-w-4xl rounded-[24px] border-cyan-100 bg-[linear-gradient(180deg,rgba(247,254,255,0.98),rgba(236,254,255,0.96))] shadow-sm">
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ShieldCheck className="size-5 text-cyan-700" />
              Verified Shipment Details
            </CardTitle>
            <CardDescription>Access granted after confirmation and phone verification.</CardDescription>
          </div>
          {summaryEntries.status && <StatusBadge status={summaryEntries.status} />}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {Object.keys(summaryEntries).length > 0 && (
          <Section title="Shipment Summary">
            <GenericKeyValueGrid data={summaryEntries} preferCurrencyKeys={["total_cost"]} />
          </Section>
        )}
        {Object.keys(senderEntries).length > 0 && (
          <Section title="Sender">
            <GenericKeyValueGrid data={senderEntries} />
          </Section>
        )}
        {Object.keys(recipientEntries).length > 0 && (
          <Section title="Recipient">
            <GenericKeyValueGrid data={recipientEntries} />
          </Section>
        )}
      </CardContent>
    </Card>
  );
}

function ToolCallCard({ name, args }: { name: string; args: Record<string, any> }) {
  const titleByTool: Record<string, string> = {
    get_shipping_quote: "Quote Request",
    track_shipment: "Tracking Request",
    create_shipment: "Shipment Creation Request",
    get_shipment_details: "Verified Shipment Detail Request",
    lookup_customer: "Customer Lookup Request",
    file_complaint: "Complaint Intake Request",
  };

  const primaryFieldsByTool: Record<string, string[]> = {
    get_shipping_quote: ["origin_zip", "destination_zip", "weight_lbs", "service_type"],
    track_shipment: ["tracking_number"],
    create_shipment: ["selected_carrier", "quoted_service_type", "quoted_total_cost", "weight_lbs"],
    get_shipment_details: ["confirmation_id", "phone_number"],
    lookup_customer: ["phone_or_email"],
    file_complaint: ["tracking_number", "issue_type", "contact_email"],
  };

  const prominentFields = primaryFieldsByTool[name] ?? Object.keys(args).slice(0, 4);
  const visibleEntries = Object.fromEntries(
    prominentFields.filter((field) => field in args).map((field) => [field, args[field]]),
  );

  return (
    <Card className="w-full max-w-4xl rounded-[22px] border-border/80 bg-white/90 shadow-sm">
      <CardHeader className="gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">{titleByTool[name] ?? formatLabel(name)}</CardTitle>
            <CardDescription>{name}</CardDescription>
          </div>
          <span className="inline-flex items-center rounded-full border border-border bg-muted/60 px-3 py-1 text-xs font-medium text-muted-foreground">
            Pending tool call
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {Object.keys(visibleEntries).length > 0 ? (
          <GenericKeyValueGrid data={visibleEntries} preferCurrencyKeys={["quoted_total_cost"]} />
        ) : (
          <code className="text-sm block p-3 rounded-xl bg-muted/40">{"{}"}</code>
        )}
      </CardContent>
    </Card>
  );
}

function ToolMessageCard({
  message,
  hideTechnicalTraces,
}: {
  message: ToolMessage;
  hideTechnicalTraces: boolean;
}) {
  const result = parseToolResultContent(message.content);

  if (hideTechnicalTraces) {
    const isBusinessTool = message.name
      ? BUSINESS_RESULT_TOOLS.has(message.name)
      : false;
    // Keep only domain cards when technical traces are hidden.
    if (!isBusinessTool || result.error || !result.record) {
      return null;
    }
  }

  if (result.error) {
    return (
      <Card className="w-full max-w-4xl rounded-[22px] border-rose-200 bg-rose-50/80 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-rose-900">
            <CircleAlert className="size-5" />
            Tool Error
          </CardTitle>
          <CardDescription>{message.name ?? "Tool response"}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-rose-900">{formatValue(result.message ?? result.raw)}</p>
        </CardContent>
      </Card>
    );
  }

  if (!result.record) {
    return <GenericToolResult message={message} parsedContent={result.raw} isJsonContent={result.isJsonContent} />;
  }

  switch (message.name) {
    case "get_shipping_quote":
      return <QuoteResultCard result={result.record} />;
    case "track_shipment":
      return <TrackingResultCard result={result.record} />;
    case "create_shipment":
      return <ShipmentCreatedCard result={result.record} />;
    case "lookup_customer":
      return <CustomerLookupCard result={result.record} />;
    case "file_complaint":
      return <ComplaintCard result={result.record} />;
    case "get_shipment_details":
      return <ShipmentDetailsCard result={result.record} />;
    default:
      return <GenericToolResult message={message} parsedContent={result.record} isJsonContent={result.isJsonContent} />;
  }
}

function parseToolResultContent(content: ToolMessage["content"]) {
  let parsedContent: any = content;
  let isJsonContent = false;

  try {
    if (typeof content === "string") {
      parsedContent = JSON.parse(content);
      isJsonContent = true;
    }
  } catch {
    parsedContent = content;
  }

  return {
    raw: parsedContent,
    isJsonContent,
    record: isRecord(parsedContent) ? parsedContent : null,
    error: isRecord(parsedContent) && parsedContent.error === true,
    message: isRecord(parsedContent) ? parsedContent.message : null,
  };
}

function GenericToolResult({
  message,
  parsedContent,
  isJsonContent,
}: {
  message: ToolMessage;
  parsedContent: any;
  isJsonContent: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  const contentStr = isJsonContent
    ? JSON.stringify(parsedContent, null, 2)
    : String(message.content);
  const contentLines = contentStr.split("\n");
  const shouldTruncate = contentLines.length > 4 || contentStr.length > 500;
  const displayedContent =
    shouldTruncate && !isExpanded
      ? contentStr.length > 500
        ? contentStr.slice(0, 500) + "..."
        : contentLines.slice(0, 4).join("\n") + "\n..."
      : contentStr;

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          {message.name ? (
            <h3 className="font-medium text-gray-900">
              Tool Result:{" "}
              <code className="bg-gray-100 px-2 py-1 rounded">
                {message.name}
              </code>
            </h3>
          ) : (
            <h3 className="font-medium text-gray-900">Tool Result</h3>
          )}
          {message.tool_call_id && (
            <code className="ml-2 text-sm bg-gray-100 px-2 py-1 rounded">
              {message.tool_call_id}
            </code>
          )}
        </div>
      </div>
      <motion.div
        className="min-w-full bg-gray-100"
        initial={false}
        animate={{ height: "auto" }}
        transition={{ duration: 0.3 }}
      >
        <div className="p-3">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={isExpanded ? "expanded" : "collapsed"}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
            >
              {isJsonContent && isRecord(parsedContent) ? (
                <table className="min-w-full divide-y divide-gray-200">
                  <tbody className="divide-y divide-gray-200">
                    {Object.entries(parsedContent).map(([key, value], argIdx) => (
                      <tr key={argIdx}>
                        <td className="px-4 py-2 text-sm font-medium text-gray-900 whitespace-nowrap">
                          {key}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-500">
                          {isComplexValue(value) ? (
                            <code className="bg-gray-50 rounded px-2 py-1 font-mono text-sm break-all">
                              {JSON.stringify(value, null, 2)}
                            </code>
                          ) : (
                            String(value)
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <code className="text-sm block">{displayedContent}</code>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
        {shouldTruncate && (
          <motion.button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full py-2 flex items-center justify-center border-t-[1px] border-gray-200 text-gray-500 hover:text-gray-600 hover:bg-gray-50 transition-all ease-in-out duration-200 cursor-pointer"
            initial={{ scale: 1 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isExpanded ? <ChevronUp /> : <ChevronDown />}
          </motion.button>
        )}
      </motion.div>
    </div>
  );
}

export function ToolCalls({
  toolCalls,
}: {
  toolCalls: AIMessage["tool_calls"];
}) {
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div className="space-y-4 w-full max-w-4xl">
      {toolCalls.map((tc, idx) => {
        const args = tc.args as Record<string, any>;
        const hasArgs = Object.keys(args).length > 0;
        const isKnownTool = [
          "get_shipping_quote",
          "track_shipment",
          "create_shipment",
          "get_shipment_details",
          "lookup_customer",
          "file_complaint",
        ].includes(tc.name);

        if (isKnownTool) {
          return <ToolCallCard key={tc.id ?? idx} name={tc.name} args={args} />;
        }

        return (
          <div
            key={idx}
            className="border border-gray-200 rounded-lg overflow-hidden"
          >
            <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
              <h3 className="font-medium text-gray-900">
                {tc.name}
                {tc.id && (
                  <code className="ml-2 text-sm bg-gray-100 px-2 py-1 rounded">
                    {tc.id}
                  </code>
                )}
              </h3>
            </div>
            {hasArgs ? (
              <table className="min-w-full divide-y divide-gray-200">
                <tbody className="divide-y divide-gray-200">
                  {Object.entries(args).map(([key, value], argIdx) => (
                    <tr key={argIdx}>
                      <td className="px-4 py-2 text-sm font-medium text-gray-900 whitespace-nowrap">
                        {key}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-500">
                        {isComplexValue(value) ? (
                          <code className="bg-gray-50 rounded px-2 py-1 font-mono text-sm break-all">
                            {JSON.stringify(value, null, 2)}
                          </code>
                        ) : (
                          String(value)
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <code className="text-sm block p-3">{"{}"}</code>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function ToolResult({
  message,
  hideTechnicalTraces = false,
}: {
  message: ToolMessage;
  hideTechnicalTraces?: boolean;
}) {
  return <ToolMessageCard message={message} hideTechnicalTraces={hideTechnicalTraces} />;
}
