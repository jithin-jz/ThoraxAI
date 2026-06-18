/**
 * Multi-tenant subdomain helpers.
 *
 * In dev:  abc.localhost:5173  → subdomain = "abc"
 * In prod: abc.domain.com     → subdomain = "abc"
 */

const BASE_DOMAIN = (import.meta.env.VITE_BASE_DOMAIN || "localhost")
  .toLowerCase()
  .trim();

const RESERVED = new Set([
  "www", "api", "app", "admin", "dashboard", "mail", "smtp", "ftp",
  "blog", "docs", "help", "support", "status", "assets", "static",
  "cdn", "auth", "login", "signup", "register", "public", "health",
]);

const SUBDOMAIN_RE = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/;

export function getBaseDomain() {
  return BASE_DOMAIN;
}

/**
 * Parse the current window's pathname and return the tenant subdomain,
 * or null if on the apex / reserved.
 */
export function getCurrentSubdomain() {
  if (typeof window === "undefined") return null;
  return parseSubdomainFromPath(window.location.pathname);
}

export function parseSubdomainFromPath(pathname) {
  if (!pathname) return null;
  const match = pathname.match(/^\/t\/([^/]+)/);
  if (match) {
    const candidate = match[1].toLowerCase();
    if (RESERVED.has(candidate)) return null;
    if (!SUBDOMAIN_RE.test(candidate)) return null;
    return candidate;
  }
  return null;
}

export function parseSubdomain(hostname) {
  // Legacy hostname parser - fallback or unused
  if (!hostname) return null;
  const host = hostname.toLowerCase();
  if (host === BASE_DOMAIN) return null;
  const suffix = `.${BASE_DOMAIN}`;
  if (!host.endsWith(suffix)) return null;
  const candidate = host.slice(0, -suffix.length);
  if (!candidate || candidate.includes(".")) return null;
  if (RESERVED.has(candidate)) return null;
  if (!SUBDOMAIN_RE.test(candidate)) return null;
  return candidate;
}

/**
 * Build a fully-qualified tenant URL using path-based routing.
 */
export function buildTenantUrl(subdomain, path = "/") {
  if (!subdomain || !SUBDOMAIN_RE.test(subdomain)) return "";
  if (typeof window === "undefined") return "";
  const { protocol, port } = window.location;
  const host = port
    ? `${BASE_DOMAIN}:${port}`
    : BASE_DOMAIN;
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${protocol}//${host}/t/${subdomain}${cleanPath}`;
}

/**
 * Validate that a URL is under our BASE_DOMAIN (prevents open redirect).
 */
export function isTrustedTenantUrl(url) {
  if (!url) return false;
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.toLowerCase();
    return host === BASE_DOMAIN || host.endsWith(`.${BASE_DOMAIN}`);
  } catch {
    return false;
  }
}

/** Are we on a tenant subdomain right now? */
export function isOnTenantSubdomain() {
  return getCurrentSubdomain() !== null;
}
