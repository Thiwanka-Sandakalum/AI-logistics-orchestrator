export interface AgentInboxInterruptActionRequest {
  action: string;
  args: Record<string, any>;
}

export interface AgentInboxInterruptConfig {
  allow_respond: boolean;
  allow_accept: boolean;
  allow_edit: boolean;
  allow_ignore: boolean;
}

export interface AgentInboxInterrupt {
  action_request: AgentInboxInterruptActionRequest;
  config: AgentInboxInterruptConfig;
  description?: string;
  raw?: unknown;
}

function isRecord(value: unknown): value is Record<string, any> {
  return typeof value === "object" && value !== null;
}

function getInterruptObject(value: unknown): Record<string, any> | null {
  if (Array.isArray(value)) {
    return isRecord(value[0]) ? value[0] : null;
  }
  return isRecord(value) ? value : null;
}

function hasLegacyShape(value: Record<string, any>): boolean {
  return (
    isRecord(value.action_request) &&
    isRecord(value.config) &&
    "allow_respond" in value.config &&
    "allow_accept" in value.config &&
    "allow_edit" in value.config &&
    "allow_ignore" in value.config
  );
}

function getInterruptArrays(value: Record<string, any>) {
  const actionRequests = Array.isArray(value.action_requests)
    ? value.action_requests
    : Array.isArray(value.actionRequests)
      ? value.actionRequests
      : null;
  const reviewConfigs = Array.isArray(value.review_configs)
    ? value.review_configs
    : Array.isArray(value.reviewConfigs)
      ? value.reviewConfigs
      : null;

  return { actionRequests, reviewConfigs };
}

export function isAgentInboxInterruptSchema(
  value: unknown,
): value is AgentInboxInterrupt | AgentInboxInterrupt[] {
  const interruptObject = getInterruptObject(value);
  if (!interruptObject) {
    return false;
  }

  if (hasLegacyShape(interruptObject)) {
    return true;
  }

  const { actionRequests, reviewConfigs } = getInterruptArrays(interruptObject);
  return Array.isArray(actionRequests) && actionRequests.length > 0 && Array.isArray(reviewConfigs);
}

export function normalizeAgentInboxInterrupt(
  value: unknown,
): AgentInboxInterrupt | null {
  const interruptObject = getInterruptObject(value);
  if (!interruptObject) {
    return null;
  }

  if (hasLegacyShape(interruptObject)) {
    return interruptObject as AgentInboxInterrupt;
  }

  const { actionRequests, reviewConfigs } = getInterruptArrays(interruptObject);
  const firstActionRequest = Array.isArray(actionRequests) ? actionRequests[0] : null;
  const firstReviewConfig = Array.isArray(reviewConfigs) ? reviewConfigs[0] : null;

  if (!isRecord(firstActionRequest)) {
    return null;
  }

  const allowedDecisions = Array.isArray(firstReviewConfig?.allowed_decisions)
    ? firstReviewConfig.allowed_decisions
    : Array.isArray(firstReviewConfig?.allowedDecisions)
      ? firstReviewConfig.allowedDecisions
      : [];

  const action =
    firstActionRequest.action ??
    firstActionRequest.name ??
    firstReviewConfig?.action_name ??
    firstReviewConfig?.actionName ??
    "Unknown";

  const args = isRecord(firstActionRequest.args)
    ? firstActionRequest.args
    : Object.fromEntries(
      Object.entries(firstActionRequest).filter(
        ([key]) => !["action", "name", "type"].includes(key),
      ),
    );

  return {
    action_request: {
      action,
      args,
    },
    config: {
      allow_accept: allowedDecisions.includes("approve"),
      allow_edit: allowedDecisions.includes("edit"),
      allow_respond: allowedDecisions.includes("reject"),
      allow_ignore: false,
    },
    description:
      typeof interruptObject.description === "string"
        ? interruptObject.description
        : typeof firstActionRequest.description === "string"
          ? firstActionRequest.description
          : undefined,
    raw: value,
  };
}
